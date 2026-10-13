# PR 说明

## 这个 PR 做了什么

<!-- 一句话说明 -->

关联 Issue：<!-- 例如 Closes #1 -->

## 改动类型

- [ ] 新功能（feat）
- [ ] 修 Bug（fix）
- [ ] 文档（docs）
- [ ] 测试（test）
- [ ] 重构（refactor）
- [ ] 构建 / CI（chore）

## 自查清单

- [ ] `python -m unittest discover -s tests -v` 全部通过
- [ ] 新增行为有对应的测试用例
- [ ] 新增的许可证 / 规则有 docstring 说明判定依据
- [ ] README / CHANGELOG 已同步更新
- [ ] 没有提交 `__pycache__`、报告文件、IDE 配置等无关内容

## 如何验证

```bash
# 粘贴你实际执行过的命令
python -m license_lens check MIT GPL-3.0
```

## 破坏性变更

<!-- 有就写；没有写"无" -->
无
