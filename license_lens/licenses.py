"""开源许可证知识库。

数据来源：课堂幻灯片「常用许可证对比（课堂必记）」+ 各许可证官方原文。

v0.2 新增四个维度（对应老师的反馈）：
    1. 适用范围 covers / does_not_cover  —— 这个许可到底管什么
    2. 商用边界 commercial_use / commercial_notes —— 能不能商用、怎么商用
    3. 法源依据 basis —— 每条结论背后的条款/来源
    4. 专利/商标/链接/网络 等结构化属性 —— 供规则引擎使用

扩展方式：在 LICENSE_DB 中追加一个 LicenseInfo 即可，
compatibility 规则引擎（core.py）与命令行（cli.py）无需改动。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LicenseInfo:
    """一种许可证的结构化描述。"""

    id: str
    name: str
    category: str
    obligations: tuple[str, ...]
    course_tip: str = ""
    url: str = ""
    aliases: tuple[str, ...] = field(default=())

    # ---- v0.2：适用范围 ----
    covers: tuple[str, ...] = ()
    does_not_cover: tuple[str, ...] = ()

    # ---- v0.2：商用 ----
    commercial_use: str = "允许"              # 允许 / 有条件 / 禁止
    commercial_notes: tuple[str, ...] = ()

    # ---- v0.2：结构化属性 ----
    patent_grant: bool = False                # 是否明示授予专利许可
    trademark_license: bool = False           # 是否授予商标使用权（多数许可都不授予）
    linking_effect: str = "无"                 # 无 / 弱 / 强
    network_copyleft: bool = False            # 是否对网络服务触发开源义务（AGPL）
    source_obligation: str = "无"              # 源码提供义务

    # ---- v0.2：法源与资质 ----
    basis: tuple[str, ...] = ()
    osi_approved: bool = True
    fsf_free: bool = True

    @property
    def is_permissive(self) -> bool:
        return self.category.startswith("宽松")

    @property
    def is_strong_copyleft(self) -> bool:
        return self.category == "强传染"

    @property
    def is_weak_copyleft(self) -> bool:
        return self.category == "弱传染"

    @property
    def is_noncommercial(self) -> bool:
        return self.commercial_use == "禁止"

    @property
    def commercially_usable(self) -> bool:
        return self.commercial_use in ("允许", "有条件")


LICENSE_DB: dict[str, LicenseInfo] = {
    "MIT": LicenseInfo(
        id="MIT",
        name="MIT License",
        category="宽松",
        obligations=(
            "保留版权声明与许可声明（复制别人代码时不得删除）",
            "在仓库根目录提供完整 LICENSE 文本",
        ),
        course_tip="工具 / 作业首选之一",
        url="https://choosealicense.com/licenses/mit/",
        aliases=("MIT License", "Expat", "MIT/X11", "X11"),
        covers=(
            "源代码：复制、修改、合并、发布、再许可",
            "文档与说明文件（作为软件的一部分）",
            "再分发：源码形式或二进制形式均可",
            "商业使用：可闭源、可收费",
        ),
        does_not_cover=(
            "专利：未明示授予专利许可（专利风险需自行评估）",
            "商标：不授予商标使用权",
            "担保：明确免责（AS IS）",
            "使用者的行为：许可只约束软件本身",
        ),
        commercial_use="允许",
        commercial_notes=(
            "可闭源商用：可以销售、嵌入商业产品、SaaS 化",
            "唯一硬要求：保留版权声明与许可声明",
            "没有专利授权条款，这是 MIT 与 Apache-2.0 的关键差别",
        ),
        patent_grant=False,
        trademark_license=False,
        linking_effect="无",
        source_obligation="无",
        basis=(
            "MIT 原文：'The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.'",
            "OSI 认证、FSF 认定为自由软件许可证",
            "choosealicense.com：MIT 是最简短的宽松许可",
        ),
    ),
    "Apache-2.0": LicenseInfo(
        id="Apache-2.0",
        name="Apache License 2.0",
        category="宽松+专利",
        obligations=(
            "保留版权与许可声明",
            "随分发提供 NOTICE 文件（若上游提供）",
            "标明被修改过的文件",
            "专利授权：使用者自动获得贡献者的专利许可",
            "不得使用 Apache 商标进行背书宣传",
        ),
        course_tip="框架类更稳妥",
        url="https://choosealicense.com/licenses/apache-2.0/",
        aliases=("Apache 2.0", "Apache License, Version 2.0", "Apache-2", "Apache License 2.0"),
        covers=(
            "源代码：复制、修改、再分发",
            "专利：§2 明示授予贡献者专利许可",
            "商标以外的全部著作权权利",
            "商业使用：可闭源、可收费",
        ),
        does_not_cover=(
            "商标：§6 明确不授予商标权",
            "担保：§7 免责",
            "专利诉讼：若你指控对方专利侵权，§3 终止对你的专利授权",
        ),
        commercial_use="允许",
        commercial_notes=(
            "可闭源商用",
            "必须保留 NOTICE（若上游提供）并标明修改过的文件",
            "明示专利授权，适合框架/中间件类项目",
            "不得使用 Apache 名称或商标做背书",
        ),
        patent_grant=True,
        trademark_license=False,
        linking_effect="无",
        source_obligation="无",
        basis=(
            "Apache-2.0 §2：版权与专利授权",
            "§3：专利诉讼导致专利授权终止",
            "§4：再分发须保留 LICENSE 与 NOTICE，并标明修改",
            "§6：不授予商标权",
            "§7：免责条款",
        ),
    ),
    "BSD-3-Clause": LicenseInfo(
        id="BSD-3-Clause",
        name="BSD 3-Clause License",
        category="宽松",
        obligations=(
            "保留版权声明与许可声明",
            "二进制形式再分发时同样保留声明",
            "禁止背书：不得用原作者名称为衍生品做宣传",
        ),
        course_tip="与 MIT 相近场景",
        url="https://choosealicense.com/licenses/bsd-3-clause/",
        aliases=("BSD-3", "BSD 3-Clause", "BSD3", "New BSD", "Modified BSD"),
        covers=(
            "源代码：复制、修改、再分发",
            "二进制再分发",
            "商业使用：可闭源、可收费",
        ),
        does_not_cover=(
            "专利：未明示授予专利许可",
            "商标：不授予商标使用权",
            "担保：免责",
        ),
        commercial_use="允许",
        commercial_notes=(
            "可闭源商用",
            "保留版权与许可声明",
            "第 3 条禁止用作者名称为衍生品背书",
        ),
        patent_grant=False,
        trademark_license=False,
        linking_effect="无",
        source_obligation="无",
        basis=(
            "BSD-3-Clause 第 1 条：保留版权声明与许可声明",
            "第 2 条：二进制再分发须复制声明",
            "第 3 条：未经书面许可不得用作者名背书",
        ),
    ),
    "GPL-3.0": LicenseInfo(
        id="GPL-3.0",
        name="GNU General Public License v3.0",
        category="强传染",
        obligations=(
            "衍生作品必须同样以 GPL 开源",
            "对外分发二进制时必须提供完整对应源码",
            "修改记录与版权声明需保留",
            "与 GPL-2.0-only 不兼容（与 GPL-3.0 兼容）",
        ),
        course_tip="慎选，先懂传染性",
        url="https://choosealicense.com/licenses/gpl-3.0/",
        aliases=("GPL-3", "GPLv3", "GNU GPL v3", "GPL3", "GNU General Public License v3"),
        covers=(
            "源代码：复制、修改、分发",
            "衍生作品：修改、链接、合并后形成的整体作品",
            "对外分发：源码与二进制",
            "专利：§11 明示授予专利许可",
        ),
        does_not_cover=(
            "商标：§7 不授予商标权",
            "担保：§15-17 免责",
            "内部使用：未对外分发时通常不触发源码义务",
            "网络服务：GPL-3.0 不要求向网络用户提供源码（AGPL 才要求）",
        ),
        commercial_use="允许",
        commercial_notes=(
            "可以收费：GPL 不禁止卖钱，允许销售软件、服务或技术支持",
            "但对外分发时必须提供完整对应源码，衍生作品必须以 GPL 授权",
            "不能把 GPL 代码链接进闭源产品后对外分发",
            "SaaS 场景：纯 GPL-3.0 不要求向网络用户提供源码",
        ),
        patent_grant=True,
        trademark_license=False,
        linking_effect="强",
        network_copyleft=False,
        source_obligation="对外分发时必须提供完整对应源码（§6）",
        basis=(
            "GPL-3.0 §5：向下游传递授权，衍生作品必须同样以 GPL 发布",
            "§6：分发目标代码时须提供对应源码",
            "§7：不授予商标权",
            "§11：专利授权",
            "FSF 兼容性列表：GPL-3.0 与 MIT / BSD-3 / Apache-2.0 兼容，与 GPL-2.0-only 不兼容",
        ),
    ),
    "LGPL-3.0": LicenseInfo(
        id="LGPL-3.0",
        name="GNU Lesser General Public License v3.0",
        category="弱传染",
        obligations=(
            "动态链接（import / 独立进程调用）时，你的项目可以闭源",
            "静态链接或修改库源码时，你的项目需以 LGPL / GPL 开源",
            "必须允许使用者替换该库（提供重新链接方式）",
        ),
        course_tip="库作者可考虑",
        url="https://choosealicense.com/licenses/lgpl-3.0/",
        aliases=("LGPL-3", "LGPLv3", "GNU LGPL v3", "LGPL3"),
        covers=(
            "库本身：修改后的库仍须以 LGPL 开源",
            "以库形式被链接的作品（区分动态 / 静态链接）",
            "专利：随 GPL-3.0 §11 一并授权",
        ),
        does_not_cover=(
            "商标：不授予商标权",
            "担保：免责",
            "与库无关的独立程序（动态链接时通常不传染）",
        ),
        commercial_use="有条件",
        commercial_notes=(
            "可以商用且保持闭源，前提是动态链接 + 允许使用者替换该库",
            "静态链接时，须提供目标文件等重链接手段，或以 LGPL/GPL 开源你的程序",
            "修改库本身时，修改部分必须以 LGPL 开源",
        ),
        patent_grant=True,
        trademark_license=False,
        linking_effect="弱",
        network_copyleft=False,
        source_obligation="修改库本身或静态链接时，须提供相应源码 / 重链接方式",
        basis=(
            "LGPL-3.0 §4：组合作品的处理（动态链接不传染；静态链接须提供重链接方式）",
            "§5：修改版库须以 LGPL 开源",
            "§11：引用 GPL-3.0 的专利授权条款",
        ),
    ),
}

#: 可选扩展许可：用于演示「知识库可扩展」，并覆盖真实场景中的非商业/源码可用许可。
OPTIONAL_LICENSES: dict[str, LicenseInfo] = {
    "ISC": LicenseInfo(
        id="ISC",
        name="ISC License",
        category="宽松",
        obligations=("保留版权声明与许可声明",),
        course_tip="MIT 的等价简化版",
        url="https://choosealicense.com/licenses/isc/",
        covers=("源代码：复制、修改、分发", "商业使用：可闭源、可收费"),
        does_not_cover=("专利：无明示授权", "商标：不授予", "担保：免责"),
        commercial_use="允许",
        commercial_notes=("可闭源商用", "只需保留版权与许可声明"),
        basis=("ISC 原文：保留版权声明与许可声明，软件按原样提供",),
    ),
    "MPL-2.0": LicenseInfo(
        id="MPL-2.0",
        name="Mozilla Public License 2.0",
        category="弱传染",
        obligations=(
            "被 MPL 覆盖的文件若有修改，需以 MPL 公开该文件源码",
            "整体作品可以为其他许可（文件级传染）",
        ),
        course_tip="文件级弱传染",
        url="https://choosealicense.com/licenses/mpl-2.0/",
        covers=("被 MPL 覆盖的文件（文件级）", "专利：§2.1 明示授权", "商业使用：可闭源"),
        does_not_cover=("商标：§2.3 不授予", "担保：免责", "其他文件：可保持原有许可"),
        commercial_use="允许",
        commercial_notes=(
            "可以商用；传染范围是文件级，不是整个项目",
            "修改过的 MPL 文件必须以 MPL 公开",
        ),
        patent_grant=True,
        linking_effect="弱",
        source_obligation="修改过的 MPL 文件须公开源码",
        basis=("MPL-2.0 §2.1：专利授权", "§2.3：不授予商标权", "§3.3：文件级传染（Exhibit B）"),
    ),
    "AGPL-3.0": LicenseInfo(
        id="AGPL-3.0",
        name="GNU Affero General Public License v3.0",
        category="强传染",
        obligations=(
            "衍生作品同样开源",
            "通过网络提供服务时，也必须向用户提供源码（GPL-3.0 无此条）",
        ),
        course_tip="最严，慎选",
        url="https://choosealicense.com/licenses/agpl-3.0/",
        covers=(
            "源代码与衍生作品",
            "网络服务：通过 HTTP/API 提供服务也触发源码义务",
            "专利：§11 明示授权",
        ),
        does_not_cover=("商标：不授予", "担保：免责"),
        commercial_use="允许",
        commercial_notes=(
            "可以商用、可以收费",
            "但如果把它做成 SaaS，必须向网络用户提供完整源码",
            "闭源 SaaS 场景基本不可行",
        ),
        patent_grant=True,
        linking_effect="强",
        network_copyleft=True,
        source_obligation="对外分发或提供网络服务时，须提供完整对应源码（§13）",
        basis=("AGPL-3.0 §13：远程网络交互时的源码提供义务", "§5/§6：与 GPL-3.0 相同的传递授权与源码义务", "§11：专利授权"),
    ),
    "Unlicense": LicenseInfo(
        id="Unlicense",
        name="The Unlicense",
        category="宽松",
        obligations=("无实质义务（放弃版权，等同公共领域）",),
        course_tip="完全不想管版权时使用",
        url="https://choosealicense.com/licenses/unlicense/",
        covers=("源代码：任意使用", "商业使用：允许"),
        does_not_cover=("专利：未明示授权", "商标：不授予", "担保：免责"),
        commercial_use="允许",
        commercial_notes=("可自由商用", "无署名义务（但建议保留出处）"),
        basis=("Unlicense 原文：放弃著作权，软件按原样提供",),
    ),
    # ---------------- 以下为「不可商用 / 商用受限」的典型，用于对照 ----------------
    "CC-BY-NC-4.0": LicenseInfo(
        id="CC-BY-NC-4.0",
        name="Creative Commons Attribution-NonCommercial 4.0",
        category="非商业",
        obligations=("署名（BY）", "不得用于商业目的（NC）", "修改需注明"),
        course_tip="文档/作品可用，软件项目不要选",
        url="https://creativecommons.org/licenses/by-nc/4.0/",
        aliases=("CC BY-NC 4.0", "CC-BY-NC", "知识共享 非商业"),
        covers=("文档、图片、课程作品", "非商业性复制与改编"),
        does_not_cover=("商业使用", "软件专利授权", "商标"),
        commercial_use="禁止",
        commercial_notes=(
            "不能用于商业目的（包括公司内部营利业务、收费产品、付费服务）",
            "不是 OSI 认可的开源许可证，也不适用于软件代码",
        ),
        patent_grant=False,
        trademark_license=False,
        osi_approved=False,
        fsf_free=False,
        basis=("CC BY-NC 4.0 §2(a)(1)：仅授予非商业性使用", "Creative Commons 官方 FAQ：NC 的定义"),
    ),
    "PolyForm-Noncommercial-1.0.0": LicenseInfo(
        id="PolyForm-Noncommercial-1.0.0",
        name="PolyForm Noncommercial License 1.0.0",
        category="非商业",
        obligations=("仅限非商业目的使用", "保留许可声明"),
        course_tip="商业产品绝对不要用",
        url="https://polyformproject.org/licenses/noncommercial/1.0.0/",
        aliases=("PolyForm Noncommercial", "PolyForm-NC"),
        covers=("非商业性使用与修改",),
        does_not_cover=("任何商业用途", "专利授权", "商标"),
        commercial_use="禁止",
        commercial_notes=(
            "任何商业用途都不允许",
            "公司内部用于营利业务通常也属于商业用途",
        ),
        osi_approved=False,
        fsf_free=False,
        basis=("PolyForm Noncommercial 1.0.0 第 1 条：非商业目的定义",),
    ),
    "BUSL-1.1": LicenseInfo(
        id="BUSL-1.1",
        name="Business Source License 1.1",
        category="源码可用（商用受限）",
        obligations=(
            "生产环境使用受限（通常限制为开发/测试/非生产）",
            "达到 Change Date 后自动转为指定开源许可",
            "保留许可声明",
        ),
        course_tip="不是开源许可，商用前必须看清 Change Date",
        url="https://mariadb.com/bsl11/",
        aliases=("BSL-1.1", "Business Source License"),
        covers=("源代码公开可见", "非生产环境使用", "Change Date 后转为开源许可"),
        does_not_cover=("无限制的商业生产使用", "OSI 开源定义下的自由使用"),
        commercial_use="有条件",
        commercial_notes=(
            "生产环境商用受限制，通常需要购买商业授权",
            "Change Date 之后按约定的开源许可（如 Apache-2.0）开放",
            "它**不是** OSI 认可的开源许可证",
        ),
        osi_approved=False,
        fsf_free=False,
        basis=("BUSL-1.1 第 2 条：授予的权利范围", "第 4 条：Change Date 与 Change License", "MariaDB 官方 FAQ"),
    ),
}
