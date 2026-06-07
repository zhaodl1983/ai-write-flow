# design-note-step2-verify-mode.md — Step 2 调研模式设计说明

> 这是一份设计决策记录，说明 brief_first_verify_mode 的来源与约束。

---

## 背景

2026-06-06，写 Agnes AI 文章时暴露了一个问题：  
CodexPlusPlus 的官方定位是 Codex App 增强工具，但用户简报里的截图展示的是用它路由 Claude Code 请求。  
当时 Step 2 把用户截图直接视为 Tier 1 Final，跳过了对"产品定位"这个高风险字段的外部核查，  
导致文章里把工具定义为 Claude Code 路由工具，与官方描述有偏差。  
这类问题留到写作阶段才被发现，属于"该在研究阶段消歧但没做"的问题。

---

## 核心设计决策

**用户素材 = Tier 1 Candidate，不是 Tier 1 Final。**

不能因为有 briefs/ 就跳过核查，也不必因为有 briefs/ 就跑完整的 Layer 1-4。  
取而代之的是三段式 `brief_first_verify_mode`：

1. **Stage A — Brief Ingest**：提取候选事实，标记为 Tier 1 Candidate
2. **Stage B — Targeted Verification**：只核查高风险字段，定点验证
3. **Stage C — Discrepancy Report**：有差异 → 立即阻断 → 用户确认后继续

**差异消歧必须在 Step 2 完成，不能留到写作或审校阶段兜底。**

---

## 高风险字段清单（Stage B 必查）

- 产品名称（相近名称但主体不同）
- 产品定位（'专为 X 设计' vs '支持 X'）
- 发布主体（公司名、团队归属）
- 版本 / 日期
- 截图功能归属（截图里的功能是否真的属于该产品）
- 价格 / API 地址 / 兼容性（会随时间变动）

---

## 保留的好设计

骨架修订后直接二次确认，不回滚 Step 3。这个处理方式是正确的，下次不要改掉。
