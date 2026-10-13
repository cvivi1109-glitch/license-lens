"""开源许可证知识库。

数据来源：课堂幻灯片「常用许可证对比（课堂必记）」。

扩展方式：在 LICENSE_DB 中追加一个 LicenseInfo 即可，
compatibility 规则引擎（core.py）与命令行（cli.py）无需任何改动。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LicenseInfo:
    """一种许可证的静态描述。"""

    id: str
    name: str
    category: str
    obligations: tuple[str, ...]
    course_tip: str = ""
    url: str = ""
    aliases: tuple[str, ...] = field(default=())

    @property
    def is_permissive(self) -> bool:
        """宽松类（可闭源分发，只需保留声明）。"""
        return self.category.startswith("宽松")

    @property
    def is_strong_copyleft(self) -> bool:
        """强传染：衍生作品必须同样开源。"""
        return self.category == "强传染"

    @property
    def is_weak_copyleft(self) -> bool:
        """弱传染：仅在静态链接/修改库本身时传染。"""
        return self.category == "弱传染"


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
    ),
}

#: 用于演示「知识库可扩展」：不在课堂必记范围内，但常见于真实依赖清单。
OPTIONAL_LICENSES: dict[str, LicenseInfo] = {
    "ISC": LicenseInfo(
        id="ISC",
        name="ISC License",
        category="宽松",
        obligations=("保留版权声明与许可声明",),
        course_tip="MIT 的等价简化版",
        url="https://choosealicense.com/licenses/isc/",
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
    ),
    "Unlicense": LicenseInfo(
        id="Unlicense",
        name="The Unlicense",
        category="宽松",
        obligations=("无实质义务（放弃版权，等同公共领域）",),
        course_tip="完全不想管版权时使用",
        url="https://choosealicense.com/licenses/unlicense/",
    ),
}
