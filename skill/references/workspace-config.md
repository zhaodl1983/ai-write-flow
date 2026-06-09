# workspace-config.md

## Workspace Resolution

Resolve the runtime workspace at the start of every session using this priority order:

1. If the user explicitly provides a workspace path in this conversation → use that path
2. If the environment variable `AI_WRITE_FLOW_WORKSPACE` is set → use that path
3. If `~/Documents/workspace/ai-write-flow` exists on disk → use it (convention default)
4. Otherwise → ask the user where to create the workspace before proceeding

Do not write any runtime files into the installed Skill directory.

## Runtime Directories

| Directory | Purpose |
|-----------|---------|
| `briefs/` | Input materials. Accept PDFs, Markdown, text files, screenshots, DOCX, spreadsheets, JSON, and web excerpts. |
| `research/` | Research JSON outputs from Step 2. |
| `output/` | Final Markdown article outputs from Step 6. |
| `images/` | Generated article images (optional extension). |

## Multi-Format Brief Handling

For each file found in `briefs/`, generate a material entry:

- **文件名**：原始文件名
- **类型**：PDF / Markdown / TXT / DOCX / 图片 / 表格 / JSON / 其他
- **读取状态**：成功 / 失败
- **提取摘要**：主要内容要点（100字以内）
- **可信度备注**：来源性质（用户原创素材、截图、第三方文章等）

Files that cannot be parsed must appear in an "未解析文件清单" — never silently skip them.

## Safety Rules

- Never delete or overwrite files in `briefs/`.
- Before overwriting a file in `research/`, `output/`, or `images/`, generate a unique filename (append timestamp) or ask the user for confirmation.
- Never hardcode API keys or credentials in any output file.
