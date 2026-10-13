# license-lens

> 把「常用许可证对比」这张表变成**可执行的规则**：给它一份依赖清单，它告诉你「你的项目能不能这样发布 + 你需要履行哪些义务」。

[![CI](https://github.com/USERNAME/license-lens/actions/workflows/ci.yml/badge.svg)](../../actions)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 这是什么问题

写 README 的时候，几乎所有人都会随手写一句 "License: MIT"。
但如果项目里引用了 **LGPL** 的库并静态链接、或者引用了 **GPL** 的库，这个 MIT 声明**本身就是违规的**。

现有的许可检查工具（`pip-licenses`、`licensecheck`）大多只做一件事：**把依赖的许可证列出来**。
它们不回答你真正关心的问题：

- 我**能不能**用 MIT 发布？
- 如果不能，**该改成什么**？
- 我到底要履行**哪些义务**？

`license-lens` 就是来回答这三个问题的。

---

## 特性

- **兼容性判定**：输入「上游依赖许可 + 我的项目许可 + 链接方式」，输出 `✅ 允许 / ⚠️ 有条件 / ❌ 禁止`，并给出**依据**与**改法**。
- **义务清单**：输出可直接勾选的 Markdown 待办清单（含 NOTICE、禁背书、专利授权等细节）。
- **依赖清单扫描**：一次扫描整个 `deps.txt`，生成 Markdown 合规报告。
- **兼容性矩阵**：一条命令打印 5 种核心许可的完整兼容性表，适合直接贴进汇报 PPT。
- **零第三方依赖**：只用 Python 标准库，clone 下来就能跑。
- **可扩展**：新增一种许可只改 `licenses.py`；新增一条规则只需注册一个类；新增一种输出格式只改渲染层。
- **不会瞎猜**：识别不了的许可一律标为 `❓ 未知`，并在报告中提示人工确认，绝不给出假的"通过"。

---

## 环境要求

| 项 | 要求 |
|----|------|
| Python | **3.10 或更高**（开发与验收环境：3.12.4） |
| 第三方依赖 | **无**（仅标准库） |
| 操作系统 | Windows / macOS / Linux（已在 Windows 11 + PowerShell 7 实测） |

> 单元测试也只用标准库 `unittest`，不需要安装任何包。

---

## 快速开始

```bash
git clone <你的仓库地址>
cd license-lens
python -m license_lens list          # 无需安装任何依赖，直接运行
```

预期输出：

```
许可证           类型          课程建议                来源
--------------------------------------------------------------------
MIT           宽松          工具 / 作业首选之一         课堂必记
Apache-2.0    宽松+专利       框架类更稳妥              课堂必记
BSD-3-Clause  宽松          与 MIT 相近场景          课堂必记
GPL-3.0       强传染         慎选，先懂传染性            课堂必记
LGPL-3.0      弱传染         库作者可考虑              课堂必记
```

（可选）以可编辑模式安装，获得 `license-lens` 命令：

```bash
pip install -e .
license-lens list
```

---

## 使用示例

### 1. 判断一个依赖能不能用

```bash
$ python -m license_lens check GPL-3.0 MIT
❌ [禁止] 上游 GPL-3.0  →  我的项目 MIT（dynamic）
   依据：GPL-3.0 具有强传染性，衍生作品必须同样开源；以 MIT 发布违反了这一义务。
   提示：改法一：把项目许可改为 GPL-3.0。
   提示：改法二：换掉该依赖（或改用 LGPL / MIT 的等价库）。
```

动态链接与静态链接的差别会被正确区分：

```bash
$ python -m license_lens check LGPL-3.0 MIT                      # 默认 dynamic
✅ [允许] 上游 LGPL-3.0  →  我的项目 MIT（dynamic）

$ python -m license_lens check LGPL-3.0 MIT --linkage static
❌ [禁止] 上游 LGPL-3.0  →  我的项目 MIT（static）
   提示：改法一：改用动态链接（本工具判定为「允许」）。
```

### 2. 扫描整份依赖清单

输入契约：每行 `<包名> [比较符+版本] [# 许可证]`（见 [`examples/deps.txt`](examples/deps.txt)）

```bash
$ python -m license_lens scan examples/deps.txt --project-license MIT
# 许可证合规扫描报告
- 项目拟采用许可：**MIT**
## 结论
⚠️ 未发现明确冲突，但有 1 个依赖的许可证无法识别，补齐后才能给出结论。
## 你需要履行的义务
**Apache-2.0**
- [ ] 随分发提供 NOTICE 文件（若上游提供）
...
```

反例（会判定为禁止）：

```bash
$ python -m license_lens scan examples/deps-gpl-conflict.txt
# 结论
❌ 当前依赖组合**不能**以 MIT 发布，共 1 个依赖冲突。
## 冲突详情
### some-gpl-tool（GPL-3.0）
- 判定：禁止
```

### 3. 打印兼容性矩阵

```bash
$ python -m license_lens matrix
| 上游 \ 我的 | MIT | Apache-2.0 | BSD-3-Clause | GPL-3.0 | LGPL-3.0 |
|---|---|---|---|---|---|
| **MIT** | ✅ 允许 | ✅ 允许 | ✅ 允许 | ✅ 允许 | ✅ 允许 |
| **GPL-3.0** | ❌ 禁止 | ❌ 禁止 | ❌ 禁止 | ✅ 允许 | ❌ 禁止 |
```

### 4. 其余命令

```bash
python -m license_lens show "Apache 2.0"        # 查看某许可详情（支持各种写法）
python -m license_lens obligations GPL-3.0      # 只输出义务清单，便于贴进 README
python -m license_lens list --all               # 含可选扩展许可（AGPL/MPL/ISC/Unlicense）
python -m license_lens scan examples/deps.txt --output report.md   # 报告写入文件
```

### 退出码（可接入 CI）

| 退出码 | 含义 |
|--------|------|
| 0 | 允许 |
| 1 | 有条件（存在未识别许可） |
| 2 | 禁止（存在冲突） |
| 3 | 未知 / 用法错误 |

---

## 架构说明

```
license_lens/
├── licenses.py   # 纯数据：许可知识库（id / 类型 / 义务 / 课程建议 / 别名）
├── core.py       # 纯逻辑：归一化 → 兼容性规则引擎 → 依赖清单扫描 → 报告渲染
└── cli.py        # 纯界面：参数解析与终端输出（不含任何业务规则）
```

**核心抽象：策略模式 + 规则注册表**

```python
class CompatibilityRule(Protocol):
    name: str
    def match(self, ctx: CompatContext) -> Verdict | None: ...

RULES = (SameLicenseRule(), PermissiveInboundRule(),
         WeakCopyleftInboundRule(), StrongCopyleftInboundRule(), FallbackRule())
```

按顺序求值，先匹配者胜出。带来的好处：

| 想做的事 | 需要改的地方 |
|----------|--------------|
| 新增一种许可证 | 只在 `licenses.py` 加一条数据 |
| 新增一条判定规则（例如 AGPL 网络服务条款） | 写一个实现 `CompatibilityRule` 的类，注册进 `RULES` |
| 新增一种输出格式（HTML / JSON） | 只加一个渲染函数，核心逻辑不动 |

详细的扩展点说明见 [`docs/设计说明.md`](docs/设计说明.md)。

---

## 开发与测试

```bash
python -m unittest discover -s tests -v     # 38 个用例，全部无需第三方依赖
```

提交前自查：

```bash
python -m unittest discover -s tests -v
python -m license_lens list
git status && git log --oneline -5
```

---

## 已知问题与限制

- **不是法律意见**：本工具的判定基于课堂许可对比表与常见实践，边界情况（尤其涉及专利、GPL-2.0-only、AGPL 网络服务条款）仍需人工确认。识别不了的组合会明确标为 `⚠️ 有条件`，不会假装通过。
- **依赖清单需人工标注许可证**：V0.1.0 不会自动从 PyPI/npm 抓取依赖的许可证，需要你在清单里写明（未来版本计划支持自动抓取）。
- **链接方式靠使用者声明**：`--linkage` 是使用者给出的假设；工具无法自动判断你是静态还是动态链接。
- **知识库覆盖有限**：核心 5 种（MIT / Apache-2.0 / BSD-3-Clause / GPL-3.0 / LGPL-3.0）+ 4 种扩展（ISC / MPL-2.0 / AGPL-3.0 / Unlicense）。
- **不支持 SPDX 表达式**：形如 `MIT OR Apache-2.0` 的双许可写法会被判为未识别。

完整变更记录见 [CHANGELOG.md](CHANGELOG.md)。

---

## 贡献

欢迎提 Issue 和 PR，请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。
Issue 请使用仓库自带的模板（Bug 反馈 / 功能建议）。

## 许可证

本项目采用 **MIT License**，详见 [LICENSE](LICENSE)。

> 选型说明：MIT 是义务最少的宽松许可，仅要求保留版权与许可声明，与项目可能引用的 Apache-2.0 / BSD-3-Clause 依赖完全兼容；本项目不希望传染使用者的作品，因此不选用 GPL。
