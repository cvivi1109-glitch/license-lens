# 变更记录

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 计划中
- 从 `requirements.txt` / `package.json` / `pom.xml` 自动识别依赖，无需手工标注许可证
- 从 PyPI / npm 元数据自动抓取依赖许可（带离线缓存）
- HTML 报告输出，含兼容性矩阵图
- 支持 SPDX 表达式（如 `MIT OR Apache-2.0`）

## [0.2.0] - 2026-11-11

### 新增
- `scope` 命令：输出适用范围（覆盖 / 不覆盖）、专利与商标授权、链接传染性、网络服务传染、源码义务与法源
- `commercial` 命令：按「销售软件 / SaaS / 内嵌 / 内部使用」分场景评估能否商用
- `adapt` 命令：不能混用时给出 5~6 条具体改法（改许可 / 动态链接 / 进程隔离 / 换依赖 / 买授权 / 仅内部使用）
- `check` 输出新增「判定依据（法源）」，每条判定附许可证条款号
- 知识库扩展：新增 AGPL-3.0、MPL-2.0、ISC、Unlicense，以及非商业许可 CC-BY-NC-4.0、PolyForm-Noncommercial-1.0.0、BUSL-1.1
- 新增 `NonCommercialInboundRule`：非商业许可默认判定为「有条件」
- 新增文档《协议的适用范围、适配与商用指南》
- 新增 24 个测试（总计 62 个）

### 变更
- `list` 输出增加「商用」列
- 适用范围与商用信息以结构化字段写入 `licenses.py`，规则引擎无需改动即可使用

## [0.1.0] - 2026-10-13

### 新增
- 许可证知识库：课堂必记 5 种（MIT / Apache-2.0 / BSD-3-Clause / GPL-3.0 / LGPL-3.0）+ 4 种扩展（ISC / MPL-2.0 / AGPL-3.0 / Unlicense）
- 许可证写法归一化：支持 `MIT License`、`Apache 2.0`、`GPLv3`、`BSD 3-Clause` 等常见别名
- 兼容性规则引擎（策略模式 + 规则注册表），输出 `允许 / 有条件 / 禁止 / 未知` 与判定依据
- 动态链接 / 静态链接对 LGPL 传染性的不同判定
- `scan` 依赖清单扫描，生成 Markdown 合规报告（含逐条判定、冲突详情、义务清单）
- `matrix` 兼容性矩阵输出，可直接粘贴进汇报材料
- 命令行退出码约定，便于接入 CI
- 38 个标准库单元测试，零第三方依赖
- GitHub Actions CI（Python 3.10 / 3.11 / 3.12）
- 贡献指南、Issue 模板、PR 模板

[Unreleased]: https://github.com/cvivi1109-glitch/license-lens/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/cvivi1109-glitch/license-lens/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/cvivi1109-glitch/license-lens/releases/tag/v0.1.0
