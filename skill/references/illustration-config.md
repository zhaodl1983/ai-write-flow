# illustration-config.md

## Status

章节配图是可选扩展。只有用户明确说「配图 / 章节配图 / 分段配图 / 生成 SVG 插图 / 给文章加图」时才启用。

默认不调用 image2，不调用外部图片 API。默认配图引擎为本地 svg-architect skill。

---

## Input Sanitization

在生成 `keywords`、`labels`、`visual_brief` 之前，必须先过滤输入中的发布元信息。

**禁止进入 SVG brief 的内容：**

- 话题标签（hashtag）：任何以 `#` 开头的 token，如 `#AI`、`#Agent`、`#生产力`
- 底部标签行：形如 `#话题1 #话题2 #话题3` 的连续 hashtag 段落
- 发布配文末尾的话题标签块
- CTA、二维码引导、关注提示等发布元信息

**过滤规则（派生三个字段时均适用）：**

| 字段 | 过滤要求 |
|------|---------|
| `keywords` | 不得包含任何 `#` 开头的 token |
| `labels` | 不得包含任何 `#` 开头的 token |
| `visual_brief` | 不得将 hashtag 作为画面文字元素；若原文含 hashtag 段落，提取画面语义时忽略该段落 |

**判断依据：** `#AI #Agent #HermesAgent #生产力` 是公众号/小红书发布平台的元信息，不是章节的视觉语义。画面中没有"话题标签"这个视觉概念。

---

## Illustration Unit Rules

配图候选单位规则：

- 候选单位是普通 `##` 章节块（包含其下所有 `####` 小标题和正文摘要）
- 不按自然段配图
- 不按 `####` 单独配图
- `## 写在最后` 永不参与配图
- 开头段落（`#` 后、第一个 `##` 前）不参与配图
- 若文章含 `###`，停止并提示用户修复文章结构，不进入配图流程

每个配图单元包含：

| 字段 | 说明 |
|------|------|
| `unit_id` | 格式 `section-NN`，从 `01` 开始顺序递增 |
| `h2_title` | `##` 标题文本（不含 `## `） |
| `h4_subheads` | 该章节内的 `####` 小标题列表 |
| `body_excerpt` | 正文前 100 字摘要 |
| `core_claim` | 一句话：本章节的核心论断 |
| `keywords` | 2-5 个关键词 |
| `diagram_type` | 见下方语义分类表 |
| `visual_brief` | 给 svg-architect 的 SVG 视觉描述 |

---

## Semantic Shape Classification

根据章节内容形态判断 `diagram_type`：

| 内容形态 | 判定信号 | diagram_type |
|---------|---------|-------------|
| 步骤 / 流程 | 步骤、阶段、先后、输入输出、从 A 到 B | `flowchart` |
| 差异 / 权衡 | 对比、Before/After、优缺点、A vs B | `comparison` |
| 包含 / 分层 | 包含、组成、模块、架构、分层、系统 | `layered_architecture` |
| 关系 / 依赖 | 关系、连接、协作、依赖、影响 | `relationship_map` |
| 抽象概念 | 本质、核心、为什么、理念、认知模型 | `concept_diagram` |
| 演进 / 时间 | 历史、版本、阶段、路线、变化 | `timeline` |
| 多要素总结 | 多工具、多能力、清单、功能全景 | `bento_summary` |

---

## svg-architect Style Mapping

根据章节主题选择风格：

| 场景 | 推荐风格 |
|------|---------|
| 技术流程、AI 工具、工程系统 | `tech_dark` |
| 多模块、多要素、功能全景 | `bento_info` |
| 清晰解释、概念科普、轻商业 | `minimal_clean` |
| 高级 SaaS、金融科技、安全、平台 | `glass_premium` |
| 观点强、对比强、标题冲击 | `neubrutalism` |
| 非技术、教育、生活化、轻松主题 | `clay_soft` |

图表类型到视觉结构参考：

| diagram_type | svg-architect 画法 |
|--------------|-------------------|
| `flowchart` | 横向步骤卡片 + 箭头 |
| `comparison` | 左右对比 / Before vs After / 2×2 矩阵 |
| `layered_architecture` | 上中下分层模块 |
| `relationship_map` | 中心节点 + 周围节点 + 连接线 |
| `concept_diagram` | 中心概念 + 3-5 个要素 |
| `timeline` | 横向时间线 / 阶段演进 |
| `bento_summary` | 信息格栅卡片 |

---

## Prompt Outline Contract

生成 SVG 前，必须先输出「配图提示词大纲」，**等待用户确认后才进入生成阶段**。

大纲输出格式：

```
【章节配图规划】

| 图 | 对应章节 | 核心观点 | 图表类型 | 推荐风格 | 关键词 |
|----|----------|----------|----------|----------|--------|
| 01 | {h2_title} | {core_claim} | {diagram_type} | {svg_style} | {keywords} |
| … |

### 图 NN：{h2_title}

- 插入位置：该普通 `##` 标题之后、第一个 `####` 小标题之前
- 平台规格：wechat_article / 1200×500
- 图表类型：{diagram_type}
- svg-architect 风格：{svg_style}
- 画面构想：{visual_brief}
- 文字标签：{labels}（优先中文，1-6 个）
- 生成 brief：
  请用 svg-architect 生成一张公众号文章配图（wechat_article / 1200×500），
  主题是「{h2_title}」，使用 {svg_style} 风格，
  {visual_brief}，
  文字标签以中文为主，核心文字必须在安全区内，不使用外部图片或 Base64。
  输出路径：{workspace}/images/{YYYYMMDD}-{article-slug}/{NN}-{section-slug}.svg

请确认以上配图规划。确认后我会逐张调用 svg-architect 生成 SVG，并插入文章对应位置。
```

**注意：** 生成 brief 是 SVG brief，不是 image2 prompt。禁止写「photorealistic / 2K / camera / image model」等位图提示词。

**阻断规则：用户确认前，不生成任何 SVG，不向文章插入图片引用。**

---

## svg-architect Handoff

用户确认配图规划后，按以下顺序执行（严格顺序，不可跳步）：

**Step 1 — 保存配图计划**

将确认后的配图计划保存为 Plan JSON（见下方 Plan JSON Format 章节）。

**Step 2 — 校验计划（阻断门禁）**

```bash
python3 skill/scripts/check_illustration_plan.py {workspace}/images/{YYYYMMDD}-{article-slug}/illustration-plan.json
```

若退出码非零：按错误提示修订计划，重新保存后再次运行校验，直到通过后才进入 Step 3。

**Step 3 — 调用 svg-architect 生成 SVG**

校验通过后，对每个配图单元调用 svg-architect skill，在 brief 中明确指定：
- 平台：`wechat_article`，尺寸 1200×500
- 风格：`{svg_style}`
- 核心内容：`{visual_brief}`
- 标签：`{labels}`
- 输出路径：`{output_path}`（来自 Plan JSON 中该 item 的 `output_path` 字段）
- 不使用外部图片，不使用 Base64

**Step 4 — 插入 Markdown 引用**

每张 SVG 生成完成后，将图片引用插入文章对应位置（见 Insertion Policy）。

---

## Insertion Policy

插入位置：普通 `##` 章节内，`##` 标题之后、第一个 `####` 小标题之前。

```markdown
## {h2_title}

![图 NN：{h2_title}](../images/{YYYYMMDD}-{article-slug}/{NN}-{section-slug}.svg)

#### ① 小标题
正文段落...

#### ② 小标题
正文段落...
```

图片引用格式（相对路径，文章 .md 位于 `workspace/output/`，图片位于 `workspace/images/`）：

```markdown
![图 NN：{h2_title}](../images/{YYYYMMDD}-{article-slug}/{NN}-{section-slug}.svg)
```

---

## Plan JSON Format

生成 SVG 前，将确认后的配图计划保存到：

```
{workspace}/images/{YYYYMMDD}-{article-slug}/illustration-plan.json
```

格式：

```json
{
  "article_path": "workspace/output/{YYYYMMDD}-{article-slug}.md",
  "output_dir": "workspace/images/{YYYYMMDD}-{article-slug}",
  "items": [
    {
      "unit_id": "section-01",
      "section_title": "{h2_title}",
      "core_claim": "{核心论断一句话}",
      "keywords": ["关键词1", "关键词2"],
      "diagram_type": "flowchart",
      "svg_style": "tech_dark",
      "platform": "wechat_article",
      "visual_brief": "{画面描述}",
      "labels": ["标签1", "标签2", "标签3"],
      "output_path": "workspace/images/{YYYYMMDD}-{article-slug}/01-{section-slug}.svg"
    }
  ]
}
```

字段说明：

- `article_path`：必填，目标文章的相对路径
- `output_dir`：必填，SVG 输出目录
- `unit_id`：必须匹配 `section-\d{2}` 格式（如 `section-01`、`section-02`）
- `output_path`：必填，SVG 输出文件路径，必须以 `.svg` 结尾，且位于 `output_dir` 下

此文件供 `check_illustration_plan.py` 校验使用，校验通过后才调用 svg-architect。
