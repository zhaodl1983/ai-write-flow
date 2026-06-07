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
bash scripts/install.sh
```

安装脚本只复制 `skill/` 目录内容到 Claude Code 的 Skills 目录，不复制 workspace/、docs/、evals/。

## 用户可定制文件

安装后，以下文件可按个人需要调整：

| 文件 | 说明 |
|------|------|
| `references/persona.md` | 写作身份与风格偏好 |
| `references/workspace-config.md` | 工作区路径与安全规则 |
| `references/image-config.md`（可选）| 配图 API 配置（默认不启用）|

## 工作区

Skill 安装目录和 workspace 是两回事：

- **Skill 安装目录** `~/.claude/skills/ai-write-flow/`：存放 SKILL.md 和 references，只读
- **workspace** `/your/workspace/path/`：存放 briefs（输入素材）、research JSON、成品文章

不要把敏感素材、API Key 或个人 briefs 提交到 Git。

## 环境变量

| 变量 | 说明 |
|------|------|
| `AI_WRITE_FLOW_WORKSPACE` | 指定运行时工作区路径（开源用户推荐配置）|

## 贡献

欢迎 PR。修改 Skill 流程请同步更新 `evals/evals.json` 中的对应测试场景。
