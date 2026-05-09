# Ouroboros 路由器設計方案與部署手冊 (繁體中文版)

> [!IMPORTANT]
> **繁體中文產出規範**：本文件已根據「Jasper Strategic Hub」全域指令，將所有術語在地化（如：合規 -> 法遵），並確保在 Windows 環境下以 UTF-8 編碼儲存，避免亂碼。

---

## 🧠 LLM 路由器：三種設計方案對比

我們借鑒了 NVIDIA 的路由器邏輯，針對 Agent Hub 的特殊算力結構提出以下適配方案：

### 1. 語義意圖路由器 (Semantic Intent Router)
*   **核心邏輯**：使用輕量級判斷層偵測任務性質。
*   **調度規則**：
    *   **研究任務** -> Perplexity/Consensus
    *   **創意/長文本 (Long Context)** -> Gemini Web CDP
    *   **代碼/系統控制** -> Antigravity 原生模型
    *   **隱私/基礎任務** -> Ollama
*   **建議用途**：追求智慧最大化與自動化額度優化。

### 2. 額度優先門檻路由器 (Quota-Threshold Router)
*   **核心邏輯**：基於 API 剩餘額度進行硬性分流。
*   **調度規則**：
    *   原生 API > 20% -> 優先使用 Antigravity 確保最高反應速度。
    *   原生 API < 20% -> 自動將非核心任務轉向 Gemini Web CDP。
    *   完全耗盡 -> 啟動 Ollama 本地算力。
*   **建議用途**：極限成本控管，確保系統永不斷線。

### 3. 「任務-模型」固定映射表 (Static Mapping)
*   **核心邏輯**：基於 N1-N8 角色職能的預設映射。
*   **調度規則**：
    *   **N5 (Book Writer)** -> 預設導向 Gemini Web CDP。
    *   **N2 (Legal Research)** -> 預設導向 Perplexity + Gemini。
    *   **N7 (Watchdog)** -> 預設導向 Antigravity。
*   **建議用途**：行為高度穩定，適合生產環境開發。

---

## 📄 Gemini Web CDP 部署與交接手冊

> **定位**：高容量推理節點 (High-Capacity Node)

### 1. 部署狀態
*   **實體路徑**：`D:\Agent_Hub\tools\gemini_web_mcp_server.py`
*   **通訊協議**：已修正 `stdout` 編碼，支援繁體中文傳輸。

### 2. 給 N1 (中樞) 的指令建議
*   **任務指派**：當 User 要求的任務上下文預計超過 **10,000 Tokens** 時，N1 應主動將任務切換至此節點。
*   **N5/N8 設定**：
    *   **N5 (寫手)**：在撰寫長篇章節（如 Chapter 1.3 終稿）時，利用 Gemini Web 處理大量參考文獻。
    *   **N8 (學術)**：在需要總結多本專書或長篇論文集時，優先調用此工具。

---

## 📄 Ollama MCP 部署與使用手冊

> **定位**：最後守護者 (Last Defense / Ouroboros Base)

### 1. 部署狀態
*   **模型**：本地已備妥 `gemma4:latest` (約 9.6 GB)。
*   **伺服器**：監聽於 `http://localhost:11434`。

### 2. 給 N1 (中樞) 的指令建議
*   **隱私保護**：當偵測到敏感個人資訊或公司內部未公開數據時，應告知 User 並嘗試調用 Ollama 進行本地處理。
*   **故障恢復**：若雲端模型發生 429 (Rate Limit) 或網路不穩，N1 應降級至 Ollama 執行拼字檢查或簡單格式轉換，以維持基本生產力。

---

## 🛑 交接 N1 執行指令清單
請指揮官直接將以下清單貼給 N1：

1.  **[ ]** 讀取 `d:\hermes-agent\.agents\knowledge\handovers\` 內的所有部署手冊。
2.  **[ ]** 更新 N5 與 N8 的 **System Prompt**，加入 Gemini Web CDP 的調用觸發條件。
3.  **[ ]** 將 Ollama 註冊為 **Emergency Fallback** 節點。
4.  **[ ]** 所有產出必須符合 **繁體中文（台灣法務在地化）** 規範。
