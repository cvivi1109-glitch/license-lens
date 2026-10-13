"""命令行界面的单元测试（不依赖第三方库，直接调用 main()）。"""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from license_lens.cli import main

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def run(*argv):
    """运行 CLI，返回 (退出码, 标准输出, 标准错误)。"""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


class TestCli(unittest.TestCase):
    def test_no_args_prints_help_and_returns_usage_error(self):
        code, out, _ = run()
        self.assertEqual(code, 3)
        self.assertIn("license-lens", out)

    def test_list_shows_core_licenses(self):
        code, out, _ = run("list")
        self.assertEqual(code, 0)
        for lid in ("MIT", "Apache-2.0", "BSD-3-Clause", "GPL-3.0", "LGPL-3.0"):
            self.assertIn(lid, out)

    def test_list_all_includes_optional_extension(self):
        _, out, _ = run("list", "--all")
        self.assertIn("AGPL-3.0", out)

    def test_show_license(self):
        code, out, _ = run("show", "Apache 2.0")
        self.assertEqual(code, 0)
        self.assertIn("NOTICE", out)

    def test_show_unknown_returns_3(self):
        code, _, err = run("show", "WTFPL")
        self.assertEqual(code, 3)
        self.assertIn("无法识别", err)

    def test_obligations_outputs_checkboxes(self):
        code, out, _ = run("obligations", "MIT")
        self.assertEqual(code, 0)
        self.assertIn("- [ ]", out)

    def test_check_allowed_returns_0(self):
        code, out, _ = run("check", "MIT", "GPL-3.0")
        self.assertEqual(code, 0)
        self.assertIn("允许", out)

    def test_check_forbidden_returns_2(self):
        code, out, _ = run("check", "GPL-3.0", "MIT")
        self.assertEqual(code, 2)
        self.assertIn("禁止", out)

    def test_check_lgpl_static_returns_2(self):
        code, _, _ = run("check", "LGPL-3.0", "MIT", "--linkage", "static")
        self.assertEqual(code, 2)

    def test_matrix_returns_0(self):
        code, out, _ = run("matrix")
        self.assertEqual(code, 0)
        self.assertIn("LGPL-3.0", out)

    def test_scan_example_with_unknown_dependency_returns_1(self):
        code, out, _ = run("scan", str(EXAMPLES / "deps.txt"))
        self.assertEqual(code, 1)
        self.assertIn("许可证合规扫描报告", out)

    def test_scan_conflict_example_returns_2(self):
        code, out, _ = run("scan", str(EXAMPLES / "deps-gpl-conflict.txt"))
        self.assertEqual(code, 2)
        self.assertIn("冲突详情", out)

    def test_scan_missing_file_returns_3(self):
        code, _, err = run("scan", str(EXAMPLES / "not-exists.txt"))
        self.assertEqual(code, 3)
        self.assertIn("无法读取", err)

    def test_scan_writes_report_file(self):
        target = EXAMPLES / "_tmp_report.md"
        try:
            code, out, _ = run("scan", str(EXAMPLES / "deps.txt"), "--output", str(target))
            self.assertEqual(code, 1)
            self.assertIn("报告已写入", out)
            self.assertTrue(target.exists())
            self.assertIn("许可证合规扫描报告", target.read_text(encoding="utf-8"))
        finally:
            if target.exists():
                target.unlink()


if __name__ == "__main__":
    unittest.main()
