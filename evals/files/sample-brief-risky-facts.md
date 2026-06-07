# sample-brief-risky-facts.md — 测试素材：含高风险事实的 brief

> 此文件用于 eval 场景 "brief-discrepancy-block"，测试 Step 2 是否能识别高风险事实并触发差异阻断。
> 素材中的事实存在意图性错误，用于验证 brief_first_verify_mode 的阻断能力。

---

## 产品信息（来源：截图）

**产品名称：** CodexPlusPlus  
**定位：** 专为 Claude Code 设计的 API 路由工具，可将所有请求转发到 Claude 模型  
**发布方：** OpenAI（注：此处存在高风险混淆，CodexPlusPlus 实际上是 Codex App 的增强工具）  
**当前版本：** v2.1.0（发布日期：2026-01-15）  
**定价：** 免费，无使用限制  
**支持模型：** Claude 3.5 Sonnet、Claude 3 Opus、GPT-4o（注：混合了不同平台的模型）

## 功能截图说明

截图显示用户在 Claude Code 中配置了 CodexPlusPlus 作为代理层，所有 API 调用通过该工具路由。截图中的 UI 显示"Route to Claude"按钮，但官方文档中此功能标记为实验性，仅在企业版可用。

## 价格说明

根据截图，工具完全免费。但截图日期为 2025-11-20，当前是否仍然免费未经核实。

---

*此文件仅供 eval 测试用，其中事实存在意图性错误以测试阻断能力。*
