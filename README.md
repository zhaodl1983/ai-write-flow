# ai-write-flow

![version](https://img.shields.io/badge/version-v0.4.2-blue)

技术博客写作 Agent Skill，适用于公众号长文、AI 工具评测、教程指南，以及公众号贴图 / 小红书图卡等场景。

支持两种输出模式：
- **longform_article**：从选题讨论、调研核查、骨架确认到正文撰写和三遍审校的完整 6 步写作流程，也支持对已有文章一键审校降 AI 味
- **card_post**：事实核查 + 卡片数量决策 + 可直接复制到图卡生成系统的结构化图卡文案

可选扩展：
- **章节 SVG 配图**：基于 `##` 章节语义生成配图规划，确认后调用 svg-architect 逐张生成 SVG 并插入文章

符合 [Agent Skills 开放标准](https://agentskills.io/specification)，支持 Hermes、Claude Code、Codex，以及通过 `--tool custom --skills-dir` 接入任意 Agent 工具。

---

## 输出模式

| 模式 | 用途 | 输出形态 |
|------|------|---------|
| `longform_article` | 公众号长文 / 技术博客 / 教程 / 深度评测 | 标准 Markdown 长文（.md） |
| `card_post` | 公众号贴图 / 小红书图卡 / 图卡生成系统文案 | 结构化卡片文案（.txt），可直接复制 |

Skill 在启动时（Step 0）自动识别用户意图，路由到对应模式：

- 用户提到「图卡 / 贴图 / 卡片 / 小红书 / 1000 字以内」→ `card_post`
- 其他情况 → `longform_article`
- 用户传入已有文章要求审校 → 审校快捷入口（跳过模式路由）

---

## 文章结构约定

ai-write-flow 输出的文章遵循固定的三层标题结构：

```
# 文章标题（全文唯一）

开头段落（此处不允许出现 ####）

## 一级章节标题

#### ① 扫读小标题
#### ② 扫读小标题
#### ③ 扫读小标题

正文段落...

## 另一个章节

#### ① 扫读小标题
#### ② 扫读小标题

正文段落...

## 写在最后

结尾段落（不要求 ####）
```

**关键规则：**

- `##` 是**章节配图的候选单位**——不是每段配一张图，也不是每个 `####` 配图，而是以整个 `##` 章节块（标题 + 小标题组 + 正文摘要）作为语义输入
- `## 写在最后` 是固定结尾标题，不参与章节配图候选
- 禁止使用 `###` 层级；层级链只有 `#` → `##` → `####`
- 每个普通 `##` 内的 `####` 从 `①` 开始编号，按章节独立重置

---

## 这个 Skill 解决什么问题

- 每次写文章都要手动加载多个规则文件，启动成本高
- 调研来源质量参差不齐，没有系统化的核查流程
- 用户素材（截图、PDF）被当作最终事实，导致文章与官方描述出入
- 写完稿子不知道从哪里开始降 AI 味，缺少操作性清单
- 个人写作风格配置零散，换工具就丢失

---

## 快速安装

```bash
git clone https://github.com/zhaodl1983/ai-write-flow.git
cd ai-write-flow

# Hermes
bash scripts/install.sh --tool hermes --workspace ~/Documents/workspace/ai-write-flow

# Claude Code
bash scripts/install.sh --tool claude-code --workspace ~/Documents/workspace/ai-write-flow

# Codex
bash scripts/install.sh --tool codex --workspace ~/Documents/workspace/ai-write-flow

# 自定义 Agent Skills 目录
bash scripts/install.sh --tool custom --skills-dir ~/.your-agent/skills --workspace ~/Documents/workspace/ai-write-flow

# 交互式向导（不传参数）
bash scripts/install.sh
```

安装向导支持 Hermes / Claude Code / Codex / Custom 四种目标，以及 `--tool auto` 自动检测已安装工具。

> **workspace 路径说明**：workspace 与 Skill 安装目录是两回事——安装脚本只复制 `skill/` 内容，workspace 独立存放 briefs（输入素材）、research JSON 和成品文章。
>
> workspace 解析优先级：**`--workspace` 参数 > 环境变量 `AI_WRITE_FLOW_WORKSPACE` > 交互询问**
>
> ```bash
> export AI_WRITE_FLOW_WORKSPACE=/your/workspace/path
> ```

---

## 仓库结构

```
ai-write-flow/
├── skill/                    # Skill 安装包（唯一可分发内容）
│   ├── SKILL.md              # 主入口：Step 0 路由 + 图卡流程 + 长文 6 步流程 + 审校入口
│   ├── references/           # 运行时规则文件（AI 按需加载）
│   │   ├── fact-policy.md       # 全局事实核验输出门禁（两种模式共享）
│   │   ├── research-config.md   # 调研行为规范（Layer 1-4 + 时效门禁 + card_post 补充）
│   │   ├── card-post-config.md  # 图卡模式：字数/卡片数/输出格式/事实规则
│   │   ├── illustration-config.md  # 章节 SVG 配图扩展：语义分类/风格映射/配图流程
│   │   ├── style-guide.md       # 写作风格硬约束（禁用词、句长、结构）
│   │   ├── checklist.md         # 三遍审校清单（含图卡模式审校）
│   │   ├── persona.md           # 作者画像（可个人定制）
│   │   └── workspace-config.md  # 工作区路径与安全规则（回退配置；workspace-local.md 由 install.sh 生成，不进入源码包）
│   ├── assets/
│   │   └── brief-template.md    # 写作素材简报模板
│   └── scripts/              # 质量校验脚本
│       ├── validate_research.py      # 校验调研 JSON schema 与时效
│       ├── check_article.py          # 校验成品文章风格与结构
│       ├── check_card_post.py        # 校验图卡文案（字数/卡片数/要点/高风险词）
│       └── check_illustration_plan.py  # 校验配图计划 JSON（生成 SVG 前运行）
├── workspace/                # 本地运行时目录（不提交 Git）
│   ├── briefs/               # INPUT：写作素材（PDF、MD、截图等）
│   ├── research/             # OUTPUT：调研 JSON
│   ├── output/               # OUTPUT：成品文章 .md + 图卡文案 .txt
│   └── images/               # OUTPUT：章节 SVG 配图（可选）
├── evals/                    # 评估测试（不进入安装副本）
│   ├── evals.json            # 场景用例定义（含 card_post + illustration 场景）
│   ├── run_evals.py          # 可执行质量门禁
│   └── files/                # 测试素材文件
├── docs/                     # 设计决策文档
├── scripts/
│   ├── install.sh            # 安装向导
│   └── package-skill.sh      # 打包为可分发 zip
├── README.md
└── LICENSE
```

> **安装目录**（如 `~/.claude/skills/ai-write-flow/`）和 **workspace** 是两回事。安装脚本只复制 `skill/` 内容，workspace 独立存在于你自己的路径下，运行产物不进入 Skill 目录。

---

## 用户可定制文件

安装后，按需调整安装目录里的副本（如 `~/.hermes/skills/ai-write-flow/references/` 或 `~/.claude/skills/ai-write-flow/references/`）：

| 文件 | 说明 | 建议 |
|------|------|------|
| `persona.md` | 写作身份、目标读者、发布平台、语气偏好 | 建议改 |
| `workspace-config.md` | 工作区路径与安全规则（回退配置，`workspace-local.md` 不存在时使用）| 开源用户改 |

> `persona.md` 是软配置，`style-guide.md` 中的硬约束优先级更高，冲突时以 `style-guide.md` 为准。

---

## 触发方式

### 完整写作流程（longform_article，6 步）

```
帮我写一篇关于 Claude Code 的 MCP 工具开发的文章
```

Skill 自动执行：解析工作区 → 检查 briefs → 调研核查 → 选题确认 → 两阶段创作 → 三遍审校 → 落盘输出。

### 审校快捷入口（降 AI 味）

将已有文章粘贴进对话：

```
帮我审校这篇文章，降低 AI 味
```

跳过 Steps 0-4，直接进入三遍审校（内容 → 风格 → 细节）。

### 图卡文案（card_post）

```
帮我给 Hermes Agent v0.16 出一套图卡，可以复制到图卡生成系统，不超过 1000 字
```

```
帮我做一套小红书图卡，介绍这个工具的 3 个核心功能
```

Skill 自动执行：调研核查（事实核查摘要）→ 卡片数量决策 → 生成可直接复制的图卡文案 → 落盘输出（.txt）。

### 章节 SVG 配图（可选扩展）

```
给这篇文章按章节生成 SVG 配图，先给我配图大纲，确认后再生成
```

流程：
1. 解析文章 `##` 章节，排除开头段落和 `## 写在最后`
2. 提取每章核心观点和关键词，判断图表类型（流程图 / 对比图 / 分层架构图 / 概念图等）
3. 输出【章节配图规划】表格，等待用户确认
4. 确认后调用 svg-architect 逐张生成 `wechat_article` SVG（1200×500）
5. 将图片引用插入文章对应章节（`####` 小标题组之后）

---

## 工作流概览

### longform_article 模式

| Step | 名称 | 核心行为 | 阻断条件 |
|------|------|---------|---------|
| Step 0 | 输出模式路由 | 识别用户意图，路由到 longform_article | 无 |
| Step 1 | 工作区 & 素材检查 | 解析 workspace → 加载 briefs，生成材料清单 | 无法解析 workspace |
| Step 2 | 调研 | briefs 有内容用三段式核查；无内容跑全量 Layer 1-4 | 质量检查不通过 / 发现差异 |
| Step 3 | 选题讨论 | 生成 3-4 个方向，含工作量 / 测试需求 | 用户未确认选题 |
| Step 4 | 两阶段创作 | 骨架确认 → 正文填充（加载 fact-policy.md 输出门禁）| 骨架未获用户确认 |
| Step 5 | 三遍审校 | 内容 → 风格（降 AI 味）→ 细节 | 无 |
| Step 6 | 落盘输出 | 保存到 `workspace/output/{date}-{slug}.md` | 文件写入失败 |

### card_post 模式

| Step | 名称 | 核心行为 | 阻断条件 |
|------|------|---------|---------|
| Step 0 | 输出模式路由 | 识别图卡意图，加载 card-post-config.md + fact-policy.md | 无 |
| Step 1 | 工作区 & 素材检查 | 同 longform_article | 无法解析 workspace |
| Step 2 | 调研与核查 | 同 longform_article + 输出 card_safe_claims / excluded_claims | 质量检查不通过 / 发现差异 |
| Step 3 | 卡片草稿 | 卡片数量决策 → 用户确认 → 生成图卡文案 | 用户未确认卡片数量 |
| Step 4 | 落盘输出 | 保存到 `workspace/output/{date}-card-{slug}.txt` | 文件写入失败 |

### Step 2 调研核查机制

| 模式 | 触发条件 | 行为 |
|------|---------|------|
| `brief_first_verify_mode` | briefs/ 有内容 | Stage A 提取候选事实 → Stage B 定点核查高风险字段 → Stage C 差异报告（有差异则阻断） |
| `publish_mode` | briefs/ 为空 | Layer 1-4 全量调研，30 天时效门禁，任一 claim 不达标则阻断 |

---

## 校验脚本

```bash
# 校验调研 JSON（schema 完整性 + 时效门禁）
python3 skill/scripts/validate_research.py workspace/research/YYYYMMDD-topic.json

# 校验成品文章（禁用词 + 长句 + 结构完整性）
python3 skill/scripts/check_article.py workspace/output/YYYYMMDD-title.md

# 校验图卡文案（字数 + 卡片数 + 要点数 + 高风险词 + 必要区块）
python3 skill/scripts/check_card_post.py workspace/output/YYYYMMDD-card-topic.txt

# 运行 eval 质量门禁
python3 evals/run_evals.py
```

---

## 安全提示

- 不要把 `briefs/` 中的敏感素材或 API Key 提交到 Git（`.gitignore` 已覆盖 workspace/ 运行时内容）
- 不要把 workspace 路径硬编码在 Skill 安装文件里
- 配图 API Key 只读取环境变量，不写入任何文件

---

## 许可证

MIT
