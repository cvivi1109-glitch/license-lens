# 变更记录

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 计划中
- 从 `requirements.txt` / `package.json` / `pom.xml` 自动识别依赖，无需手工标注许可证
- 从 PyPI / npm 元数据自动抓取依赖许可（带离线缓存）
- HTML 报告输出，含兼容性矩阵图
- 支持 SPDX 表达式（如 `MIT OR Apache-2.0`）

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

[Unreleased]: https://github.com/USERNAME/license-lens/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/USERNAME/license-lens/releases/tag/v0.1.0
