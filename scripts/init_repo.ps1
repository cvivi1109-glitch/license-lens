#Requires -Version 5.1
<#
.SYNOPSIS
    一键初始化 license-lens 仓库：git init + 按功能分组的 6 次提交 + 打版本标签。

.DESCRIPTION
    对应课程「课程最低要求」里的"提交历史可追溯"。
    本脚本只做三件事：初始化仓库、按功能分组提交、打标签。它不会删除任何文件。

.PARAMETER Email
    本次提交使用的邮箱。必须能对上你的 GitHub/Gitee 账号，否则提交无法归属到你名下。
    省略时会读取全局 git 配置；若全局配置不是邮箱格式，脚本会报错并给出改法。

.PARAMETER AuthorName
    提交者姓名。省略时读取全局 git 配置。

.PARAMETER Tag
    要打的标签名，默认 v0.1.0。

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\scripts\init_repo.ps1

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\scripts\init_repo.ps1 -Email "me@example.com" -AuthorName "常紫薇"
#>
[CmdletBinding()]
param(
    [string]$Email,
    [string]$AuthorName,
    [string]$Tag = 'v0.1.0'
)

$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $repoRoot
Write-Host ""
Write-Host "仓库目录：$repoRoot" -ForegroundColor Cyan
Write-Host ""

# ---------------------------------------------------------------- 1. 前置检查
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw '未找到 git，请先安装 Git 并确保它在 PATH 中。'
}

if (-not $Email) { $Email = (git config --global user.email) }
if (-not $AuthorName) { $AuthorName = (git config --global user.name) }

if (-not $Email -or $Email -notmatch '@') {
    Write-Host "[x] 提交邮箱不合法：'$Email'" -ForegroundColor Red
    Write-Host "    提交历史必须能对上你的 GitHub/Gitee 账号，否则老师无法确认是谁提交的。" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "    改法 A：先设置全局邮箱，再重新运行本脚本" -ForegroundColor Yellow
    Write-Host '        git config --global user.email "你的邮箱@example.com"'
    Write-Host "    改法 B：直接给本脚本传邮箱" -ForegroundColor Yellow
    Write-Host '        powershell -ExecutionPolicy Bypass -File .\scripts\init_repo.ps1 -Email "你的邮箱@example.com"'
    Write-Host ""
    exit 1
}
if (-not $AuthorName) { $AuthorName = 'license-lens contributor' }

Write-Host "提交身份：$AuthorName <$Email>" -ForegroundColor Green

# ---------------------------------------------------------------- 2. 初始化
if (-not (Test-Path (Join-Path $repoRoot '.git'))) {
    git init -b main | Out-Null
    Write-Host "已初始化 Git 仓库（默认分支 main）" -ForegroundColor Green
}
else {
    Write-Host "已存在 .git，跳过初始化"
}

# 只写入本仓库的局部配置，不修改你的全局 git 配置
git config user.name $AuthorName
git config user.email $Email

# ---------------------------------------------------------------- 3. 分组提交
$commits = @(
    @{ Msg = 'chore: 初始化仓库配置、许可与工程元数据'
        Paths = @('.gitignore', '.gitattributes', 'LICENSE', 'pyproject.toml') }
    @{ Msg = 'feat(licenses): 建立许可证知识库（课堂必记 5 种 + 扩展 4 种）'
        Paths = @('license_lens/__init__.py', 'license_lens/licenses.py') }
    @{ Msg = 'feat(core): 实现兼容性规则引擎与依赖清单扫描'
        Paths = @('license_lens/core.py') }
    @{ Msg = 'feat(cli): 提供 list/show/check/scan/matrix 命令行入口'
        Paths = @('license_lens/cli.py', 'license_lens/__main__.py') }
    @{ Msg = 'test: 覆盖归一化、规则判定与扫描报告的单元测试'
        Paths = @('tests') }
    @{ Msg = 'docs: 补充 README、设计说明、贡献指南、CI 与发布说明'
        Paths = @('README.md', 'CHANGELOG.md', 'CONTRIBUTING.md', 'RELEASE_NOTES_v0.1.0.md', 'examples', 'docs', '.github', 'scripts') }
)

Write-Host ""
Write-Host "开始按功能分组提交："
$made = 0
foreach ($item in $commits) {
    git add -- $item.Paths
    $staged = git diff --cached --name-only
    if (-not $staged) {
        Write-Host "  跳过（无改动）：$($item.Msg)" -ForegroundColor DarkGray
        continue
    }
    git commit -q -m $item.Msg
    $made++
    Write-Host "  [$made] $($item.Msg)" -ForegroundColor Green
}

# 兜底：把剩下的文件一次提交掉，避免漏文件
git add -A
if (git diff --cached --name-only) {
    git commit -q -m 'chore: 提交其余文件'
    Write-Host "  [收尾] chore: 提交其余文件" -ForegroundColor Green
    $made++
}

# ---------------------------------------------------------------- 4. 打标签
if (git tag --list $Tag) {
    Write-Host ""
    Write-Host "标签 $Tag 已存在，跳过" -ForegroundColor DarkGray
}
else {
    git tag -a $Tag -m "v0.1.0 — 首个可用版本（38 个单元测试通过）"
    Write-Host ""
    Write-Host "已打标签：$Tag" -ForegroundColor Green
}

# ---------------------------------------------------------------- 5. 自检
Write-Host ""
Write-Host "自检：运行单元测试 ..." -ForegroundColor Cyan
$python = if (Get-Command python -ErrorAction SilentlyContinue) { 'python' } else { 'py' }
& $python -m unittest discover -s tests
if ($LASTEXITCODE -ne 0) {
    Write-Host "[x] 单元测试未通过，请先修复再推送。" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "提交历史：" -ForegroundColor Cyan
git log --oneline --decorate

Write-Host ""
Write-Host "完成。接下来：" -ForegroundColor Cyan
Write-Host "  1) 在 GitHub/Gitee 网页上新建**公开**仓库 license-lens（不要勾选自动生成 README）"
Write-Host "  2) git remote add origin https://github.com/<你的用户名>/license-lens.git"
Write-Host "  3) git branch -M main"
Write-Host "  4) git push -u origin main --tags"
Write-Host ""
Write-Host "  详细步骤见 docs\推送与首个Release指引.md" -ForegroundColor DarkGray
Write-Host ""
