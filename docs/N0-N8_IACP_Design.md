# N0-N8 內部通訊機制 (IACP) 架構設計草案

> [!NOTE]
> 這是基於 GStack 與 GSD 精神的「代理人間通訊協議 (Inter-Agent Communication Protocol, IACP)」腦力風暴設計文件。目標是消除目前的黑箱通訊，建立可稽核的通訊軌跡 (Audit Trail)。

## 🎯 核心需求與元資料 (Metadata)

我們需要記錄的核心四要素是：
1. **發話端 (Sender)**：例如 N1 (Jasper)
2. **受話端 (Receiver)**：例如 N5 (Book Writer)
3. **時間戳記 (Timestamp)**：精確到秒的 ISO 格式
4. **通訊內容 (Payload)**：下達的指令或回傳的結果

在此之上，從架構設計的觀點，我建議額外增加兩個追蹤用的維度：
* **追蹤 ID (Trace ID)**：用於把「N1 呼叫 N5」與「N5 回傳結果給 N1」這兩件事綁在一起（類似分散式系統的 Trace Span）。
* **狀態 (Status)**：包含 `[REQUEST]`, `[PROCESSING]`, `[COMPLETED]`, `[ERROR]`。

---

## 🛠️ 三種架構方案探索 (Proposed Approaches)

### 方案 A：GSD 原生檔案系統日誌流 (Pure GSD File Stream)
完全依照 GSD 的純文字檔案管理精神。

* **作法**：在 `.agent_memory/` 或 `.planning/` 底下新增一個 `comms/` 目錄。每一次發生內部通訊，就產生一個 Markdown 檔案，檔名格式為 `YYYYMMDD_HHMMSS_N1_to_N5.md`。
* **優點**：人類極度易讀，完美融入現有的 Git 與檔案系統，您隨時可以用 VSCode 點開來看他們到底說了什麼。
* **缺點**：如果 Agent 們頻繁「碎碎念」或通訊次數增加，會產生海量碎小檔案，長期來看效能較差，且要進行統計與除錯時不易整體概覽。

### 方案 B：SQLite 事件溯源資料庫 (Event Sourcing DB)
結合 Hermes (N7) 的底層技術。

* **作法**：擴展目前 Hermes 內部的 `SessionDB` (SQLite)，建立一張專屬的 `agent_communications` 資料表。所有的通訊都是一筆隱藏的資料庫紀錄。
* **優點**：極致的效能。您可以輕易讓 Agent 執行如「撈出昨天 N8 傳給 N1 的所有錯誤回報」這類複雜查詢。
* **缺點**：人類不直觀。必須開發特定的指令（如 `/show_comms`）才能讓您在終端機或 IDE 中看到這些紀錄，失去「沉浸閱讀」的直覺性。

### 方案 C：混合式通訊總線 (Hybrid Event Bus) 🏆 *N7 推薦*
結合 Ouroboros 概念，取 A 與 B 的平衡。

* **作法**：
  1. **總表 (Livestream Log)**：維護一個單一的 `agent_comms_livestream.md` (或 .jsonl) 檔案，只記錄**輕量摘要**（例如：「[16:20:00] N1 -> N5 [REQUEST]：要求分析法規」）。
  2. **封存 (Payload Storage)**：如果通訊的具體內容超過 500 字，或者夾帶了大量的程式碼/文獻，才將長篇內容獨立存為單一檔案，並在總表中留下檔案超連結 (Markdown link)。
* **優點**：您只要點開 `agent_comms_livestream.md` 就能像看對話紀錄一樣看到所有 Agent 的互動概況。若要深究細節，點擊超連結即可展開。既保留了人類閱讀體驗，也避免了檔案系統的混亂。

---

## 🛑 Open Questions (需指揮官裁示)

> [!IMPORTANT]
> 為了決定最終的實作方向，請指揮官回覆以下核心問題：
> 
> **您希望「通訊紀錄」的「持久性 (Persistence)」與「可見性 (Visibility)」到什麼程度？**
> 
> 1. **全天候錄影**：無論任務大小，事無鉅細全紀錄，我希望有一個像「監控儀表板」的 Markdown 檔案可以隨時看他們說話。**(請選擇方案 C)**
> 2. **案件卷宗**：只有在執行具體 GSD 任務（例如一個 Phase）時，才把該任務相關的通訊寫在該任務的目錄下，任務結束就封存。**(請選擇方案 A 修改版)**
> 3. **底層黑盒**：我平常不想看到這些雜訊，只要在系統出錯或我主動詢問時，你們能從資料庫撈出通訊歷史證明就好。**(請選擇方案 B)**

請裁示您的偏好，或提出您對於方案的修正想法。確認後我們將進入具體的程式碼/腳本規劃階段。
