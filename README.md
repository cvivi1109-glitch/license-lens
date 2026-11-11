# license-lens

> **把「常用许可证对比」这张表变成可执行的规则。**
> 一条命令回答四个问题：**能不能混用？管什么？能不能商用？不能混怎么改？**

[![CI](https://github.com/cvivi1109-glitch/license-lens/actions/workflows/ci.yml/badge.svg)](https://github.com/cvivi1109-glitch/license-lens/actions)
![version](https://img.shields.io/badge/version-0.2.0-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 为什么需要它

写 README 的时候，几乎所有人都会随手写一句 `License: MIT`。
但如果项目里引用了 **GPL** 的库，或者**静态链接**了 **LGPL** 的库，这个 MIT 声明**本身就是违规的**。

现有的许可检查工具（`pip-licenses`、`licensecheck`）大多只做一件事：**把依赖的许可证列出来**。
它们不回答你真正关心的问题：

- 我**能不能**用 MIT 发布？
- 如果不能，**该改成什么**？
- 这个许可到底**管什么**（代码？专利？商标？网络服务？）
- 我到底要履行**哪些义务**、能不能**商用**？

`license-lens` 就是来回答这些问题的。

---

## 功能总览（v0.2）

| 能力 | 命令 | 输出 |
|------|------|------|
| **兼容性判定** | `check` | ✅ 允许 / ⚠️ 有条件 / ❌ 禁止 + 判定依据 + 法源 |
| **适用范围** | `scope` | 覆盖什么 / 不覆盖什么 / 专利 / 商标 / 链接 / 网络服务 / 源码义务 |
| **商用评估** | `commercial` | 按「销售软件 / SaaS / 内嵌 / 内部使用」分场景给结论 |
| **适配方案** | `adapt` | 5~6 条具体改法：改许可 / 动态链接 / 进程隔离 / 换依赖 / 买授权 |
| **义务清单** | `obligations` | 可直接勾选的 Markdown 清单 |
| **依赖清单扫描** | `scan` | 整份 `deps.txt` 的 Markdown 合规报告 |
| **兼容性矩阵** | `matrix` | 5 种核心许可的完整兼容性表，可直接贴进汇报 PPT |

另外：

- **判定依据可追溯**：每条结论都附条款号（GPL-3.0 §5/§6/§11、Apache-2.0 §2/§6、LGPL-3.0 §4、AGPL-3.0 §13）
- **零第三方依赖**：只用 Python 标准库，clone 下来就能跑
- **可扩展**：新增一种许可只改 `licenses.py`；新增一条规则只需注册一个类
- **不会瞎猜**：识别不了的许可标为 `❓ 未知`，不确定的组合标 `⚠️ 有条件`，绝不假装通过

---

## 快速开始

```bash
git clone https://github.com/cvivi1109-glitch/license-lens.git
cd license-lens
python -m license_lens list
```

预期输出：

```
许可证                           类型                      商用        来源
------------------------------------------------------------------------------
MIT                           宽松                      允许        课堂必记
Apache-2.0                    宽松+专利                   允许        课堂必记
BSD-3-Clause                  宽松                      允许        课堂必记
GPL-3.0                       强传染                     允许        课堂必记
LGPL-3.0                      弱传染                     有条件       课堂必记

共 5 种。
用法：python -m license_lens scope <许可证>    # 看适用范围与法源
      python -m license_lens commercial <许可证>  # 看商用评估
```

> 不需要 `pip install`，也不需要虚拟环境。Python 3.10+ 即可。

---

## 命令一览

| 命令 | 作用 | 示例 |
|------|------|------|
| `list` | 列出知识库（12 种） | `python -m license_lens list --all` |
| `show` | 查看某许可的类型与义务 | `python -m license_lens show "Apache 2.0"` |
| `scope` | 适用范围 + 法源 | `python -m license_lens scope GPL-3.0` |
| `commercial` | 商用评估 | `python -m license_lens commercial GPL-3.0` |
| `obligations` | 义务清单 | `python -m license_lens obligations MIT` |
| `check` | 两两兼容性判定 | `python -m license_lens check GPL-3.0 MIT` |
| `adapt` | 冲突时的改法 | `python -m license_lens adapt LGPL-3.0 MIT --linkage static` |
| `matrix` | 兼容性总表 | `python -m license_lens matrix` |
| `scan` | 扫描依赖清单 | `python -m license_lens scan examples/deps.txt` |

### 退出码（可接入 CI）

| 退出码 | 含义 |
|--------|------|
| 0 | 允许 |
| 1 | 有条件（存在未识别许可） |
| 2 | 禁止（存在冲突） |
| 3 | 未知 / 用法错误 |

---

## 使用示例

### 1. `check` —— 能不能混用（带法源）

```bash
$ python -m license_lens check GPL-3.0 MIT
```

```
❌ [禁止] 上游 GPL-3.0  →  我的项目 MIT（dynamic）
   依据：GPL-3.0 具有强传染性，衍生作品必须同样开源；以 MIT 发布违反了这一义务。
   提示：改法一：把项目许可改为 GPL-3.0。
   提示：改法二：换掉该依赖（或改用 LGPL / MIT 的等价库）。
   提示：若只是通过网络调用该库所在的服务（未链接代码），通常不构成衍生作品，但仍需人工确认。
   法源（来自上游 GPL-3.0）：
     - GPL-3.0 §5：向下游传递授权，衍生作品必须同样以 GPL 发布
     - §6：分发目标代码时须提供对应源码
     - §7：不授予商标权
     - §11：专利授权
     - FSF 兼容性列表：GPL-3.0 与 MIT / BSD-3 / Apache-2.0 兼容，与 GPL-2.0-only 不兼容
   改法：python -m license_lens adapt GPL-3.0 MIT
```

反过来就允许：

```bash
$ python -m license_lens check MIT GPL-3.0
✅ [允许] 上游 MIT  →  我的项目 GPL-3.0（dynamic）
```

> 这就是"传染只能单向升级，不能降级"。

### 2. `scope` —— 这个许可到底管什么

```bash
$ python -m license_lens scope GPL-3.0
```

```
# GNU General Public License v3.0（GPL-3.0）

- 类型：**强传染**
- 商用：**允许**
- 专利授权：有（明示）
- 商标授权：无
- 链接传染性：强
- 网络服务传染：否
- 源码义务：对外分发时必须提供完整对应源码（§6）

## 适用范围（覆盖什么）
- 源代码：复制、修改、分发
- 衍生作品：修改、链接、合并后形成的整体作品
- 对外分发：源码与二进制
- 专利：§11 明示授予专利许可

## 不覆盖什么
- 商标：§7 不授予商标权
- 内部使用：未对外分发时通常不触发源码义务
- 网络服务：GPL-3.0 不要求向网络用户提供源码（AGPL 才要求）

## 判定依据（法源）
- GPL-3.0 §5：向下游传递授权，衍生作品必须同样以 GPL 发布
- §6：分发目标代码时须提供对应源码
- §11：专利授权
```

### 3. `commercial` —— 能不能商用

```bash
$ python -m license_lens commercial GPL-3.0
```

```
# GNU General Public License v3.0（GPL-3.0）商用评估

- 总体结论：**允许**

| 场景 | 能否商用 | 说明 |
|------|----------|------|
| 销售软件 | ✅ 可以 | 可以收费，但对外分发时须提供完整源码，衍生作品须以 GPL 授权 |
| SaaS 服务 | ✅ 可以 | GPL-3.0 不要求向网络用户提供源码（这是它与 AGPL 的关键差别） |
| 内部使用 | ✅ 可以 | 未对外分发，通常不触发源码义务 |
| 闭源产品内嵌 | ❌ 不可以 | 把 GPL 代码链接进闭源产品后对外分发，违反 §5 |
```

不带参数时列出全部 12 种许可的商用总表：

```bash
$ python -m license_lens commercial
```

### 4. `adapt` —— 不能混用怎么办

```bash
$ python -m license_lens adapt LGPL-3.0 MIT --linkage static
```

```
# 适配方案

当前判定：❌ **禁止**（上游 LGPL-3.0 → 我的项目 MIT）

## 可选的改法

| 方案 | 可行性 | 具体做法 | 注意事项 |
|------|--------|----------|----------|
| 改为动态链接 | 推荐 | 用动态库 / 独立进程方式调用，不要静态编译进你的程序。 | 同时要允许使用者替换该库。 |
| 把项目许可改为 LGPL-3.0 或 GPL-3.0 | 可行 | 让项目本身也采用传染性许可，义务自然满足。 | 会改变你项目的开源方式。 |
| 替换该依赖 | 可行 | 换成 MIT / Apache-2.0 的等价库。 | 优先确认是否有官方替代品。 |
| 购买商业授权 | 可行 | 部分商业库提供免 LGPL 义务的商业许可。 | 需要预算。 |
```

### 5. `scan` —— 一次检查整份依赖清单

输入契约：每行 `<包名> [比较符+版本] [# 许可证]`（见 [`examples/deps.txt`](examples/deps.txt)）

```bash
$ python -m license_lens scan examples/deps.txt --project-license MIT
```

```
# 许可证合规扫描报告

- 项目拟采用许可：**MIT**
- 依赖条目：5

## 结论
⚠️ 未发现明确冲突，但有 1 个依赖的许可证无法识别，补齐后才能给出结论。

## 逐条判定
| 行号 | 依赖 | 声明许可 | 判定 |
| 5 | requests | Apache-2.0 | ✅ 允许 |
| 6 | flask | BSD-3-Clause | ✅ 允许 |
| 7 | pydantic | MIT | ✅ 允许 |
| 8 | psycopg2-binary | LGPL-3.0 | ✅ 允许 |
| 9 | numpy | — | ❓ 未识别 |

## 你需要履行的义务
**Apache-2.0**
- [ ] 随分发提供 NOTICE 文件（若上游提供）
...
```

### 6. `matrix` —— 兼容性总表

```bash
$ python -m license_lens matrix
```

```
| 上游 \ 我的 | MIT | Apache-2.0 | BSD-3-Clause | GPL-3.0 | LGPL-3.0 |
|---|---|---|---|---|---|
| **MIT** | ✅ 允许 | ✅ 允许 | ✅ 允许 | ✅ 允许 | ✅ 允许 |
| **Apache-2.0** | ✅ 允许 | ✅ 允许 | ✅ 允许 | ✅ 允许 | ✅ 允许 |
| **BSD-3-Clause** | ✅ 允许 | ✅ 允许 | ✅ 允许 | ✅ 允许 | ✅ 允许 |
| **GPL-3.0** | ❌ 禁止 | ❌ 禁止 | ❌ 禁止 | ✅ 允许 | ❌ 禁止 |
| **LGPL-3.0** | ✅ 允许 | ✅ 允许 | ✅ 允许 | ✅ 允许 | ✅ 允许 |
```

> 上表为**默认动态链接**；LGPL 在静态链接下对宽松许可的列会变为 ❌。

---

## 判定依据（法源）

所有结论都来自三层证据，**不是凭感觉**：

| 层级 | 依据 | 作用 |
|------|------|------|
| 第 1 层（最高） | **许可证原文条款** | GPL-3.0 §5/§6/§11、Apache-2.0 §2/§3/§4/§6、LGPL-3.0 §4/§5、AGPL-3.0 §13、CC BY-NC §2(a)(1) |
| 第 2 层 | **OSI 认证 / FSF 兼容性列表 / SPDX** | 判断是否开源、与谁兼容 |
| 第 3 层 | **choosealicense.com 等官方 FAQ** | 选型建议与解释 |
| 最终解释 | 法院 / 律师 | 工具明确声明"不构成法律意见" |

对"独立进程算不算衍生作品"这类**没有统一判例**的问题，工具一律标注"边界存在争议，需咨询法律意见"，不给假结论。

完整的适用范围与商用说明见 [docs/协议的适用范围与商用指南.md](docs/协议的适用范围与商用指南.md)。

---

## 许可证适用范围对比

| 许可证 | 专利授权 | 商标授权 | 源码义务 | 链接传染 | 网络服务 | 商用 |
|--------|:---:|:---:|---|---|:---:|---|
| MIT | ❌ | ❌ | 无 | 无 | 否 | ✅ 允许 |
| BSD-3-Clause | ❌ | ❌（禁背书） | 无 | 无 | 否 | ✅ 允许 |
| Apache-2.0 | ✅ §2 | ❌ §6 | 无 | 无 | 否 | ✅ 允许 |
| LGPL-3.0 | ✅ | ❌ | 改库 / 静态链接时 | 弱 | 否 | ⚠️ 有条件 |
| GPL-3.0 | ✅ §11 | ❌ §7 | 对外分发时 | 强 | 否 | ✅ 允许（须开源） |
| AGPL-3.0 | ✅ | ❌ | 分发或提供服务时 | 强 | **是 §13** | ✅ 允许（SaaS 须开源） |
| MPL-2.0 | ✅ | ❌ | 修改过的文件 | 弱（文件级） | 否 | ✅ 允许 |

**三个最容易判错的地方**：

1. **公司内部用 GPL** → 不分发，通常**不触发**源码义务
2. **GPL 做 SaaS** → GPL-3.0 **不要求**给网络用户源码；**AGPL 才要求**
3. **LGPL 静态链接** → 不能直接闭源；**动态链接才能**

---

## 商用速查

> **开源 ≠ 不能商用。** MIT / BSD / Apache / GPL / LGPL **全部允许商用**，区别只在"商用后要付出什么"。

| 许可证 | 能商用 | 代价 |
|--------|:---:|---|
| MIT / BSD-3 | ✅ | 保留版权与许可声明 |
| Apache-2.0 | ✅ | 保留 NOTICE + 标明修改 |
| LGPL-3.0 | ✅ | 动态链接 + 允许替换库 |
| GPL-3.0 | ✅ | 对外分发时公开源码，衍生作品同样 GPL |
| AGPL-3.0 | ✅ | 提供网络服务时公开源码 |
| BUSL-1.1 | ⚠️ | 生产环境通常需商业授权 |
| CC-BY-NC / PolyForm-NC | ❌ | 仅限非商业用途 |

按商业模式选许可：

| 你的模式 | 推荐 |
|----------|------|
| 卖闭源软件 | MIT / Apache-2.0 / BSD |
| 卖 SaaS 且不想开源 | MIT / Apache-2.0 / BSD（避开 AGPL） |
| 卖 SaaS 且愿意开源 | AGPL-3.0 |
| 卖技术支持 / 定制 | GPL-3.0 也可以 |
| 开源核心 + 商业版 | 核心 MIT / Apache |
| 硬件 / 嵌入式 | MIT / Apache（避开 GPL） |

---

## 架构说明

```
license_lens/
├── licenses.py   # 纯数据：12 种许可的结构化元数据
│                 #   类型 / 义务 / 适用范围 / 商用边界 / 专利商标 / 法源
├── core.py       # 纯逻辑：归一化 → 规则引擎 → 扫描 → 报告 → 商用/适配
└── cli.py        # 纯界面：参数解析与终端输出（不含任何业务规则）
```

**核心抽象：策略模式 + 规则注册表**

```python
class CompatibilityRule(Protocol):
    name: str
    def match(self, ctx: CompatContext) -> Verdict | None: ...

RULES = (SameLicenseRule(), NonCommercialInboundRule(), PermissiveInboundRule(),
         WeakCopyleftInboundRule(), StrongCopyleftInboundRule(), FallbackRule())
```

按顺序求值，先匹配者胜出：

| 想做的事 | 需要改的地方 |
|----------|--------------|
| 新增一种许可证 | 只在 `licenses.py` 加一条数据 |
| 新增一条判定规则（如 AGPL 网络条款） | 写一个实现 `CompatibilityRule` 的类，注册进 `RULES` |
| 新增一种输出格式（HTML / JSON） | 只加一个渲染函数，核心逻辑不动 |
| 新增一种商用场景 | 在 `commercial_advice()` 里加一条分支 |

`LicenseInfo` 的字段与扩展方式见 [docs/设计说明.md](docs/设计说明.md)。

---

## 开发与测试

```bash
python -m unittest discover -s tests -v     # 62 个用例，全部无需第三方依赖
```

```
Ran 62 tests in 0.05s

OK
```

CI：GitHub Actions 在 Python 3.10 / 3.11 / 3.12 上跑全量测试。

提交前自查：

```bash
python -m unittest discover -s tests -v
python -m license_lens list
git status && git log --oneline -5
```

---

## 已知问题与限制

- **不是法律意见**：判定基于许可证原文、OSI/FSF/SPDX 与常见实践；涉及专利、GPL-2.0-only、AGPL 网络条款、衍生作品认定等边界时仍需律师确认。
- **依赖清单需人工标注许可证**：V0.2.0 不会自动从 PyPI/npm 抓取，需要你在清单里写明（V0.3 计划支持）。
- **链接方式靠使用者声明**：`--linkage` 是使用者给出的假设，工具无法自动判断静态/动态链接。
- **知识库覆盖 12 种**：核心 5 种 + 扩展 7 种（ISC / MPL-2.0 / AGPL-3.0 / Unlicense / CC-BY-NC-4.0 / PolyForm-Noncommercial-1.0.0 / BUSL-1.1）。
- **不支持 SPDX 表达式**：`MIT OR Apache-2.0` 这类双许可写法会被判为未识别。

完整变更记录见 [CHANGELOG.md](CHANGELOG.md)，v0.2.0 的发布说明见 [RELEASE_NOTES_v0.2.0.md](RELEASE_NOTES_v0.2.0.md)。

---

## 文档

| 文档 | 内容 |
|------|------|
| [docs/协议的适用范围与商用指南.md](docs/协议的适用范围与商用指南.md) | **老师反馈的完整回答**：适用范围、适配手段、判定依据、商用模型 |
| [docs/设计说明.md](docs/设计说明.md) | 问题定义、设计模式、架构与扩展点（汇报用） |
| [docs/验收记录.md](docs/验收记录.md) | 所有命令的真实运行输出 |
| [docs/推送与首个Release指引.md](docs/推送与首个Release指引.md) | 仓库发布流程 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 贡献指南与提交规范 |

---

## 贡献

欢迎提 Issue 和 PR，请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。
Issue 请使用仓库自带的模板（Bug 反馈 / 功能建议）。

## 许可证

本项目采用 **MIT License**，详见 [LICENSE](LICENSE)。

> 选型说明：MIT 是义务最少的宽松许可，仅要求保留版权与许可声明，与本项目可能引用的 Apache-2.0 / BSD-3-Clause 依赖完全兼容；本项目不希望传染使用者的作品，因此不选用 GPL。
