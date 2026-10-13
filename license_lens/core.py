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
from dataclasses import dataclass
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
            return verdict
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
