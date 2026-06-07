---
name: ai-write-flow
version: 0.1.0
description: |
  Use this skill when the user wants to write, rewrite, polish, fact-check, outline, draft, or review Chinese technical articles, AI/tooling blog posts, 公众号长文, tutorials, or existing drafts. Use for full writing workflows from input material ingestion, research, topic selection, outline approval, drafting, and three-pass review; also use when the user asks to 降AI味, 去AI腔, 润色, 改写, 审校, or make writing more natural.
---

# ai-write-flow — 技术博客写作工作流

## 快捷入口：审校模式

**触发意图：** 用户传入已有文章 + 表达"降AI味 / 审校 / 去掉AI腔 / 润色"等意图

**跳过步骤：** Steps 1-4 全部跳过

**直接加载：** `references/style-guide.md` + `references/checklist.md`

**执行流程：** 直接进入 Step 5 三遍审校（内容 → 风格 → 细节）

**输出结构：** 审校报告（对话窗口展示）+ 修订后全文

---

## 主流程（6 步）

### Step 1：工作区解析 & 素材检查（Workspace & Brief Check）

**触发条件：** 工作流启动时自动执行

**加载文件：** `references/workspace-config.md`

**行为规范：**

1. 加载 `references/workspace-config.md`，按以下优先级解析运行时工作区：
   - 若用户在本次对话中明确指定路径 → 使用该路径
   - 若环境变量 `AI_WRITE_FLOW_WORKSPACE` 已设置 → 使用该路径
   - 若 `/Users/zhaodonglin/Documents/ai-write-flow/workspace` 存在 → 使用该路径（个人本地模式）
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

**加载文件：** `references/persona.md` + `references/style-guide.md`

**行为规范（两阶段，严格顺序）：**

**第一阶段：骨架生成**
- 基于选定选题和 persona.md 生成文章骨架
- 骨架包含：标题、各章节标题、每章预计字数、开头方式
- 骨架在对话窗口展示，等待用户确认

**第二阶段：正文填充**
- 用户确认骨架后才进入正文；正文必须遵守 style-guide.md 的所有硬约束，并完成禁用表达清单检查

**阻断规则：** 第一阶段骨架必须获得用户明确确认（"确认"/"可以"/"好的"），否则不进入第二阶段

---

### Step 5：三遍审校（Review）

**触发条件：** Step 4 正文完成后执行（或通过审校快捷入口直接触发）

**加载文件：** `references/checklist.md`

**行为规范（三遍，顺序执行）：**

1. **第一遍：内容审校** — 技术准确性、数据一致性、逻辑结构
2. **第二遍：风格审校（降AI味）** — 套话清理、书面词替换、结构强制项、人味增强
3. **第三遍：细节打磨** — 句长、段落、标点、朗读顺畅度

**输出结构：**
- 审校报告：在对话窗口完整展示（含每遍发现的问题）
- 修订后全文：在对话窗口输出
- **审校报告禁止写入最终 .md 稿件文件**

**阻断规则：** 无（三遍全部完成后进入 Step 6）

---

### Step 6：落盘输出（Publish）

**触发条件：** Step 5 完成后执行

**加载文件：** 无

**行为规范：**

1. 将修订后全文保存到 `{workspace}/output/{YYYYMMDD}-{title-slug}.md`
2. 文件名格式：`YYYYMMDD` 为今日日期，`title-slug` 为标题的 kebab-case 版本
3. 输出保存路径供用户确认

**阻断规则：** 文件写入失败时报错，列出路径，请用户检查目录是否存在

---

## 工作区规则

详细工作区解析规则、目录说明与安全约束见 `references/workspace-config.md`。

## 配图扩展（可选）

For optional article image generation, read `references/image-config.md` only when the user explicitly asks to generate or insert images.
