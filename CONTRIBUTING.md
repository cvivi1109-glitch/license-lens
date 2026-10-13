# 贡献指南

感谢你愿意为 license-lens 出一份力。本文档说明「怎么提问题」和「怎么改代码」。

## 一、报告问题（Issue）

提 Issue 前请先在 [现有 Issue](../../issues) 里搜一下，避免重复。

请使用仓库自带模板：

- **Bug 反馈**：`.github/ISSUE_TEMPLATE/bug_report.md`
- **功能建议**：`.github/ISSUE_TEMPLATE/feature_request.md`

好的 Issue 应当包含：

| 要素 | 写法示例 |
|------|----------|
| 现象 | `check LGPL-3.0 MIT --linkage static` 返回了「允许」 |
| 复现步骤 | 1. 执行命令 2. 观察输出 |
| 期望结果 | 应当返回「禁止」 |
| 实际结果 | 粘贴真实输出 |
| 环境 | Python 3.12.4 / Windows 11 / commit `abc1234` |

## 二、提交代码（Pull Request）

### 1. 开发流程

```bash
git checkout -b feature/add-agpl-network-clause     # 从 main 拉分支
# ... 改代码 ...
python -m unittest discover -s tests -v             # 必须全绿
git commit -m "feat(rules): 新增 AGPL 网络服务条款判定"
git push -u origin feature/add-agpl-network-clause
```

### 2. 分支命名

| 前缀 | 用途 |
|------|------|
| `feature/xxx` | 新功能 |
| `fix/xxx` | 修 Bug |
| `docs/xxx` | 只改文档 |
| `refactor/xxx` | 重构，不改行为 |

### 3. 提交信息规范（Conventional Commits）

格式：`<类型>(<范围>): <一句话说明>`

| 类型 | 用途 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修 Bug |
| `docs` | 文档 |
| `test` | 测试 |
| `refactor` | 重构 |
| `chore` | 构建 / 配置 / 杂项 |

范围建议：`core`、`cli`、`licenses`、`docs`、`ci`。

示例：
```
feat(core): 支持 MPL-2.0 的文件级传染判定
fix(cli): 修正 scan 在空清单下的退出码
docs(readme): 补充环境依赖说明
```

### 4. 新增一种许可证

只改 `license_lens/licenses.py`：在 `LICENSE_DB`（课堂必记）或 `OPTIONAL_LICENSES`（扩展）里追加一条 `LicenseInfo`。
如果你的许可有特殊的兼容性语义（例如 AGPL 的网络服务条款），再按下面的方式加规则。

### 5. 新增一条兼容性规则

在 `license_lens/core.py` 中写一个类，实现 `CompatibilityRule` 协议，然后注册进 `RULES`：

```python
class MyRule:
    name = "my-rule"

    def match(self, ctx: CompatContext) -> Verdict | None:
        if not <适用条件>:
            return None
        return _verdict(ctx, LEVEL_OK, "判定依据……", rule=self.name)

RULES = (SameLicenseRule(), MyRule(), ..., FallbackRule())
```

注意：`FallbackRule` 必须始终留在最后，保证任何组合都有结论。

### 6. PR 自查清单

- [ ] `python -m unittest discover -s tests -v` 全部通过
- [ ] 新增行为有对应测试用例
- [ ] 新增的许可证 / 规则有 docstring 说明判定依据
- [ ] 文档（README / CHANGELOG）已同步更新
- [ ] 没有提交 `__pycache__`、报告文件、IDE 配置等无关内容

## 三、行为准则

- 讨论聚焦技术问题，对事不对人。
- 许可判定的分歧请附**依据来源**（SPDX 列表、choosealicense.com、官方许可证原文）。

## 四、许可证

贡献的代码将按本项目的 [MIT License](LICENSE) 授权。
