# 推送与首个 Release 指引（对着做，10 分钟搞定）

本文件对应「课程最低要求」里的 **公开仓库可访问 / 有 Issue 记录问题 / 至少一次 Release / 提交历史可追溯**。

---

## 第 0 步：先确认 Git 身份正确

提交历史必须能对上你的账号，否则老师看不出"这是谁交的"。在终端执行：

```powershell
git config --global user.email    # 不能是手机号，必须是邮箱
git config --global user.name
```

如果邮箱不对：

```powershell
git config --global user.email "你的邮箱@example.com"
```

> 不想暴露真实邮箱：在 GitHub → Settings → Emails 勾选 "Keep my email addresses private"，
> 使用形如 `12345678+用户名@users.noreply.github.com` 的地址。

---

## 第 1 步：本地初始化（自动生成 6 次有意义的提交）

```powershell
cd "D:\AAAAAAAAAAAA2026\open resource\开学准备\starter-repo"
powershell -ExecutionPolicy Bypass -File .\scripts\init_repo.ps1
```

如果全局邮箱还没改好，可以临时指定：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\init_repo.ps1 -Email "你的邮箱@example.com" -AuthorName "常紫薇"
```

脚本会：检查前置条件 → `git init` → 按功能分 6 次提交 → 打上 `v0.1.0` 标签 → 跑一遍测试。

验证：

```powershell
git log --oneline --graph
git tag
```

---

## 第 2 步：在网页上创建公开仓库

1. 打开 GitHub → 右上角 `+` → **New repository**（或 Gitee → 新建仓库）。
2. 仓库名：`license-lens`
3. 描述：`开源许可证合规扫描器：输入依赖清单，输出能否这样发布与需要履行的义务`
4. 可见性：**Public（公开）** ← 课程要求
5. **不要**勾选 "Add a README file" / ".gitignore" / "license"（本地已经有了，勾了会冲突）
6. 点 **Create repository**

---

## 第 3 步：关联远程并推送

```powershell
git remote add origin https://github.com/<你的用户名>/license-lens.git
git branch -M main
git push -u origin main --tags
```

> 首次推送会弹出浏览器让你登录 GitHub，按提示授权即可。
> 推送失败提示 `remote origin already exists` 时，改用：
> `git remote set-url origin https://github.com/<你的用户名>/license-lens.git`

推送完成后，把 README 里的 `USERNAME` 全部替换成你的用户名（徽章和链接才会指对地方）：

```powershell
# 用 VS Code 全局替换最省事：Ctrl+Shift+H，搜索 USERNAME
```

然后：

```powershell
git add -A
git commit -m "docs(readme): 修正仓库链接与 CI 徽章地址"
git push
```

---

## 第 4 步：提 1 个真实的 Issue（满足"有 Issue 记录问题"）

**别为了凑数提"test"这种 Issue**，老师看得出来。下面这个就是本项目真实的待办：

1. 打开仓库页面 → **Issues** → **New issue** → 选 **功能建议（feature_request）**
2. 标题：`支持从 requirements.txt 自动读取依赖许可证`
3. 正文（可直接粘贴）：

```
## 想解决的问题
现在 scan 命令要求每行手工写上 `# 许可证`，依赖一多就容易漏写，
漏写的依赖会被标为「待补全」，导致报告结论不是最终结论。

## 期望的方案
直接读取 pip 已安装元数据（importlib.metadata）或 requirements.txt 的包名，
自动从本地已安装包的 METADATA 文件中读取 License 字段，无需联网。

## 备选方案
若自动读取失败，保留现在的手工标注方式作为回退。

## 附加信息
- 影响 v0.1.0 的 scan 命令
- 优先级：中
```

4. 提交后把 Issue 编号记下来（例如 `#1`）。

---

## 第 5 步：发布首个 Release（满足"至少一次 Release"）

1. GitHub 仓库页面右侧 → **Releases** → **Draft a new release**
2. **Choose a tag** → 选择已有的 `v0.1.0`
3. **Release title**：`v0.1.0 — 首个可用版本`
4. **Describe this release**：把 `RELEASE_NOTES_v0.1.0.md` 的内容整段粘贴进去
5. 点 **Publish release**

发布后，`CHANGELOG.md` 里的 `v0.1.0` 链接就能点开了。

---

## 第 6 步：验收（对着「课程最低要求」逐条勾）

| 要求 | 怎么验证 |
|------|----------|
| 公开仓库可访问 | 退出登录或用无痕窗口打开仓库地址，能看到代码 |
| README 可跑通 | 在别人的电脑上（或清空环境后）按 README 的快速开始执行，能出预期输出 |
| LICENSE 明确 | 仓库首页右侧显示 "MIT license"，根目录有 `LICENSE` |
| 有 Issue 记录问题 | Issues 列表至少 1 条，内容是真实待办 |
| 至少一次 Release | Releases 页面有 `v0.1.0` |
| 提交历史可追溯 | `git log --oneline` 显示 6 条语义化提交，且每条都能对到你的头像 |

---

## 附：如果还想更省事（可选）

安装 GitHub CLI 后，创建仓库、提 Issue、发 Release 都能用命令完成：

```powershell
winget install --id GitHub.cli          # 安装
gh auth login                           # 登录
gh repo create license-lens --public --source . --remote origin --push
gh issue create --title "支持从 requirements.txt 自动读取依赖许可证" --body-file .github/ISSUE_TEMPLATE/feature_request.md
gh release create v0.1.0 --title "v0.1.0 — 首个可用版本" --notes-file RELEASE_NOTES_v0.1.0.md
```

以及配置 SSH 免密推送：

```powershell
ssh-keygen -t ed25519 -C "你的邮箱@example.com"          # 一路回车
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub | Set-Clipboard   # 复制公钥
# 粘贴到 GitHub → Settings → SSH and GPG keys → New SSH key
git remote set-url origin git@github.com:<你的用户名>/license-lens.git
```
