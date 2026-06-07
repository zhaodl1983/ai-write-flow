# research-config.md — 调研行为规范

> AI 执行 Step 2 调研时的机器可执行配置。不是给人读的文档，是行为约束。

---

## 执行模式

| 模式 | 触发时机 | 门禁状态 |
|------|---------|---------|
| `brief_first_verify_mode` | Step 2，briefs/ 有内容时（**默认**） | Stage A→B→C 三段式，Stage C 有差异则阻断 |
| `publish_mode` | Step 2，briefs/ 为空时（全量调研） | 全部 4 层生效，任一不达标则阻断 |
| `explore_mode` | Step 3 选题讨论（为角度探索提供线索） | 仅执行 Layer 1+2，不做 Claim 核查 |

---

## brief_first_verify_mode 三段式规范

用户素材（截图、手写数据、简报）定义为 **`Tier 1 Candidate`**，不是 `Tier 1 Final`。须经 Stage B 核查通过后才能升级为 `verified`。

### 高风险字段（Stage A 必须提取，Stage B 必须核查）

| 字段类型 | 说明 |
|---------|------|
| 产品名称 | 相近名称但主体不同，容易混淆 |
| 产品定位 | '专为 X 设计' vs '支持 X' 的归属差异 |
| 发布主体 | 公司名、团队、上下级关系 |
| 版本 / 日期 | 版本号、发布时间、截图时效性 |
| 截图功能归属 | 截图中演示的功能是否归属于该产品 |
| 价格 / API / 兼容性 | 会随时间变动的字段，需确认最新性 |

### Stage B 核查原则

- 只验证高风险字段，不机械跑与候选事实无关的 Layer
- 外部来源按下方 Source Tiers 判断质量
- 候选事实与外部来源**一致** → 标记 `verified`
- **找不到**外部来源 → 标记 `unverified`（记录，不强制阻断，但正文须加归因标注）
- 候选事实与外部来源**矛盾** → 标记 `discrepancy`，**必须阻断**

### 差异门禁触发条件（任一满足即阻断）

- 用户截图和公开资料表述不一致
- 产品名称相近但主体不同
- 功能演示成立，但官方定位描述不同
- 时间相关信息（版本、定价、可用性）无法确认最新性

---

## 4 层核心机制（publish_mode 使用）

```
Layer 1  主题解析      判断 topic_type → 确定权威来源形态
Layer 2  来源分层      Tier 1-4，事实结论只接受 Tier 1/2 支撑
Layer 3  Claim 核查    原子级事实拆解 + supported/unverified/contradicted
Layer 4  时效门禁      30 天统一硬门禁，不达标直接阻断
```

---

## Layer 1：主题类型枚举

| topic_type | 涵盖子类型 | 权威来源应包含 |
|-----------|-----------|-------------|
| `product` | 产品发布、模型发布、公司公告、功能更新 | 官网 + 官方文档 + release/changelog + GitHub org |
| `concept` | 技术概念、方法论、学术论文、标准规范 | 原始论文 + 作者主页 + 参考实现 |
| `open-source` | 开源项目、框架、工具库 | GitHub repo + docs + releases + changelog |
| `news` | 行业新闻、投融资、政策法规、收购事件 | 第一手公告 + 原始材料（须 ≥2 个独立来源交叉确认）|

---

## Layer 2：来源分层（Source Tiers）

| Tier | 来源类型 | 能否支撑发布级事实 |
|------|---------|----------------|
| 1 | 官方文档、release notes、公告、论文原文、GitHub releases | ✅ 是 |
| 2 | 作者/维护者博客、技术演讲、实验室说明 | ✅ 是 |
| 3 | 权威科技媒体（TechCrunch、The Verge 等） | ❌ 仅用于找线索 |
| 4 | 社区帖子、论坛、问答 | ❌ 仅用于找线索 |

---

## Layer 3：Claim 级 JSON Schema

调研结果必须输出为以下 JSON 结构，保存到 `workspace/research/{YYYYMMDD}-{topic-slug}.json`：

```json
{
  "topic": "string",
  "topic_type": "product | concept | open-source | news",
  "research_date": "YYYY-MM-DD",
  "mode": "brief_first_verify_mode | publish_mode | explore_mode",
  "freshness_policy": {
    "max_age_days": 30,
    "blocking": true
  },
  "tier_1_candidates": [
    {
      "field": "string",
      "candidate_text": "string",
      "source": "brief",
      "verification_status": "verified | unverified | discrepancy",
      "discrepancy_note": "string (仅 status=discrepancy 时填写)"
    }
  ],
  "discrepancies": [
    {
      "field": "string",
      "user_claim": "string",
      "external_evidence": "string",
      "source_url": "string",
      "risk": "string"
    }
  ],
  "sources": [
    {
      "tier": 1,
      "title": "string",
      "url": "string",
      "source_date": "YYYY-MM-DD"
    }
  ],
  "claims": [
    {
      "claim_id": "c001",
      "claim_text": "string",
      "tier": 1,
      "source_url": "string",
      "source_date": "YYYY-MM-DD",
      "evidence_quote": "string",
      "status": "supported | unverified | contradicted"
    }
  ],
  "quality_check": {
    "citation_coverage": "100%",
    "unsupported_claim_count": 0,
    "contradiction_count": 0,
    "discrepancy_count": 0,
    "stale_source_count": 0,
    "passed": true
  }
}
```

---

## Layer 4：时效门禁

- **30 天统一硬门禁**，无例外
- 背景材料可用旧资料，但必须显式标注 `"type": "background"`，**不得进入发布正文**
- 任何来源没有明确日期 → 视为不合格，直接阻断

---

## 阻断条件

### brief_first_verify_mode（Stage C 触发）

- `tier_1_candidates` 中有任一 `verification_status == "discrepancy"` → 阻断，输出【差异确认】格式，等待用户确认

### publish_mode（Layer 1-4 触发）

- `status == "unverified"` 的 claim 存在
- `status == "contradicted"` 的 claim 存在
- 任何 claim 的 `source_date` 超过 30 天
- 任何来源没有明确日期
- `quality_check.passed == false`
- 发布正文中出现未标注的旧资料
