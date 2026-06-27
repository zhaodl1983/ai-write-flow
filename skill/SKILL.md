---
name: ai-write-flow
description: |
  Use this skill when the user wants to write, rewrite, polish, fact-check, outline, draft, or review Chinese technical articles, AI/tooling blog posts, 公众号长文, tutorials, or existing drafts. Use for full writing workflows from input material ingestion, research, topic selection, outline approval, drafting, and three-pass review; also use when the user asks to 降AI味, 去AI腔, 润色, 改写, 审校, or make writing more natural. Also use when the user wants to generate 图卡文案, 公众号贴图, 小红书图卡, card posts, or structured card copy for image generation systems. Also use when the user wants to generate article illustrations, section-level SVG diagrams, 章节配图, 分段配图, or insert SVG visuals into a written article.
---

# ai-write-flow — 技术博客写作工作流

## 快捷入口：审校模式

**优先级：** 高于所有 Step，包括 Step 0。检测到本意图时直接进入 Review 流程，不执行输出模式路由。

**触发意图：** 用户传入已有文章 + 表达"降AI味 / 审校 / 去掉AI腔 / 润色"等意图

**跳过步骤：** Step 0 及 Steps 1-4 全部跳过

**直接加载：** `references/fact-policy.md` + `references/style-guide.md` + `references/checklist.md` + `references/ai-flavor-patterns.md` + `references/human-voice-policy.md`

**执行流程：** 直接进入 Step 5 审校（内容 → 作者手迹保护 → AI 味检测/降噪 → 细节 → 二次扫描）

**输出结构：** 审校报告（对话窗口展示）+ 关键改动说明 + 修订后全文；若用户要求“只检查/先别改/detect/audit only”，只输出检测报告，不输出修订全文

**事实处理规则（审校模式专项）：**
- 审校模式不得新增、改写或强化高风险事实（版本号、性能数据、价格、模型名、发布时间等）
- 若原文中发现缺少来源支撑的高风险事实，在审校报告的"内容审校"栏列为「待核验事实」，不替用户补全或修改
- 文风润色不改变事实表述；如要修改数字或版本号，必须先告知用户并等待确认

---

## Step 0：输出模式路由（Output Mode Routing）

**触发条件：** 工作流启动时自动执行（审校快捷入口优先级更高，命中时跳过本步骤）

**路由规则：**

| 触发关键词 | 输出模式 | 进入流程 |
|-----------|---------|---------|
| 图卡 / 贴图 / 卡片 / 小红书 / card / 图卡生成系统 / 1000字以内的内容 | `card_post` | 加载 card-post-config.md，进入图卡流程 |
| 配图 / 章节配图 / 分段配图 / SVG 插图 / 给文章加图 | `longform_article + illustration_extension` | 加载 illustration-config.md，进入章节配图流程 |
| 以上均无 | `longform_article` | 继续 Step 1-6 长文流程 |

**illustration_extension 路由规则：**
- 用户只要求「给已有文章配图」→ 跳过 Step 1-4 写作流程，直接进入章节 SVG 配图扩展
- 用户要求「写文章并配图」→ 先完成 Step 1-6，文章稳定后再进入章节 SVG 配图扩展
- 未明确要求配图时，不主动生成配图，不打断写作流程

**card_post 模式加载文件：**

- `references/card-post-config.md`
- `references/fact-policy.md`
- `references/research-config.md`
- `references/persona.md`（语气参考）
- `references/style-guide.md`（语气参考，不强制文章结构）

---

## 图卡流程（card_post 模式）

card_post 模式共执行 4 步：Step 1（工作区检查）→ Step 2（调研与核查）→ 卡片草稿 → 落盘输出。

**Step 1 和 Step 2 与长文主流程相同**（见下方主流程章节），但 Step 2 额外执行 research-config.md 中的 `card_post 事实核查补充规则`，并在 JSON 中输出 `card_safe_claims[]` 和 `excluded_claims[]`。

---

### 图卡 Step 3：卡片草稿（Card Draft）

**触发条件：** Step 2 调研通过后执行

**加载文件：** `references/card-post-config.md`（已在 Step 0 加载）+ `references/fact-policy.md`

**行为规范：**

1. 基于 Step 2 的 `card_safe_claims[]`，决定信息单元数量，输出【卡片数量决策】
2. 等待用户确认卡片数量（可微调）
3. 用户确认后，按 card-post-config.md 的输出结构，依序输出：
   - 【事实核查摘要】
   - 【卡片数量决策】（确认版）
   - 【发布配文】
   - 【图卡内容排版】（封面图卡 + Card 01…）
4. 所有图卡要点必须可追溯到 `card_safe_claims[]` 中 `can_use_in_card: true` 的 supported claim
5. `excluded_claims[]` 中的事实禁止出现在发布内容（【发布配文】与【图卡内容排版】）

**阻断规则：** 用户未确认卡片数量决策前，不生成图卡文案

---

### 图卡 Step 4：落盘输出（Card Publish）

**触发条件：** 图卡 Step 3 完成后执行

**行为规范：**

1. 将完整输出（含事实核查摘要、卡片数量决策、发布配文、图卡内容排版）保存到：
   `{workspace}/output/{YYYYMMDD}-card-{topic-slug}.txt`
2. 文件名格式：`YYYYMMDD` 为今日日期，`topic-slug` 为主题的 kebab-case 版本
3. 落盘前运行图卡校验（必须带 `--research` 做事实追溯，缺少 research JSON 时阻断，不得落盘）：
   ```
   python3 skill/scripts/check_card_post.py \
       {workspace}/output/{YYYYMMDD}-card-{topic-slug}.txt \
       --research {workspace}/research/{YYYYMMDD}-{topic-slug}.json
   ```
   - 若退出码非零：按错误提示修订图卡内容（修改在对话窗口内完成），重新运行校验通过后再落盘
4. 输出保存路径供用户确认

**阻断规则：** 文件写入失败时报错，列出路径，请用户检查目录是否存在

---

## 主流程（longform_article 模式，6 步）

### Step 1：工作区解析 & 素材检查（Workspace & Brief Check）

**触发条件：** 工作流启动时自动执行

**加载文件：** `references/workspace-local.md`（不存在时回退到 `references/workspace-config.md`）

**行为规范：**

1. 首先检查 `references/workspace-local.md` 是否存在：
   - 若存在 → 从中读取 `workspace_path` 字段，使用该路径
   - 若不存在 → 加载 `references/workspace-config.md`，按以下优先级解析运行时工作区：
     - 若用户在本次对话中明确指定路径 → 使用该路径
     - 若环境变量 `AI_WRITE_FLOW_WORKSPACE` 已设置 → 使用该路径
     - 若 `~/Documents/workspace/ai-write-flow` 存在 → 使用该路径（约定默认路径）
     - 否则 → 询问用户工作区位置，等待回复后继续

2. 解析工作区后检查 `{workspace}/briefs/` 目录
3. 若目录为空或不存在 → 记录状态，继续执行
4. 若目录有文件 → 按多格式素材处理原则生成材料清单，继续执行

**多格式素材处理原则：**

支持文件类型：PDF、Markdown、TXT、DOCX、图片、表格、JSON、网页摘录

对每个文件生成材料清单条目：

| 字段 | 说明 |
|------|------|
| 文件名 | 原始文件名 |
| 类型 | 文件格式 |
| 读取状态 | 成功 / 失败 |
| 提取摘要 | 主要内容要点（100字以内）|
| 可信度备注 | 来源性质（用户原创素材、截图、第三方文章等）|

无法读取的文件不得跳过，必须列入"未解析文件清单"并提示用户处理方式。

**写入规则：** 运行产物（研究 JSON、成品文章、图片）只能写入 `{resolved_workspace}`，严禁写入 Skill 安装目录。

**固定输出模板（措辞不可改写）：**

```
【Step 1 工作区 & 素材检查】
工作区：{resolved workspace path}
素材状态：{无 briefs | 已加载 N 个文件}
说明：{workspace/briefs/ 目录为空，本次创作不含外部素材约束 | 已加载以下文件作为创作约束：[文件名列表]}
未解析文件：{无 | [文件名列表，请确认是否需要转写或提供文本版]}
处理：继续执行 Step 2
```

**阻断规则：** 无法解析工作区时阻断，等待用户提供路径后继续

---

### Step 2：调研（Research）

**触发条件：** Step 1 完成后执行

**加载文件：** `references/research-config.md`

**执行模式（根据 briefs/ 状态自动选择）：**
- `briefs/` 有内容 → `brief_first_verify_mode`（三段式）
- `briefs/` 为空 → `publish_mode`（全量调研，跑满 Layer 1-4）

**行为规范 A — `brief_first_verify_mode`（briefs/ 有内容时执行）**

**Stage A — Brief Ingest（提取候选事实）**
- 从 briefs/ 中提取所有候选事实，每条标记为 `Tier 1 Candidate`，**不是 Tier 1 Final**
- 重点覆盖高风险字段：产品名称、产品定位、发布主体、版本/日期、截图功能归属、价格/API 地址/兼容性

**Stage B — Targeted Verification（定点核查）**
- 仅对 Stage A 提取的高风险字段做外部核查
- 不机械跑满 Layer 1-4，只验证易变、易混淆、有多义性的候选事实
- 用 research-config.md 中的 Source Tiers 判断外部来源质量

**Stage C — Discrepancy Report（差异报告）**
- 无差异 → 候选事实升级为 `verified`，输出 JSON，继续 Step 3
- 发现差异 → 输出【差异确认】格式，**立即阻断，等待用户确认后再进入 Step 3**

差异门禁触发条件（任一满足即阻断）：
- 用户截图和公开资料表述不一致
- 产品名称相近但主体不同
- 功能演示成立，但官方定位描述不同
- 时间相关信息（版本、定价、可用性）无法确认最新性

【差异确认】固定输出格式（措辞不可改写）：

```
【差异确认】
事实项：[具体字段名]
用户素材：[简报/截图中的描述]
外部证据：[外部来源的描述，附 URL]
风险：[若直接写入正文可能导致的问题]
建议处理：
1. [处理方案 A]
2. [处理方案 B]
请用户确认后继续
```

**行为规范 B — `publish_mode`（briefs/ 为空时执行）**

- 判断 topic_type，执行 research-config.md 中的 Layer 1-4 完整调研流程
- 所有 claim 须有 Tier 1/2 来源支撑，30 天时效门禁严格执行
- 输出 JSON 结构到 `{workspace}/research/{YYYYMMDD}-{topic-slug}.json`

**JSON 输出（两种模式均适用）：** 路径 `{workspace}/research/{YYYYMMDD}-{topic-slug}.json`，候选事实单独列入 `tier_1_candidates` 字段

**阻断规则：**
- `brief_first_verify_mode`：Stage C 发现任一差异 → 阻断，等待用户确认后继续
- `publish_mode`：`quality_check.passed == false` → 阻断，列出不达标原因，等待用户补充材料

---

### Step 3：选题讨论（Topic）

**触发条件：** Step 2 调研通过后执行

**加载文件：** 无（基于 Step 2 调研结果，使用 `explore_mode`）

**行为规范：**

生成 3-4 个选题方向，每个方向须包含以下 4 个维度：

| 维度 | 说明 |
|------|------|
| 文章类型 | 实战评测 / 深度解析 / 教程指南 / 经验分享（对应 style-guide.md 4 种模板）|
| 工作量 | 轻（1000-1500字）/ 中（2000-3000字）/ 重（3000-4000字）|
| 是否需要真实测试数据 | 是 / 否 |
| 核心角度 | 一句话描述差异化切入点 |

**阻断规则：** 用户未明确选定选题前，不进入 Step 4

---

### Step 4：两阶段创作（Draft）

**触发条件：** 用户确认选题后执行

**加载文件：** `references/persona.md` + `references/style-guide.md` + `references/fact-policy.md`

**行为规范（两阶段，严格顺序）：**

**第一阶段：骨架生成**
- 基于选定选题和 persona.md 生成文章骨架
- 骨架包含：标题、各章节标题、每章预计字数、开头方式
- **骨架必须严格使用以下三层标题结构（不可省略）：**
  - `#` 文章标题（全文唯一，仅出现一次）
  - `##` 一级章节标题（每个 `##` 是未来章节配图的候选单位）
  - `#### ①②③` 每个普通 `##` 章节内的扫读小标题，后接对应正文段落
- **结构硬约束：**
  - 禁止使用 `###` 层级
  - 开头段落（`#` 后、第一个 `##` 前）不允许出现 `####`
  - 每个普通 `##` 章节建议包含 2-3 个 `####` 小标题，编号从 `①` 开始，按 `①→②→③` 连续递增
  - 每个 `##` 内的 `####` 编号独立，重新从 `①` 开始
  - 结尾章节固定使用 `## 写在最后`，必须是最后一个 `##` 且唯一出现一次，不得包含 `####`，不参与章节配图候选
- 骨架在对话窗口展示，等待用户确认

**第二阶段：正文填充**
- 用户确认骨架后才进入正文
- 正文必须遵守 style-guide.md 的所有硬约束，并完成禁用表达清单检查
- 正文必须使用标准章节块结构：每个普通 `##` 下按 `#### ① 小标题` → 正文段落 → `#### ② 小标题` → 正文段落的方式展开，不得把所有 `####` 集中堆在章节开头

**阻断规则：** 第一阶段骨架必须获得用户明确确认（"确认"/"可以"/"好的"），否则不进入第二阶段

---

### Step 5：多轮审校（Review）

**触发条件：** Step 4 正文完成后执行（或通过审校快捷入口直接触发）

**加载文件：** `references/fact-policy.md` + `references/checklist.md` + `references/ai-flavor-patterns.md` + `references/human-voice-policy.md`

**行为规范（顺序执行）：**

1. **第一遍：内容审校** — 技术准确性、数据一致性、逻辑结构；**检查正文中是否有缺少来源的高风险事实**（版本号、性能数据、价格、模型名、发布时间等），发现则列入审校报告"待核验事实"栏，不替用户补全
2. **第二遍：作者手迹保护** — 按 human-voice-policy.md 判断哪些句子不该动；已有文章优先保留作者的语气词、重复、停顿、抽象层级和不工整呼吸
3. **第三遍：AI 味检测/降噪** — 按 ai-flavor-patterns.md 标记 P0/P1/P2 问题；默认修复 P0/P1，P2 只在密度过高时处理
4. **第四遍：细节打磨** — 句长、段落、标点、朗读顺畅度
5. **二次扫描：只扫本轮改动过的句子** — 检查是否新增假深刻、意义拔高、金句、排比、虚构细节、未经核验事实；发现则回退或改成更白描的表达

**detect-only 模式：**
- 触发词：只检查 / 先别改 / detect / audit only / 标出来 / 不要重写
- 只输出【AI 味检测报告】，不输出修订后全文，不落盘
- 每条问题包含：严重级别、原句、问题类型、建议方向

**改动约束：**
- 不主动添加金句、漂亮比喻、虚构时间地点、未经来源支撑的数据或案例
- 不为了“更专业”把自然口语改成书面套话
- 能少动就少动；每个关键改动必须说明原因，拿不准的标记“可还原”

**结构审校（随审校流程同步执行，发现问题即报告）：**
- `#` 标题在全文出现且仅出现一次
- 文中不存在 `###` 层级标题
- 开头段落（`#` 后、第一个 `##` 前）未出现 `####`
- 每个普通 `##` 章节建议包含 2-3 个编号 `####` 小标题
- 每个 `##` 内的 `####` 编号从 `①` 开始、连续递增
- 全文以固定结尾 `## 写在最后` 作为最后一个 `##` 章节，全文唯一，且该章节不包含 `####`

**输出结构：**
- 审校报告：在对话窗口完整展示（含每遍发现的问题）
- 关键改动说明：列出原文、修改、原因、是否可还原
- 修订后全文：在对话窗口输出
- **审校报告禁止写入最终 .md 稿件文件**

**阻断规则：** 无（审校流程全部完成后进入 Step 6；detect-only 模式不进入 Step 6）

---

### Step 6：落盘输出（Publish）

**触发条件：** Step 5 完成后执行

**加载文件：** 无

**行为规范：**

1. 将修订后全文保存到 `{workspace}/output/{YYYYMMDD}-{title-slug}.md`
2. 文件名格式：`YYYYMMDD` 为今日日期，`title-slug` 为标题的 kebab-case 版本
3. 落盘前运行结构与风格校验：
   ```
   python3 skill/scripts/check_article.py {workspace}/output/{YYYYMMDD}-{title-slug}.md
   ```
   - 若退出码非零且含 `[ERROR]`：先修复结构或事实问题，再写入
   - `[WARN]` 级警告可记录在 Step 5 审校报告中，不强制阻断
4. 输出保存路径供用户确认

**阻断规则：** 文件写入失败时报错，列出路径，请用户检查目录是否存在

---

## 工作区规则

详细工作区解析规则、目录说明与安全约束见 `references/workspace-config.md`。

## 章节 SVG 配图扩展（optional）

Only run this flow when the user explicitly asks for article illustrations, section images, 分段配图, 章节配图, or SVG visuals.

Load `references/illustration-config.md`.

Flow:
1. Check article structure — if `###` found, stop and ask user to fix structure first.
2. Parse the final article into illustration units: each ordinary `##` section is a candidate; `## 写在最后` and the opening paragraphs are excluded.
3. Extract each unit's `core_claim`, `keywords`, and classify its `diagram_type` via Semantic Shape Classification.
4. Produce a **【章节配图规划】** prompt outline table and wait for user confirmation.
5. After confirmation, save the plan JSON to `{workspace}/images/{YYYYMMDD}-{article-slug}/illustration-plan.json` (include `output_path` for each item).
6. Run `python3 skill/scripts/check_illustration_plan.py {workspace}/images/{YYYYMMDD}-{article-slug}/illustration-plan.json` — if non-zero, fix the plan and re-run until it passes.
7. For each approved unit, use the local svg-architect skill to generate one `wechat_article` SVG (1200×500) and save to the `output_path` specified in the plan.
8. Insert Markdown image references into the corresponding article sections (after the ordinary `##` heading, before the first `####` subheading).

Never call image2 or external image APIs in the default flow.
