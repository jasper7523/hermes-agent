---
name: evaluator-calibration
trigger: manual
description: 觸發 N7 跨模型校準流程（Gemini + Ollama Gemma 雙重評估）
---

# Evaluator 校準流程 (Cross-Model Calibration)

## 使用方式

在需要高信賴度評估時，輸入 `/evaluator-calibrate` 觸發此流程。

## 校準步驟

### Step 1：Gemini 產出主評估報告

使用 N7 四維評分系統，對目標交付物進行評估：
- 品質 / 原創性 / 工藝 / 功能性（各 1-5 分）
- 列出至少 1 個缺陷或改進空間
- 產出評估摘要（≤200 字）

### Step 2：調用 Ollama Gemma 取得第二意見

```
工具：mcp_Ollama-Local-Oracle_ollama_chat
模型：gemma4:latest
Prompt 範本：

「你是一個嚴格的程式碼/架構審查員。請對以下交付物進行四維評分（品質/原創性/工藝/功能性，各 1-5 分），並列出至少 1 個缺陷。

交付物內容：
{target_content}

請以 JSON 格式回覆：
{ "quality": X, "originality": X, "craftsmanship": X, "functionality": X, "defects": ["..."] }
」
```

### Step 3：比對差異

- 計算四維平均分差異：`|gemini_avg - gemma_avg| / gemini_avg * 100`
- **差異 ≤ 20%**：校準通過，採用 Gemini 評估結果
- **差異 > 20%**：標記 `CALIBRATION_MISMATCH`，升級至使用者人工仲裁
- 紀錄校準結果至 `.agent_comms/evaluations/`
