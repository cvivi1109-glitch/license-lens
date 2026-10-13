"""core 模块的单元测试。

运行：python -m unittest discover -s tests -v
"""

import unittest

from license_lens import core
from license_lens.core import (
    LEVEL_CONDITIONAL,
    LEVEL_FORBIDDEN,
    LEVEL_OK,
    LEVEL_UNKNOWN,
    build_report,
    check,
    normalize,
    obligations,
    render_matrix,
    render_report,
    scan_text,
)


class TestNormalize(unittest.TestCase):
    def test_exact_id(self):
        self.assertEqual(normalize("MIT"), "MIT")

    def test_common_spellings(self):
        self.assertEqual(normalize("MIT License"), "MIT")
        self.assertEqual(normalize("Apache 2.0"), "Apache-2.0")
        self.assertEqual(normalize("apache-2.0"), "Apache-2.0")
        self.assertEqual(normalize("GPLv3"), "GPL-3.0")
        self.assertEqual(normalize("BSD 3-Clause"), "BSD-3-Clause")
        self.assertEqual(normalize("lgpl-3.0"), "LGPL-3.0")

    def test_strips_surrounding_noise(self):
        self.assertEqual(normalize("  MIT  "), "MIT")

    def test_unknown_returns_none(self):
        self.assertIsNone(normalize("WTFPL"))
        self.assertIsNone(normalize(""))
        self.assertIsNone(normalize(None))


class TestObligations(unittest.TestCase):
    def test_mit_requires_attribution(self):
        items = obligations("MIT")
        self.assertTrue(any("版权" in i for i in items))

    def test_apache_mentions_notice_and_patent(self):
        joined = "".join(obligations("Apache-2.0"))
        self.assertIn("NOTICE", joined)
        self.assertIn("专利", joined)

    def test_unknown_raises(self):
        with self.assertRaises(core.UnknownLicenseError):
            obligations("NOT-A-LICENSE")


class TestCheck(unittest.TestCase):
    def test_same_license_allowed(self):
        v = check("MIT", "MIT")
        self.assertEqual(v.level, LEVEL_OK)
        self.assertEqual(v.exit_code, 0)

    def test_permissive_inbound_into_copyleft_allowed(self):
        self.assertEqual(check("MIT", "GPL-3.0").level, LEVEL_OK)
        self.assertEqual(check("BSD-3-Clause", "Apache-2.0").level, LEVEL_OK)

    def test_apache_inbound_carries_gpl2_warning(self):
        v = check("Apache-2.0", "GPL-3.0")
        self.assertEqual(v.level, LEVEL_OK)
        self.assertTrue(any("GPL-2.0-only" in note for note in v.notes))

    def test_gpl_inbound_into_permissive_forbidden(self):
        v = check("GPL-3.0", "MIT")
        self.assertEqual(v.level, LEVEL_FORBIDDEN)
        self.assertEqual(v.exit_code, 2)
        self.assertIn("传染", v.reason)

    def test_gpl_inbound_into_lgpl_forbidden(self):
        self.assertEqual(check("GPL-3.0", "LGPL-3.0").level, LEVEL_FORBIDDEN)

    def test_lgpl_dynamic_linking_allowed(self):
        v = check("LGPL-3.0", "MIT", linkage="dynamic")
        self.assertEqual(v.level, LEVEL_OK)
        self.assertTrue(any("替换" in note for note in v.notes))

    def test_lgpl_static_linking_forbidden_with_permissive_outbound(self):
        v = check("LGPL-3.0", "MIT", linkage="static")
        self.assertEqual(v.level, LEVEL_FORBIDDEN)
        self.assertTrue(any("动态链接" in note for note in v.notes))

    def test_lgpl_static_linking_allowed_with_copyleft_outbound(self):
        self.assertEqual(check("LGPL-3.0", "GPL-3.0", linkage="static").level, LEVEL_OK)

    def test_unknown_license_is_reported_not_guessed(self):
        v = check("WTFPL", "MIT")
        self.assertEqual(v.level, LEVEL_UNKNOWN)
        self.assertEqual(v.exit_code, 3)

    def test_rules_are_extensible_via_registry(self):
        self.assertIsInstance(core.RULES[-1], core.FallbackRule)
        self.assertGreaterEqual(len(core.RULES), 4)


class TestMatrix(unittest.TestCase):
    def test_diagonal_is_allowed(self):
        for src, verdicts in core.matrix():
            for verdict in verdicts:
                if verdict.inbound == verdict.outbound:
                    self.assertEqual(verdict.level, LEVEL_OK, f"{src} 对角线应为允许")

    def test_matrix_rendering_has_headers(self):
        text = render_matrix()
        self.assertIn("上游", text)
        for lid in core.CORE_IDS:
            self.assertIn(lid, text)


class TestScan(unittest.TestCase):
    TEXT = """# 依赖清单
requests==2.32.3        # Apache-2.0
flask==3.0.3            # BSD-3-Clause
pydantic==2.9.2         # MIT
psycopg2-binary==2.9.9  # LGPL-3.0
mystery-lib==0.1.0

some-gpl-tool==1.0      # GPL-3.0
"""

    def test_parses_names_versions_and_licenses(self):
        findings = scan_text(self.TEXT)
        self.assertEqual(len(findings), 6)
        first = findings[0]
        self.assertEqual(first.name, "requests")
        self.assertEqual(first.version, "2.32.3")
        self.assertEqual(first.license_id, "Apache-2.0")

    def test_unlabeled_dependency_is_unknown(self):
        findings = scan_text(self.TEXT)
        mystery = [f for f in findings if f.name == "mystery-lib"][0]
        self.assertIsNone(mystery.license_id)

    def test_report_detects_conflict(self):
        report = build_report(self.TEXT, project_license="MIT", linkage="dynamic")
        names = [i.finding.name for i in report.blocked]
        self.assertEqual(names, ["some-gpl-tool"])
        self.assertIn("不能", report.conclusion)

    def test_lgpl_dependency_is_allowed_under_dynamic_linking(self):
        report = build_report(self.TEXT, project_license="MIT", linkage="dynamic")
        names = [i.finding.name for i in report.blocked]
        self.assertNotIn("psycopg2-binary", names)

    def test_render_report_is_markdown_with_obligation_checkboxes(self):
        report = build_report(self.TEXT, project_license="Apache-2.0")
        text = render_report(report)
        self.assertIn("# 许可证合规扫描报告", text)
        self.assertIn("- [ ]", text)
        self.assertIn("## 冲突详情", text)


if __name__ == "__main__":
    unittest.main()
