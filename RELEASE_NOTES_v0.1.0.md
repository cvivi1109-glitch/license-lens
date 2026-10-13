# v0.1.0 — 首个可用版本

**发布日期**：2026-10-13
**类型**：首个 Release（MVP）

---

## 一句话介绍

`license-lens` 是一个零依赖的命令行工具：给它一份依赖清单，它回答「你的项目能不能这样发布」以及「你必须履行哪些义务」。

---

## 这个版本包含什么

### 新增功能

| 命令 | 作用 |
|------|------|
| `python -m license_lens list` | 列出内置的 9 种许可证（课堂必记 5 种 + 扩展 4 种） |
| `python -m license_lens show <许可>` | 查看某个许可证的类型、课程建议与关键义务 |
| `python -m license_lens obligations <许可>` | 只输出可勾选的义务清单 |
| `python -m license_lens check <上游> <我的> [--linkage dynamic\|static]` | 判断能否这样发布，并给出依据与改法 |
| `python -m license_lens matrix` | 打印 5 种核心许可证的完整兼容性矩阵 |
| `python -m license_lens scan <清单文件> [--project-license MIT] [--output report.md]` | 扫描依赖清单并生成 Markdown 合规报告 |

### 核心能力

- 许可证写法归一化：`MIT License` / `Apache 2.0` / `GPLv3` / `BSD 3-Clause` / `LGPL-3.0` 均可识别。
- **动态链接与静态链接的区别对待**：`LGPL-3.0 → MIT` 在动态链接下判定为「允许」，静态链接下判定为「禁止」，并给出三种改法。
- 规则引擎采用**策略模式 + 规则注册表**，新增许可证或规则无需改动核心流程。
- 识别不了的许可证一律标为 `❓ 未知`，并在报告里列为"待补全"，**不会给出假的"通过"**。
- 命令行退出码约定（0/1/2/3），可直接接入 CI。

### 质量保障

- 38 个单元测试，全部基于 Python 标准库，零第三方依赖。
- GitHub Actions CI：Python 3.10 / 3.11 / 3.12 全量跑测试。
- 完整中文文档：README、设计说明、贡献指南。

---

## 安装与快速验证

本版本**无需安装**即可运行：

```bash
git clone <仓库地址>
cd license-lens
python -m unittest discover -s tests -v     # 38 个用例应全部通过
python -m license_lens check GPL-3.0 MIT    # 应输出 ❌ [禁止]
```

---

## 已知问题

- 依赖清单需要手工标注许可证，V0.1.0 不会自动抓取（计划在 V0.2 支持）。
- 链接方式由使用者通过 `--linkage` 声明，工具不会自动判断。
- 不支持 SPDX 表达式（`MIT OR Apache-2.0` 会被判为未识别）。
- 判定结果仅供参考，不构成法律意见；边界情况（专利、GPL-2.0-only、AGPL 网络条款）需人工确认。

完整清单见 README 的「已知问题与限制」。

---

## 下一步

V0.2 计划：自动解析依赖清单、从包元数据抓取许可证、HTML 报告。详见 [CHANGELOG.md](../CHANGELOG.md) 的 `[Unreleased]` 一节。

---

## 许可证

[MIT](../LICENSE)
