"""v0.2 新增能力：适用范围、商用评估、适配方案、判定依据。"""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

from license_lens import core
from license_lens.cli import main
from license_lens.core import (
    LEVEL_CONDITIONAL,
    LEVEL_FORBIDDEN,
    LEVEL_OK,
    adaptations,
    check,
    commercial_advice,
    render_commercial,
    render_scope,
)


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


class TestScope(unittest.TestCase):
    def test_mit_scope_has_coverage_and_basis(self):
        text = render_scope("MIT")
        self.assertIn("适用范围", text)
        self.assertIn("商用：**允许**", text)
        self.assertIn("判定依据", text)

    def test_gpl_scope_mentions_source_obligation_and_clauses(self):
        text = render_scope("GPL-3.0")
        self.assertIn("网络服务", text)
        self.assertIn("§5", text)
        self.assertIn("源码", text)

    def test_patent_and_trademark_fields(self):
        self.assertTrue(core.lookup("Apache-2.0").patent_grant)
        self.assertFalse(core.lookup("MIT").patent_grant)
        self.assertFalse(core.lookup("Apache-2.0").trademark_license)

    def test_linkage_and_network_flags(self):
        self.assertEqual(core.lookup("LGPL-3.0").linking_effect, "弱")
        self.assertEqual(core.lookup("GPL-3.0").linking_effect, "强")
        self.assertTrue(core.lookup("AGPL-3.0").network_copyleft)
        self.assertFalse(core.lookup("GPL-3.0").network_copyleft)


class TestCommercial(unittest.TestCase):
    def test_all_core_licenses_allow_commercial_use(self):
        for lid in core.CORE_IDS:
            self.assertTrue(core.lookup(lid).commercially_usable, lid)

    def test_gpl_allows_saas_but_not_closed_source_bundle(self):
        _, rows = commercial_advice("GPL-3.0")
        by_scenario = {r.scenario: r for r in rows}
        self.assertIn("可以", by_scenario["SaaS 服务"].verdict)
        self.assertIn("不可以", by_scenario["闭源产品内嵌"].verdict)

    def test_agpl_saas_is_conditional(self):
        _, rows = commercial_advice("AGPL-3.0")
        row = [r for r in rows if "SaaS" in r.scenario][0]
        self.assertIn("有条件", row.verdict)

    def test_lgpl_dynamic_commercial_is_allowed(self):
        _, rows = commercial_advice("LGPL-3.0")
        row = [r for r in rows if "动态链接" in r.scenario][0]
        self.assertIn("可以", row.verdict)

    def test_noncommercial_is_forbidden_everywhere(self):
        _, rows = commercial_advice("CC-BY-NC-4.0")
        self.assertTrue(all("不可以" in r.verdict for r in rows))
        self.assertFalse(core.lookup("CC-BY-NC-4.0").osi_approved)

    def test_busl_is_source_available_but_conditional(self):
        info = core.lookup("BUSL-1.1")
        self.assertEqual(info.commercial_use, "有条件")
        self.assertFalse(info.osi_approved)

    def test_render_commercial_contains_table_and_basis(self):
        text = render_commercial("GPL-3.0")
        self.assertIn("| 场景 | 能否商用 | 说明 |", text)
        self.assertIn("§5", text)


class TestAdaptations(unittest.TestCase):
    def test_gpl_into_mit_offers_relicense_and_replace(self):
        verdict, options = adaptations("GPL-3.0", "MIT")
        self.assertEqual(verdict.level, LEVEL_FORBIDDEN)
        titles = "".join(o.title for o in options)
        self.assertIn("GPL-3.0", titles)
        self.assertTrue(any("替换" in o.title for o in options))

    def test_lgpl_static_offers_dynamic_linking(self):
        verdict, options = adaptations("LGPL-3.0", "MIT", linkage="static")
        self.assertEqual(verdict.level, LEVEL_FORBIDDEN)
        self.assertTrue(any("动态链接" in o.title for o in options))

    def test_allowed_case_offers_keep_current(self):
        verdict, options = adaptations("MIT", "GPL-3.0")
        self.assertEqual(verdict.level, LEVEL_OK)
        self.assertTrue(any("保持现状" in o.title for o in options))

    def test_noncommercial_offers_replacement(self):
        verdict, options = adaptations("CC-BY-NC-4.0", "MIT")
        self.assertEqual(verdict.level, LEVEL_CONDITIONAL)
        self.assertTrue(any("替代品" in o.title for o in options))

    def test_agpl_offers_network_service_split(self):
        _, options = adaptations("AGPL-3.0", "MIT")
        self.assertTrue(any("网络服务" in o.title for o in options))


class TestBasis(unittest.TestCase):
    def test_verdict_carries_upstream_basis(self):
        verdict = check("GPL-3.0", "MIT")
        self.assertTrue(any("§5" in b for b in verdict.basis))

    def test_check_cli_prints_basis(self):
        code, out, _ = run("check", "GPL-3.0", "MIT")
        self.assertEqual(code, 2)
        self.assertIn("法源", out)

    def test_noncommercial_check_is_conditional(self):
        verdict = check("CC-BY-NC-4.0", "MIT")
        self.assertEqual(verdict.level, LEVEL_CONDITIONAL)


class TestV02Cli(unittest.TestCase):
    def test_scope_command(self):
        code, out, _ = run("scope", "Apache 2.0")
        self.assertEqual(code, 0)
        self.assertIn("专利授权：有", out)

    def test_commercial_command_without_argument(self):
        code, out, _ = run("commercial")
        self.assertEqual(code, 0)
        self.assertIn("BUSL-1.1", out)

    def test_commercial_command_with_argument(self):
        code, out, _ = run("commercial", "LGPL-3.0")
        self.assertEqual(code, 0)
        self.assertIn("静态链接", out)

    def test_adapt_command(self):
        code, out, _ = run("adapt", "GPL-3.0", "MIT")
        self.assertEqual(code, 0)
        self.assertIn("适配方案", out)
        self.assertIn("把项目许可改为 GPL-3.0", out)

    def test_list_all_shows_noncommercial(self):
        _, out, _ = run("list", "--all")
        self.assertIn("CC-BY-NC-4.0", out)
        self.assertIn("非商业", out)


if __name__ == "__main__":
    unittest.main()
