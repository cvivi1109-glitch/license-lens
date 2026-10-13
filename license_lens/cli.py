"""license-lens 命令行界面。

用法：python -m license_lens <子命令> [参数]

退出码（便于接入 CI）：
    0 = 允许    1 = 有条件    2 = 禁止    3 = 未知/用法错误
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .core import (
    ALL_LICENSES,
    CORE_IDS,
    LINKAGE_CHOICES,
    LINKAGE_DYNAMIC,
    LEVEL_CONDITIONAL,
    LEVEL_UNKNOWN,
    build_report,
    check,
    obligations,
    render_matrix,
    render_report,
    scan_text,
)


def _ensure_utf8_output() -> None:
    """保证在 Windows 控制台也能输出中文与符号。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):  # pragma: no cover - 环境相关
            pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="license-lens",
        description="开源许可证合规扫描器：输入依赖清单，输出「能不能这样发布 + 要履行哪些义务」。",
        epilog="示例：python -m license_lens scan examples/deps.txt --project-license MIT",
    )
    parser.add_argument("--version", action="version", version=f"license-lens {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="<子命令>")

    p_list = sub.add_parser("list", help="列出知识库中的全部许可证")
    p_list.add_argument("--all", action="store_true", help="连可选的扩展许可一起列出")

    p_show = sub.add_parser("show", help="查看某种许可证的详情与义务")
    p_show.add_argument("license", help="许可证名称，例如 MIT / GPL-3.0 / Apache 2.0")

    p_ob = sub.add_parser("obligations", help="只输出义务清单（便于贴进 README）")
    p_ob.add_argument("license", help="许可证名称")

    p_check = sub.add_parser("check", help="判断一个依赖许可能否用于某种项目许可")
    p_check.add_argument("inbound", help="上游依赖的许可证")
    p_check.add_argument("outbound", help="你的项目要采用的许可证")
    p_check.add_argument(
        "--linkage",
        choices=LINKAGE_CHOICES,
        default=LINKAGE_DYNAMIC,
        help="链接方式：dynamic（默认，import/独立进程）或 static（静态链接/修改库源码）",
    )

    sub.add_parser("matrix", help="打印 5 种核心许可的兼容性矩阵")

    p_scan = sub.add_parser("scan", help="扫描依赖清单并生成合规报告")
    p_scan.add_argument("manifest", help="依赖清单文件路径（例如 examples/deps.txt）")
    p_scan.add_argument("--project-license", default="MIT", help="你的项目拟采用的许可证（默认 MIT）")
    p_scan.add_argument("--linkage", choices=LINKAGE_CHOICES, default=LINKAGE_DYNAMIC, help="链接方式假设")
    p_scan.add_argument("--output", help="把报告写到指定文件（默认打印到屏幕）")
    return parser


def _cmd_list(show_all: bool) -> int:
    ids = list(ALL_LICENSES) if show_all else list(CORE_IDS)
    print(f"{'许可证':<14}{'类型':<12}{'课程建议':<20}{'来源'}")
    print("-" * 68)
    for lid in ids:
        info = ALL_LICENSES[lid]
        source = "课堂必记" if lid in CORE_IDS else "可选扩展"
        print(f"{info.id:<14}{info.category:<12}{info.course_tip:<20}{source}")
    print()
    print(f"共 {len(ids)} 种。用法：python -m license_lens show <许可证>")
    return 0


def _cmd_show(raw: str) -> int:
    lid = None
    from .core import normalize

    lid = normalize(raw)
    if lid is None:
        print(f"❓ 无法识别的许可证：{raw!r}", file=sys.stderr)
        print("   可用写法示例：MIT / Apache 2.0 / BSD-3 / GPLv3 / LGPL-3.0", file=sys.stderr)
        return 3
    info = ALL_LICENSES[lid]
    print(f"{info.name}  ({info.id})")
    print(f"类型      : {info.category}")
    print(f"课程建议  : {info.course_tip}")
    print(f"参考      : {info.url}")
    print("关键义务  :")
    for ob in info.obligations:
        print(f"  - {ob}")
    return 0


def _cmd_obligations(raw: str) -> int:
    try:
        items = obligations(raw)
    except Exception:
        print(f"❓ 无法识别的许可证：{raw!r}", file=sys.stderr)
        return 3
    for ob in items:
        print(f"- [ ] {ob}")
    return 0


def _cmd_check(inbound: str, outbound: str, linkage: str) -> int:
    verdict = check(inbound, outbound, linkage=linkage)
    print(f"{verdict.symbol} [{verdict.level}] 上游 {verdict.inbound}  →  我的项目 {verdict.outbound}（{linkage}）")
    print(f"   依据：{verdict.reason}")
    for note in verdict.notes:
        print(f"   提示：{note}")
    return verdict.exit_code


def _cmd_scan(manifest: str, project_license: str, linkage: str, output: str | None) -> int:
    try:
        with open(manifest, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        print(f"❓ 无法读取依赖清单：{exc}", file=sys.stderr)
        return 3

    findings = scan_text(text)
    if not findings:
        print("❓ 依赖清单里没有可识别的条目。", file=sys.stderr)
        print("   格式约定：每行 <包名> [比较符+版本] [ # 许可证]", file=sys.stderr)
        return 3

    report = build_report(text, project_license=project_license, linkage=linkage)
    rendered = render_report(report)
    if output:
        with open(output, "w", encoding="utf-8") as fh:
            fh.write(rendered + "\n")
        print(f"报告已写入：{output}")
    else:
        print(rendered)

    if report.blocked:
        return 2
    if report.unknown:
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    _ensure_utf8_output()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "list":
        return _cmd_list(args.all)
    if args.command == "show":
        return _cmd_show(args.license)
    if args.command == "obligations":
        return _cmd_obligations(args.license)
    if args.command == "check":
        return _cmd_check(args.inbound, args.outbound, args.linkage)
    if args.command == "matrix":
        print(render_matrix())
        return 0
    if args.command == "scan":
        return _cmd_scan(args.manifest, args.project_license, args.linkage, args.output)

    parser.print_help()
    return 3


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
