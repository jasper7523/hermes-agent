# AI Agent Hub 升格為「真實中樞 (True Hub)」實作計畫

這個計畫旨在解決目前 `AI_Agent_Hub` 過度集中在「法律與資料庫檢索」的單一架構，將其升格為真正常駐的「路由中樞 (Hub)」，並將不同業務邏輯拆分給專職的 Sub-Agents。

## 回顧當前架構痛點
目前 `src/core/adk_engine.py` 的 `coordinator_agent` 寫死了大量關於「情報窮盡」、「法學資料庫」的系統指令 (Prompt)，並直接掛載全域工具與 `analyzer/comparator/grader` 子代理。
這導致：
1. **角色混淆**：當要求他寫文章或寫程式時，他會受到法規指令的干擾。
2. **工具大鍋炒**：所有的 `skills/` (包含寫作、程式、爬蟲) 全被打包進單一 `SkillToolset` 並塞給大腦，增加了 Token 消耗與工具調用幻覺。

## Proposed Changes (重構架構)

我們將利用 `google.adk` 既有的 `sub_agents` 特性建立**階層式多重代理 (Hierarchical Multi-Agent)** 架構：

### 1. 創立「總部中樞」 (Hub / Triage Agent)
將 `coordinator_agent` 的身份洗淨，改為「分發調度員」。
**職責**：理解使用者的意圖，若為單純對話則直接回覆；若需專業工作，則將任務委派給對應的 Sub-Agent。不直接持有任何底層武器 (Tools)。

### 2. 創立三大領域特種兵 (Domain Agents)
在 `adk_engine.py` 中新增三個平行的 Agent：

*   **Legal_Research_Agent (法務與情報官)**
    *   **繼承舊業**：原本的「最高執行禁令：情報窮盡與嚴謹推理原則」全部移交給它。
    *   **下轄部隊**：保留原本的 `Analyzer`, `Comparator`, `Grader` 作為它的 sub_agents。
    *   **專屬武器**：綁定法學爬蟲、資料庫讀取 playbook 等技能。
*   **Software_Engineer_Agent (程式開發官)**
    *   **職責**：專注於軟體開發、終端機操作、系統抓蟲。
    *   **指令**：遵循 Clean Code 與 Zero-Trust 系統操作原則。
    *   **專屬武器**：僅掛載 `opencli-operate`, `cli-anything`, `sandbox_io` 等 coding skills。
*   **Creative_Writer_Agent (文案撰稿官)**
    *   **職責**：處理行銷文案、社群貼文、一般論述撰寫。
    *   **指令**：專注於語氣、說服力與排版。
    *   **專屬武器**：掛載 `my-writer`、`auto-wiki` 相關寫作生成技能。

### 3. 工具掛載邏輯重構 (`traffic_router.py` & `adk_engine.py`)
原本 `TrafficRouter.mount_tools` 會把所有武器塞給 `coordinator`。需重構為：
*   讀取 `skills/` 目錄時，透過檔名或標籤分類，分別將對應的 Toolset 賦予三個 Domain Agents。
*   `TrafficRouter` 判斷雙引擎熱切換時，自動將模型設定同步傳遞給 Hub 及其所有的 Sub-Agents。

---

### [MODIFY] src/core/adk_engine.py
- **重構 `_init_engine`**：
  1. 移除 `coordinator_agent` 身上的法規 prompt。
  2. 新增 `Legal_Agent` 並繼承舊有的法規 Prompt 與 Evaluator Pipeline (`analyzer`, `comparator`, `grader`)。
  3. 新增 `Coding_Agent`。
  4. 新增 `Writing_Agent`。
  5. 重新宣告 `coordinator_agent` 作為頂層 Hub，並設定 `sub_agents=[Legal_Agent, Coding_Agent, Writing_Agent]`。
- **重構 `SkillToolset` 自動掛載邏輯**：依照 Skill 的名稱進行分類 (例如含有 `cli` 的給 Coding, `writer` 的給 Writing, 其餘給 Legal)。

### [MODIFY] src/core/traffic_router.py
- 更新 `mount_tools` 以適應多層架構，將全域工具（例如 `get_current_time`）給予 Hub，而 MCP 或 `api_search_tool` 與 `write_to_sandbox` 分派給需要的 Sub-Agent。
- 同時修改外層 FastAPI 呼叫時所注入的 `strategic_prompt`，將其收斂並僅動態賦予負責執行的代理人。

## 第一階段 Verification Plan
1. **Unit Test (Dry Run)**：執行 `pipenv run python d:\AI_Agent_Hub\main.py` 確定 ADKEngine 可以順利將 Hub 與三大 Agent 實例化不崩潰。
2. **Intent Routing Test**：發送「請幫我寫一首關於 AI 的詩」，觀察 ADK 是否成功轉發給 `Writing_Agent` 而非觸發「情報窮盡禁令」退回請求。
3. **Coding Test**：發送「用 python 幫我寫個 hello world」，確認由 `Coding_Agent` 承接。

## 🔴 User Review Required
1. 這三個代理人分類 (Legal / Coding / Writing) 是否符合您的需求？有需要擴增其他的嗎？
2. 在自動掛載 `skills` 時，我們可以簡單透過資料夾名稱進行分發（例如白名單：寫作給 `my-writer`），您是否有偏好的分發方式？
3. 請審視以上架構與方向，授權後我將開始改寫 `adk_engine.py` 與 `traffic_router.py`。
