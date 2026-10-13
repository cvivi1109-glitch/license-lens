# 推送与首个 Release 指引

本文件对应「课程最低要求」里的 **公开仓库可访问 / 有 Issue 记录问题 / 至少一次 Release / 提交历史可追溯**。

> 下面的「已完成」部分我已经在你这台电脑上实际执行并验证过了，你只需要做剩下的网页操作。

---

## 已完成（无需再做）

| 事项 | 状态 |
|------|------|
| Git 安装与身份配置 | ✅ `cvivi` / `cvivi1109@gmail.com` |
| 本地仓库初始化 | ✅ 已 `git init`，默认分支 `main` |
| 语义化提交历史 | ✅ 7 次提交（chore / feat / test / docs） |
| 版本标签 | ✅ 已打 `v0.1.0` |
| 单元测试 | ✅ 38 个用例全部通过 |
| SSH 密钥 | ✅ 已生成 `~\.ssh\id_ed25519`（指纹 `SHA256:E0+PeGOyCH3c92TT55RU3gqgYfpCyisudnztB1WD558`） |
| 远程地址 | ✅ `origin` = `git@github.com:cvivi1109-glitch/license-lens.git` |
| README 徽章与链接 | ✅ 已填入真实用户名，无需再改 |

---

## 还剩 4 步（都在网页或一条命令里）

### 第 1 步：把 SSH 公钥加到 GitHub

1. 打开 <https://github.com/settings/keys>
2. 点 **New SSH key**
3. **Title** 随便填，例如 `我的笔记本`
4. **Key type** 选 `Authentication Key`
5. **Key** 里粘贴下面这行（这是我为你生成的公钥）：

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOJ5HPJ5956YRF4flJZ4Eypl0Ciigg3aszueJAdlodHQ cvivi1109@gmail.com
```

6. 点 **Add SSH key**（可能会要求你输入 GitHub 密码确认）

> 获取公钥的另一种方式：在终端执行 `Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub`

验证是否成功（可选）：

```powershell
ssh -T git@github.com
# 成功时显示：Hi cvivi1109-glitch! You've successfully authenticated...
```

### 第 2 步：创建公开仓库

1. 打开 <https://github.com/new>
2. **Repository name**：`license-lens`
3. **Description**：`开源许可证合规扫描器：输入依赖清单，输出能否这样发布与需要履行的义务`
4. 可见性：选 **Public** ← 课程要求
5. **不要**勾选 "Add a README file"、".gitignore"、"Choose a license"（本地已经有了，勾了会冲突）
6. 点 **Create repository**

### 第 3 步：推送

```powershell
cd "D:\AAAAAAAAAAAA2026\open resource\开学准备\starter-repo"
git push -u origin main --tags
```

用的是 SSH，**不需要输密码，也不需要访问令牌**。可能出现的提示：

| 提示 | 含义 | 怎么办 |
|------|------|--------|
| `Permission denied (publickey)` | 公钥还没加到账号 | 回第 1 步 |
| `Repository not found` | GitHub 上还没建仓库 | 回第 2 步（注意仓库名大小写要一致） |
| `remote origin already exists` | 地址重复添加 | `git remote set-url origin git@github.com:cvivi1109-glitch/license-lens.git` |
| `Could not read from remote repository` | 用户名/仓库名拼错 | `git remote -v` 核对 |

成功时会看到：

```
* [new branch]      main -> main
* [new tag]         v0.1.0 -> v0.1.0
```

### 第 4 步：提 1 个真实的 Issue

**别为了凑数提 "test" 这种 Issue**，老师看得出来。下面这个就是本项目真实的待办：

1. 仓库页面 → **Issues** → **New issue** → 选 **功能建议（feature_request）**
2. 标题：`支持从 requirements.txt 自动读取依赖许可证`
3. 正文（可直接粘贴，模板会自动带出三个小标题）：

```
## 想解决的问题
现在 scan 命令要求每行手工写上 `# 许可证`，依赖一多就容易漏写，
漏写的依赖会被标为「待补全」，导致报告结论不是最终结论。

## 期望的方案
直接读取 pip 已安装元数据（importlib.metadata），
从本地已安装包的 METADATA 文件中读取 License 字段，无需联网。

## 备选方案
若自动读取失败，保留现在的手工标注方式作为回退。

## 附加信息
- 影响 v0.1.0 的 scan 命令
- 优先级：中
```

### 第 5 步：发布首个 Release

1. 仓库页面右侧 → **Releases** → **Draft a new release**
2. **Choose a tag** → 选择已有的 `v0.1.0`
3. **Release title**：`v0.1.0 — 首个可用版本`
4. **Describe this release**：把 `RELEASE_NOTES_v0.1.0.md` 的内容整段粘贴进去
5. 点 **Publish release**

---

## 验收：对着「课程最低要求」逐条勾

| 要求 | 怎么验证 | 状态 |
|------|----------|------|
| 公开仓库可访问 | 用无痕窗口打开仓库地址，不登录也能看到代码 | ⬜ |
| README 可跑通 | 按 README 的快速开始执行，能得到文档里的输出 | ⬜ |
| LICENSE 明确 | 仓库首页右侧显示 "MIT license"，根目录有 `LICENSE` | ⬜ |
| 有 Issue 记录问题 | Issues 列表至少 1 条，内容是真实待办 | ⬜ |
| 至少一次 Release | Releases 页面有 `v0.1.0` | ⬜ |
| 提交历史可追溯 | `git log --oneline` 每条提交都能对到你的头像 | ⬜ |

---

## 附：可选的高阶玩法

安装 GitHub CLI 后，建仓库、提 Issue、发 Release 都能用命令完成：

```powershell
winget install --id GitHub.cli
gh auth login
gh repo create license-lens --public --source . --remote origin --push
gh issue create --title "支持从 requirements.txt 自动读取依赖许可证"
gh release create v0.1.0 --title "v0.1.0 — 首个可用版本" --notes-file RELEASE_NOTES_v0.1.0.md
```

> 注意：`gh` 用的是 HTTPS + OAuth 令牌，和上面的 SSH 是两套独立凭证，互不影响。

### 备用方案：不想用 SSH，改用 HTTPS + 访问令牌

```powershell
git remote set-url origin https://github.com/cvivi1109-glitch/license-lens.git
git push -u origin main --tags
```

GitHub 已禁止用账号密码做 Git 操作，所以密码框里要填 **Personal Access Token**：
GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → 勾选 `repo` 权限生成。
（你当前的 `credential.helper=store` 会把令牌明文保存在 `~\.git-credentials`，安全性不如 SSH，所以推荐用 SSH。）
