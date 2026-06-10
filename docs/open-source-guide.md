# open-source-guide.md — 开源分发说明

## 仓库结构

```
ai-write-flow/
├── skill/          # Skill 安装包（可分发内容）
├── workspace/      # 本地运行时目录（不提交）
├── docs/           # 设计文档（不进入安装副本）
├── evals/          # 评估测试（不进入安装副本）
├── scripts/        # 安装与打包脚本
├── README.md       # 面向用户的说明文档
└── LICENSE
```

## 安装

```bash
# Hermes
bash scripts/install.sh --tool hermes --workspace ~/Documents/workspace/ai-write-flow

# Claude Code
bash scripts/install.sh --tool claude-code --workspace ~/Documents/workspace/ai-write-flow

# Codex
bash scripts/install.sh --tool codex --workspace ~/Documents/workspace/ai-write-flow

# 自定义 Agent Skills 目录
bash scripts/install.sh --tool custom --skills-dir ~/.your-agent/skills --workspace ~/Documents/workspace/ai-write-flow

# 交互式向导
bash scripts/install.sh
```

安装脚本只复制 `skill/` 目录内容到目标 Agent 的 Skills 目录，不复制 workspace/、docs/、evals/。

支持的安装目标：

| 参数 | 默认目录 | 环境变量覆盖 |
|------|---------|------------|
| `--tool hermes` | `~/.hermes/skills` | `HERMES_SKILLS_DIR` |
| `--tool claude-code` | `~/.claude/skills` | `CLAUDE_SKILLS_DIR` |
| `--tool codex` | `~/.codex/skills` | `CODEX_HOME` |
| `--tool custom` | 由 `--skills-dir` 指定 | — |
| `--tool auto` | 自动检测已安装工具 | — |

## 用户可定制文件

安装后，以下文件可按个人需要调整：

| 文件 | 说明 |
|------|------|
| `references/persona.md` | 写作身份与风格偏好 |
| `references/workspace-config.md` | 工作区路径与安全规则（`workspace-local.md` 不存在时的回退配置）|
| `references/workspace-local.md` | 安装脚本自动生成，写入本机 workspace 路径；Step 1 优先读取此文件 |
| `references/image-config.md`（可选）| 配图 API 配置（默认不启用）|

## 工作区

Skill 安装目录和 workspace 是两回事：

- **Skill 安装目录**（如 `~/.hermes/skills/ai-write-flow/` 或 `~/.claude/skills/ai-write-flow/`）：存放 SKILL.md 和 references，只读
- **workspace** `/your/workspace/path/`：存放 briefs（输入素材）、research JSON、成品文章

不要把敏感素材、API Key 或个人 briefs 提交到 Git。

## 环境变量

| 变量 | 说明 |
|------|------|
| `AI_WRITE_FLOW_WORKSPACE` | 指定运行时工作区路径（开源用户推荐配置）|

## 贡献

欢迎 PR。修改 Skill 流程请同步更新 `evals/evals.json` 中的对应测试场景。
