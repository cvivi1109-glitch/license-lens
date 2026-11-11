"""license-lens 核心逻辑。

分层（也是本项目的"架构接口复用"演示点）：

    licenses.py   纯数据：许可知识库
    core.py      纯逻辑：归一化 / 义务 / 兼容性规则引擎 / 依赖清单扫描
    cli.py       纯界面：参数解析与输出渲染

扩展点：
    * 新增一种许可证  -> 只改 licenses.py
    * 新增一条兼容性规则 -> 写一个实现 CompatibilityRule 协议的类，注册进 RULES
    * 新增一种输出格式   -> 只改 cli.py / 渲染函数
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import Protocol

from .licenses import LICENSE_DB, OPTIONAL_LICENSES, LicenseInfo

#: 全部已知许可（课堂必记 5 种 + 可选扩展）
ALL_LICENSES: dict[str, LicenseInfo] = {**LICENSE_DB, **OPTIONAL_LICENSES}

#: 课堂必记的 5 种
CORE_IDS: tuple[str, ...] = tuple(LICENSE_DB)

LINKAGE_DYNAMIC = "dynamic"
LINKAGE_STATIC = "static"
LINKAGE_CHOICES = (LINKAGE_DYNAMIC, LINKAGE_STATIC)

LEVEL_OK = "允许"
LEVEL_CONDITIONAL = "有条件"
LEVEL_FORBIDDEN = "禁止"
LEVEL_UNKNOWN = "未知"

_EXIT_CODES = {LEVEL_OK: 0, LEVEL_CONDITIONAL: 1, LEVEL_FORBIDDEN: 2, LEVEL_UNKNOWN: 3}


class UnknownLicenseError(ValueError):
    """写法无法归一到知识库中的任何许可。"""

    def __init__(self, raw: str) -> None:
        super().__init__(f"无法识别的许可证：{raw!r}")
        self.raw = raw


# --------------------------------------------------------------------------- #
# 归一化
# --------------------------------------------------------------------------- #
def _key(raw: str) -> str:
    """把任意写法压成只含小写字母/数字/点的比较键。"""
    return "".join(ch for ch in raw.lower() if ch.isalnum() or ch == ".")


def _build_index() -> dict[str, str]:
    index: dict[str, str] = {}
    for lid, info in ALL_LICENSES.items():
        for candidate in (lid, info.name, *info.aliases):
            index.setdefault(_key(candidate), lid)
    return index


_INDEX: dict[str, str] = _build_index()


def normalize(raw: str | None) -> str | None:
    """把 'Apache 2.0' / 'gplv3' / 'MIT License' 这类写法归一成规范 id。"""
    if not raw:
        return None
    return _INDEX.get(_key(raw))


def lookup(raw: str) -> LicenseInfo:
    """归一化并返回许可详情，识别不了就抛 UnknownLicenseError。"""
    lid = normalize(raw)
    if lid is None:
        raise UnknownLicenseError(raw)
    return ALL_LICENSES[lid]


def obligations(raw: str) -> tuple[str, ...]:
    """返回某个许可的义务清单。"""
    return lookup(raw).obligations


# --------------------------------------------------------------------------- #
# 兼容性规则引擎
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CompatContext:
    """一次兼容性判定的输入。"""

    inbound: LicenseInfo
    outbound: LicenseInfo
    linkage: str = LINKAGE_DYNAMIC


@dataclass(frozen=True)
class Verdict:
    """一次兼容性判定的输出。"""

    level: str
    inbound: str
    outbound: str
    reason: str
    notes: tuple[str, ...] = ()
    rule: str = ""
    basis: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return self.level == LEVEL_OK

    @property
    def exit_code(self) -> int:
        return _EXIT_CODES.get(self.level, 3)

    @property
    def symbol(self) -> str:
        return {
            LEVEL_OK: "✅",
            LEVEL_CONDITIONAL: "⚠️",
            LEVEL_FORBIDDEN: "❌",
            LEVEL_UNKNOWN: "❓",
        }.get(self.level, "❓")


class CompatibilityRule(Protocol):
    """兼容性规则接口：匹配成功返回 Verdict，不适用返回 None。"""

    name: str

    def match(self, ctx: CompatContext) -> Verdict | None:  # pragma: no cover - 协议声明
        ...


def _verdict(ctx: CompatContext, level: str, reason: str, notes: tuple[str, ...] = (), rule: str = "") -> Verdict:
    return Verdict(
        level=level,
        inbound=ctx.inbound.id,
        outbound=ctx.outbound.id,
        reason=reason,
        notes=notes,
        rule=rule,
    )


class NonCommercialInboundRule:
    """上游是非商业许可：只能用于非商业用途。"""

    name = "noncommercial-inbound"

    def match(self, ctx: CompatContext) -> Verdict | None:
        if not ctx.inbound.is_noncommercial:
            return None
        return _verdict(
            ctx,
            LEVEL_CONDITIONAL,
            f"{ctx.inbound.id} 是**非商业**许可：只允许非商业用途，不能用于以 {ctx.outbound.id} 发布的商业项目。",
            notes=(
                "如果项目不涉及商业用途，仍可使用，但需遵守署名等义务。",
                "如果涉及收费、公司营利业务或付费服务，必须更换依赖或购买商业授权。",
                "非商业许可通常不是 OSI 认可的开源许可证，课程项目不建议选用。",
            ),
            rule=self.name,
        )


class SameLicenseRule:
    """上下游同一种许可：永远允许。"""

    name = "same-license"

    def match(self, ctx: CompatContext) -> Verdict | None:
        if ctx.inbound.id != ctx.outbound.id:
            return None
        return _verdict(ctx, LEVEL_OK, f"上下游同为 {ctx.inbound.id}，不存在冲突。", rule=self.name)


class PermissiveInboundRule:
    """上游是宽松许可：可放进任何许可的项目，但宽松许可的义务继续传递。"""

    name = "permissive-inbound"

    def match(self, ctx: CompatContext) -> Verdict | None:
        if not ctx.inbound.is_permissive:
            return None
        notes = [f"仍需履行 {ctx.inbound.id} 的义务：{ '；'.join(ctx.inbound.obligations) }"]
        if ctx.inbound.id == "Apache-2.0" and ctx.outbound.is_strong_copyleft:
            notes.append("注意：Apache-2.0 的代码不能用于 GPL-2.0-only（专利条款冲突），用于 GPL-3.0 是兼容的。")
        return _verdict(
            ctx,
            LEVEL_OK,
            f"{ctx.inbound.id} 属于宽松许可，允许被用于以 {ctx.outbound.id} 发布的项目。",
            notes=tuple(notes),
            rule=self.name,
        )


class WeakCopyleftInboundRule:
    """上游是弱传染许可（LGPL / MPL）：看链接方式。"""

    name = "weak-copyleft-inbound"

    def match(self, ctx: CompatContext) -> Verdict | None:
        if not ctx.inbound.is_weak_copyleft:
            return None
        if ctx.linkage == LINKAGE_DYNAMIC:
            return _verdict(
                ctx,
                LEVEL_OK,
                f"{ctx.inbound.id} 是弱传染许可，动态链接（import / 独立进程调用）不构成衍生作品，"
                f"因此可以用于以 {ctx.outbound.id} 发布的闭源项目。",
                notes=(
                    "仍需履行义务：" + "；".join(ctx.inbound.obligations),
                    "必须在文档中说明如何替换该库（使用者有权自行升级/替换）。",
                ),
                rule=self.name,
            )
        if ctx.outbound.is_weak_copyleft or ctx.outbound.is_strong_copyleft:
            return _verdict(
                ctx,
                LEVEL_OK,
                f"静态链接 {ctx.inbound.id}，但你的项目同样采用传染性许可 {ctx.outbound.id}，可以满足义务。",
                notes=("需遵守两者中较严格的义务。",),
                rule=self.name,
            )
        return _verdict(
            ctx,
            LEVEL_FORBIDDEN,
            f"静态链接 {ctx.inbound.id} 会使你的程序成为衍生作品，而以 {ctx.outbound.id} 发布无法满足"
            f"「衍生作品同样开源」的要求。",
            notes=(
                f"改法一：改用动态链接（本工具判定为「{LEVEL_OK}」）。",
                f"改法二：把项目许可改为 {ctx.inbound.id} 或 GPL-3.0。",
                "改法三：换掉这个依赖。",
            ),
            rule=self.name,
        )


class StrongCopyleftInboundRule:
    """上游是强传染许可（GPL / AGPL）：整份作品必须同样开源。"""

    name = "strong-copyleft-inbound"

    def match(self, ctx: CompatContext) -> Verdict | None:
        if not ctx.inbound.is_strong_copyleft:
            return None
        if ctx.outbound.is_strong_copyleft:
            return _verdict(
                ctx,
                LEVEL_OK,
                f"上游 {ctx.inbound.id} 与你的项目许可 {ctx.outbound.id} 同属传染性许可，可共存（需遵守较严格者）。",
                notes=("务必在 README 中说明「衍生作品需同样开源」。",),
                rule=self.name,
            )
        return _verdict(
            ctx,
            LEVEL_FORBIDDEN,
            f"{ctx.inbound.id} 具有强传染性，衍生作品必须同样开源；以 {ctx.outbound.id} 发布违反了这一义务。",
            notes=(
                f"改法一：把项目许可改为 {ctx.inbound.id}。",
                "改法二：换掉该依赖（或改用 LGPL / MIT 的等价库）。",
                "若只是通过网络调用该库所在的服务（未链接代码），通常不构成衍生作品，但仍需人工确认。",
            ),
            rule=self.name,
        )


class FallbackRule:
    """兜底：未覆盖的组合一律标为「有条件」，绝不假装自己知道。"""

    name = "fallback"

    def match(self, ctx: CompatContext) -> Verdict | None:
        return _verdict(
            ctx,
            LEVEL_CONDITIONAL,
            f"本工具的知识库暂未覆盖 {ctx.inbound.id} → {ctx.outbound.id} 这一组合，请人工确认。",
            notes=("建议查阅 https://choosealicense.com 或 SPDX 许可列表。",),
            rule=self.name,
        )


#: 规则注册表：按顺序求值，先匹配者胜出
RULES: tuple[CompatibilityRule, ...] = (
    SameLicenseRule(),
    NonCommercialInboundRule(),
    PermissiveInboundRule(),
    WeakCopyleftInboundRule(),
    StrongCopyleftInboundRule(),
    FallbackRule(),
)


def check(inbound: str, outbound: str, linkage: str = LINKAGE_DYNAMIC) -> Verdict:
    """判断「以 outbound 许可发布的项目」能否使用「inbound 许可的依赖」。"""
    src, dst = normalize(inbound), normalize(outbound)
    if src is None or dst is None:
        unknown = [raw for raw, nid in ((inbound, src), (outbound, dst)) if nid is None]
        return Verdict(
            level=LEVEL_UNKNOWN,
            inbound=src or inbound,
            outbound=dst or outbound,
            reason="无法识别的许可证：" + "、".join(repr(u) for u in unknown),
            notes=("请在 https://choosealicense.com 或 SPDX 许可列表中核对写法。",),
            rule="unknown-license",
        )
    ctx = CompatContext(inbound=ALL_LICENSES[src], outbound=ALL_LICENSES[dst], linkage=linkage)
    for rule in RULES:
        verdict = rule.match(ctx)
        if verdict is not None:
            basis = tuple(ctx.inbound.basis)
            return replace(verdict, basis=verdict.basis + basis)
    raise AssertionError("规则注册表缺少兜底规则")  # pragma: no cover


def matrix() -> list[tuple[str, list[Verdict]]]:
    """生成「上游 → 我的项目」兼容性矩阵（课堂必记 5 种两两组合）。"""
    return [(src, [check(src, dst) for dst in CORE_IDS]) for src in CORE_IDS]


# --------------------------------------------------------------------------- #
# 依赖清单扫描
# --------------------------------------------------------------------------- #
#: 输入契约：每行 <包名> [比较符+版本] [ # 许可证]
_LINE_RE = re.compile(
    r"^\s*(?P<name>[A-Za-z0-9][A-Za-z0-9._\-/]*)"
    r"(?:\s*(?:==|>=|<=|~=|!=|>|<|@)\s*(?P<version>[^\s#]+))?"
    r"\s*(?:(?:#|//)\s*(?P<license>.*))?$"
)


@dataclass(frozen=True)
class Finding:
    """依赖清单里的一行。"""

    line_no: int
    name: str
    version: str = ""
    license_raw: str = ""
    license_id: str | None = None

    @property
    def recognized(self) -> bool:
        return self.license_id is not None


def scan_text(text: str) -> list[Finding]:
    """解析依赖清单文本，返回每一行的识别结果。"""
    findings: list[Finding] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("//"):
            continue
        m = _LINE_RE.match(line)
        if not m:
            findings.append(Finding(line_no=line_no, name=stripped.split()[0], license_raw=""))
            continue
        raw_license = (m.group("license") or "").strip()
        findings.append(
            Finding(
                line_no=line_no,
                name=m.group("name"),
                version=(m.group("version") or "").strip(),
                license_raw=raw_license,
                license_id=normalize(raw_license),
            )
        )
    return findings


@dataclass(frozen=True)
class DependencyVerdict:
    """单个依赖相对项目许可的判定结果。"""

    finding: Finding
    verdict: Verdict | None

    @property
    def symbol(self) -> str:
        if self.finding.license_id is None:
            return "❓"
        assert self.verdict is not None
        return self.verdict.symbol


@dataclass(frozen=True)
class Report:
    """一次扫描的完整结论。"""

    project_license: str
    linkage: str
    items: tuple[DependencyVerdict, ...]

    @property
    def blocked(self) -> tuple[DependencyVerdict, ...]:
        return tuple(i for i in self.items if i.verdict is not None and i.verdict.level == LEVEL_FORBIDDEN)

    @property
    def unknown(self) -> tuple[DependencyVerdict, ...]:
        return tuple(i for i in self.items if i.finding.license_id is None)

    @property
    def conclusion(self) -> str:
        if self.blocked:
            return f"❌ 当前依赖组合**不能**以 {self.project_license} 发布，共 {len(self.blocked)} 个依赖冲突。"
        if self.unknown:
            return (
                f"⚠️ 未发现明确冲突，但有 {len(self.unknown)} 个依赖的许可证无法识别，"
                "补齐后才能给出结论。"
            )
        return f"✅ 当前依赖组合**可以**以 {self.project_license} 发布，注意履行下方义务清单。"


def build_report(text: str, project_license: str = "MIT", linkage: str = LINKAGE_DYNAMIC) -> Report:
    """扫描依赖清单并逐条与项目许可比对。"""
    findings = scan_text(text)
    items = []
    for finding in findings:
        verdict = None
        if finding.license_id is not None:
            verdict = check(finding.license_id, project_license, linkage=linkage)
        items.append(DependencyVerdict(finding=finding, verdict=verdict))
    return Report(project_license=project_license, linkage=linkage, items=tuple(items))


def aggregated_obligations(report: Report) -> list[tuple[str, tuple[str, ...]]]:
    """按许可聚合义务清单，去重且保持稳定顺序。"""
    seen: dict[str, tuple[str, ...]] = {}
    for item in report.items:
        lid = item.finding.license_id
        if lid and lid not in seen:
            seen[lid] = ALL_LICENSES[lid].obligations
    return list(seen.items())


def render_report(report: Report) -> str:
    """把扫描结果渲染成 Markdown 报告。"""
    lines: list[str] = []
    lines.append("# 许可证合规扫描报告")
    lines.append("")
    lines.append(f"- 项目拟采用许可：**{report.project_license}**")
    lines.append(f"- 链接方式假设：**{report.linkage}**（动态链接 / 静态链接）")
    lines.append(f"- 依赖条目：{len(report.items)}")
    lines.append("")
    lines.append("## 结论")
    lines.append("")
    lines.append(report.conclusion)
    lines.append("")
    lines.append("## 逐条判定")
    lines.append("")
    lines.append("| 行号 | 依赖 | 版本 | 声明许可 | 归一化 | 判定 |")
    lines.append("|------|------|------|----------|--------|------|")
    for item in report.items:
        f = item.finding
        normalized = f.license_id or "—"
        detail = item.verdict.level if item.verdict else "未识别"
        lines.append(f"| {f.line_no} | {f.name} | {f.version or '—'} | {f.license_raw or '—'} | {normalized} | {item.symbol} {detail} |")
    lines.append("")

    blocked = report.blocked
    if blocked:
        lines.append("## 冲突详情")
        lines.append("")
        for item in blocked:
            assert item.verdict is not None
            lines.append(f"### {item.finding.name}（{item.finding.license_id}）")
            lines.append("")
            lines.append(f"- 判定：{item.verdict.level}")
            lines.append(f"- 依据：{item.verdict.reason}")
            for note in item.verdict.notes:
                lines.append(f"- 建议：{note}")
            lines.append("")

    unknown = report.unknown
    if unknown:
        lines.append("## 待补全的依赖")
        lines.append("")
        for item in unknown:
            lines.append(f"- 第 {item.finding.line_no} 行：{item.finding.name}（未声明许可证）")
        lines.append("")

    obligations_list = aggregated_obligations(report)
    if obligations_list:
        lines.append("## 你需要履行的义务")
        lines.append("")
        for lid, items in obligations_list:
            lines.append(f"**{lid}**")
            for ob in items:
                lines.append(f"- [ ] {ob}")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("> 本报告由 license-lens 生成，仅作辅助判断，不构成法律意见。")
    return "\n".join(lines)


def render_matrix() -> str:
    """渲染兼容性矩阵（行=上游依赖许可，列=我的项目许可）。"""
    rows = matrix()
    lines = ["| 上游 \\ 我的 | " + " | ".join(CORE_IDS) + " |", "|" + "---|" * (len(CORE_IDS) + 1)]
    for src, verdicts in rows:
        cells = " | ".join(f"{v.symbol} {v.level}" for v in verdicts)
        lines.append(f"| **{src}** | {cells} |")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# v0.2：适用范围 / 商用评估 / 适配方案
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CommercialAdvice:
    """某个商用场景下的结论。"""

    scenario: str
    verdict: str
    note: str


@dataclass(frozen=True)
class Adaptation:
    """一条把当前组合改成合规组合的具体路径。"""

    title: str
    feasibility: str
    action: str
    caveat: str = ""


def render_scope(raw: str) -> str:
    """输出一种许可证的适用范围、商用边界与法源。"""
    info = lookup(raw)
    lines = [
        f"# {info.name}（{info.id}）",
        "",
        f"- 类型：**{info.category}**",
        f"- 商用：**{info.commercial_use}**",
        f"- OSI 认证：{'是' if info.osi_approved else '否'} ｜ FSF 自由许可：{'是' if info.fsf_free else '否'}",
        f"- 专利授权：{'有（明示）' if info.patent_grant else '无（仅默认版权许可）'}",
        f"- 商标授权：{'有' if info.trademark_license else '无'}",
        f"- 链接传染性：{info.linking_effect}",
        f"- 网络服务传染：{'是（AGPL 式）' if info.network_copyleft else '否'}",
        f"- 源码义务：{info.source_obligation}",
        f"- 参考：{info.url}",
        "",
        "## 适用范围（覆盖什么）",
        "",
    ]
    lines += [f"- {x}" for x in info.covers] or ["- （未登记）"]
    lines += ["", "## 不覆盖什么", ""]
    lines += [f"- {x}" for x in info.does_not_cover] or ["- （未登记）"]
    lines += ["", "## 商用说明", ""]
    lines += [f"- {x}" for x in info.commercial_notes] or ["- （未登记）"]
    lines += ["", "## 关键义务", ""]
    lines += [f"- [ ] {x}" for x in info.obligations]
    lines += ["", "## 判定依据（法源）", ""]
    lines += [f"- {x}" for x in info.basis] or ["- （未登记）"]
    lines += [
        "",
        "> 依据来自许可证官方原文与 OSI / FSF / choosealicense 的公开资料，不构成法律意见。",
    ]
    return "\n".join(lines)


def commercial_advice(raw: str) -> tuple[LicenseInfo, tuple[CommercialAdvice, ...]]:
    """按常见商用场景给出「能不能商用」的判断。"""
    info = lookup(raw)

    if info.is_noncommercial:
        rows = tuple(
            CommercialAdvice(s, "❌ 不可以", f"{info.id} 仅限非商业用途")
            for s in ("销售软件", "SaaS 订阅服务", "公司内部营利业务", "嵌入商业硬件")
        )
        return info, rows

    if info.id == "GPL-3.0":
        return info, (
            CommercialAdvice("销售软件", "✅ 可以", "可以收费，但对外分发时须提供完整源码，衍生作品须以 GPL 授权"),
            CommercialAdvice("SaaS 服务", "✅ 可以", "GPL-3.0 不要求向网络用户提供源码（这是它与 AGPL 的关键差别）"),
            CommercialAdvice("内部使用", "✅ 可以", "未对外分发，通常不触发源码义务"),
            CommercialAdvice("闭源产品内嵌", "❌ 不可以", "把 GPL 代码链接进闭源产品后对外分发，违反 §5"),
        )

    if info.id == "LGPL-3.0":
        return info, (
            CommercialAdvice("销售软件（动态链接）", "✅ 可以", "保持动态链接并允许使用者替换库，即可闭源销售"),
            CommercialAdvice("SaaS 服务", "✅ 可以", "动态链接下通常无源码义务"),
            CommercialAdvice("静态链接", "⚠️ 有条件", "须提供目标文件等重链接方式，或以 LGPL/GPL 开源你的程序"),
            CommercialAdvice("修改库本身", "⚠️ 有条件", "修改部分必须以 LGPL 开源"),
        )

    if info.id == "AGPL-3.0":
        return info, (
            CommercialAdvice("销售软件", "✅ 可以", "可以收费，但须提供完整源码，衍生作品须以 AGPL 授权"),
            CommercialAdvice("SaaS / 网络服务", "⚠️ 有条件", "必须向所有网络用户提供完整对应源码（§13）"),
            CommercialAdvice("内部使用", "✅ 可以", "仅内部使用、不对外提供服务时义务较轻"),
            CommercialAdvice("闭源 SaaS", "❌ 不可以", "网络交互即触发源码义务"),
        )

    if info.commercial_use == "有条件":
        return info, (
            CommercialAdvice("商业使用", "⚠️ 有条件", "需满足许可中约定的条件，详见下方商用说明"),
        )

    return info, (
        CommercialAdvice("销售软件", "✅ 可以", "可闭源销售，只需保留版权与许可声明"),
        CommercialAdvice("SaaS 服务", "✅ 可以", "无额外源码义务"),
        CommercialAdvice("嵌入商业产品", "✅ 可以", "保留声明即可"),
        CommercialAdvice("公司内部使用", "✅ 可以", "无额外限制"),
    )


def adaptations(inbound: str, outbound: str, linkage: str = LINKAGE_DYNAMIC) -> tuple[Verdict, tuple[Adaptation, ...]]:
    """给出「从当前组合改成合规组合」的具体路径。"""
    verdict = check(inbound, outbound, linkage=linkage)
    src, dst = normalize(inbound), normalize(outbound)
    if src is None or dst is None:
        return verdict, (
            Adaptation("先修正许可证写法", "必须", "用 SPDX 标识或 choosealicense 上的标准名称重新输入。"),
        )

    info = ALL_LICENSES[src]
    project = ALL_LICENSES[dst]
    options: list[Adaptation] = []

    if verdict.level == LEVEL_OK:
        options.append(
            Adaptation(
                "保持现状",
                "推荐",
                f"直接以 {project.id} 发布，同时逐条履行 {info.id} 的义务。",
                f"义务清单：python -m license_lens obligations {info.id}",
            )
        )
        options.append(
            Adaptation(
                "补一份第三方声明",
                "推荐",
                "在 README 或 NOTICE 中列出所有依赖及其许可证，便于审计与交付。",
                "可用 python -m license_lens scan deps.txt 生成这份清单。",
            )
        )
        return verdict, tuple(options)

    if info.is_noncommercial:
        return verdict, (
            Adaptation("换成可商用的替代品", "推荐", "寻找功能等价、且采用 MIT / Apache-2.0 / BSD-3 的库。", "最彻底，优先考虑。"),
            Adaptation("购买商业授权", "可行", "联系版权方购买商业许可，取得商业使用资格。", "需要预算与商务流程。"),
            Adaptation("限定为非商业用途", "有条件", "只在课程、研究、个人非商业项目中使用。", "一旦涉及收费或公司营利业务即违约。"),
        )

    if info.is_strong_copyleft:
        options += [
            Adaptation(f"把项目许可改为 {info.id}", "推荐", f"将项目整体改为 {info.id}，并公开源码。", "最简单、最稳妥，也是课堂项目的常见做法。"),
            Adaptation("替换该依赖", "可行", "换成许可更宽松、功能等价的库。", "需要评估替换成本与功能差异。"),
        ]
        if info.network_copyleft:
            options.append(
                Adaptation("拆成独立网络服务", "有条件", "把该组件作为独立服务部署，通过 HTTP/API 调用，不链接进主程序。", "网络边界认定存在争议，务必咨询法律意见。")
            )
        else:
            options.append(
                Adaptation("拆成独立进程 / 服务", "有条件", "通过子进程、RPC 或独立服务调用，避免形成单一衍生作品。", "边界认定存在争议，务必咨询法律意见。")
            )
        options += [
            Adaptation("仅内部使用、不对外分发", "有条件", "GPL 的源码义务由「分发」触发，内部使用通常不触发。", "一旦对外提供二进制或服务，需重新评估。"),
            Adaptation("购买商业授权", "可行", "联系版权方购买豁免 GPL 的商业许可。", "多数开源项目并不提供。"),
        ]
        return verdict, tuple(options)

    if info.is_weak_copyleft:
        return verdict, (
            Adaptation("改为动态链接", "推荐", "用动态库 / 独立进程方式调用，不要静态编译进你的程序。", "同时要允许使用者替换该库。"),
            Adaptation(f"把项目许可改为 {info.id} 或 GPL-3.0", "可行", "让项目本身也采用传染性许可，义务自然满足。", "会改变你项目的开源方式。"),
            Adaptation("替换该依赖", "可行", "换成 MIT / Apache-2.0 的等价库。", "优先确认是否有官方替代品。"),
            Adaptation("购买商业授权", "可行", "部分商业库提供免 LGPL 义务的商业许可。", "需要预算。"),
        )

    return verdict, (
        Adaptation("更换项目许可", "可行", f"把项目许可改为 {info.id}，即可直接使用该依赖。", "会改变你项目的开放方式。"),
        Adaptation("替换该依赖", "可行", "换成与你项目许可兼容的库。", "注意检查该库自身的传递依赖。"),
    )


def render_commercial(raw: str) -> str:
    """输出一种许可证的商用评估报告。"""
    info, rows = commercial_advice(raw)
    lines = [
        f"# {info.name}（{info.id}）商用评估",
        "",
        f"- 总体结论：**{info.commercial_use}**",
        f"- OSI 认证：{'是' if info.osi_approved else '否'}（非 OSI 许可不等于不能商用，但风险更高）",
        "",
        "| 场景 | 能否商用 | 说明 |",
        "|------|----------|------|",
    ]
    lines += [f"| {r.scenario} | {r.verdict} | {r.note} |" for r in rows]
    lines += ["", "## 商用注意事项", ""]
    lines += [f"- {x}" for x in info.commercial_notes] or ["- （未登记）"]
    lines += ["", "## 判定依据", ""]
    lines += [f"- {x}" for x in info.basis] or ["- （未登记）"]
    lines += ["", "> 本评估仅供参考，不构成法律意见；商用前建议由法务复核。"]
    return "\n".join(lines)


def render_adaptations(verdict: Verdict, options: tuple[Adaptation, ...]) -> str:
    """输出适配方案。"""
    lines = [
        "# 适配方案",
        "",
        f"当前判定：{verdict.symbol} **{verdict.level}**（上游 {verdict.inbound} → 我的项目 {verdict.outbound}）",
        "",
        f"依据：{verdict.reason}",
        "",
        "## 可选的改法",
        "",
        "| 方案 | 可行性 | 具体做法 | 注意事项 |",
        "|------|--------|----------|----------|",
    ]
    lines += [f"| {o.title} | {o.feasibility} | {o.action} | {o.caveat} |" for o in options]
    if verdict.basis:
        lines += ["", f"## 判定依据（法源，来自上游 {verdict.inbound}）", ""]
        lines += [f"- {b}" for b in verdict.basis]
    lines += ["", "> 适配方案是工程建议，最终合规性请以许可证原文与专业法律意见为准。"]
    return "\n".join(lines)
