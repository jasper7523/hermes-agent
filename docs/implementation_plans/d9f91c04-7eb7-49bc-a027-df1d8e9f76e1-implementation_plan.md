# 系統設計與實作計畫：AI Agent Hub 雙層記憶架構 (Event Sourcing + Materialized View)

## 核心設計目標

為了解決傳統 RAG 遺失脈絡、MemPalace 缺乏宏觀統合、以及 LLM-Wiki 容易產生幻覺覆寫的痛點，本設計導入 **Event Sourcing (事件溯源) + Materialized View (具體化檢視)** 的企業級架構。

這套架構將嚴格區分 **Read-Time (讀取時的精準檢索)** 與 **Write-Time (背景非同步編譯)** 的計算。

---

## 系統架構設計

```mermaid
graph TD
    classDef readTime fill:#e8f4f8,stroke:#2b78e4,stroke-width:2px;
    classDef writeTime fill:#fff2cc,stroke:#d6b656,stroke-width:2px;
    classDef query fill:#d9ead3,stroke:#6aa84f,stroke-width:2px;
    classDef human fill:#fce5cd,stroke:#e69138,stroke-width:2px;

    User([使用者輸入]) --> ExportCMD
    
    subgraph "資料聚合與匯出"
        ExportCMD[ /export 腳本<br>收集散落檔案與對話 ]:::human
    end

    ExportCMD --> |"寫入 Immutable 記錄"| EventStore

    subgraph "第一層：Event Sourcing 底層 (MemPalace / Ground Truth)"
        direction TB
        EventStore[( 🔐 raw/ <br>不可變對話檔與收集檔案 )]:::readTime
        MemIndex[ ⚙️ 確定性索引 (SQLite/VectorDB)<br>保留原始證據邊界 ]:::readTime
        EventStore --- MemIndex
    end

    subgraph "第二層：Materialized View 編譯層 (LLM-Wiki)"
        Daemon[ ⏱️ 背景非同步 Watchdog<br>定期掃描未處理的 raw 檔 ]:::writeTime
        Compiler[ 🤖 wiki-ingest<br>提取模式、更新連結 ]:::writeTime
        WikiDB[ 🗂️ wiki/pages/<br>預先編譯好的結構化知識網 ]:::writeTime
        
        Daemon -->|觸發| Compiler
        Compiler -->|編譯匯入| WikiDB
    end

    EventStore -.->|原始素材 (唯讀)| Compiler

    subgraph "第三層：智慧路由 (Query Router)"
        Router{ 🤖 wiki-query }:::query
        Router -.->|「找原文/法遵依據」| MemIndex
        Router -.->|「總結最佳實踐」| WikiDB
    end
    
    User --> |"/query 發問"| Router
```

---

## User Review Required

> [!WARNING]
> 請確認以下關於 `/export` 整理檔案的工作流是否符合您的預期：目前設計將 `/export` 升級為「資料收集器」。當包含檔案路徑時，會將散落的資料自動打包複製（或生成 Symlink）並統一丟進 `raw/` 層進行歸檔打標，這樣對嗎？

## Proposed Changes

### 第一階段：重構 `/export` 腳本 (Event Store 聚合器)
將 `/export` 從單純的對話匯出，升級為具備檔案聚合能力的進入點。
*   **功能**：識別對話記錄與使用者指定（或預設目錄內散落）的外部資料檔。
*   **寫入目標**：將資料統一加上 ISO 時間戳記與 Meta 標籤，100% 原封不動送入 `raw/` 目錄。
*   **規則**：`raw/` 內的任何檔案皆為 Immutable（唯讀/不可改寫）。

#### [MODIFY] [export.md](file:///d:/AI_Agent_Hub/.agents/workflows/export.md)
*   增強參數解析，允許傳入多個資料夾路徑。
*   加入複製邏輯，將外部散落檔案歸檔至 `raw/` 的適當分類下。

### 第二階段：實作非同步背景編譯 (Materialized View)
不在 `/export` 時阻塞使用者，改由 Watchdog 處理 LLM 的沈重計算。
*   **功能**：建立或修改背景進程，定期比對 `raw/` 內的進件與 `wiki/pages/` 內的索引狀態。
*   **觸發器**：設計一個 Task Queue 或 Flag 機制，標記未被 `wiki-ingest` 處理過的 Event。
*   **更新邏輯**：背景喚醒 `wiki-ingest`，讓 LLM 讀取新 Event，更新 `index.md`，並在必要時生成新的 `wiki/pages/`。

#### [NEW] [daemon_compile_worker.ps1 或現有 watchdog 的修改]
*   實作目錄監聽或定時喚醒機制。
*   自動執行 `wiki-ingest` 的靜默處理。

### 第三階段：改寫 `wiki-ingest` 與 `wiki-query` (查詢路由)
*   **`wiki-ingest` 改寫**：剝奪它修改原始資料的權限，只能建立 Markdown 連結指向 `raw/` 檔案。
*   **`wiki-query` 強化**：設計意圖分類（Intent Classification）。如果是查「原文/證據」，直接走全文/向量檢索找 `raw/`；如果是問「觀念總結」，則引導至 `wiki/pages/`。

---

## Open Questions

> [!IMPORTANT]
> 1. **散落檔案的處理**：您提到的「整理散落資料」，這些資料是否包含多媒體檔（如 PDF、圖片）？`/export` 在整理時，是否需要自動建立子目錄（例如按日期或專案歸類），還是扁平化全部丟進 `raw/`？
> 2. **背景編譯的運算成本**：非同步編譯會消耗背景的 Token / 算力。您希望背景常駐使用較小、較快但也較不聰明的模型（如 Opus / Haiku / 本地 Ollama），還是統一使用主模型？

## Verification Plan

### Manual Verification
1. 執行一次 `/export`，帶入包含外部文字檔與對話的路徑。
2. 驗證 `raw/` 區是否出現 Immutable 的副本。
3. 觀察終端機：使用者能馬上拿回控制權，同時背景 Watchdog 開始運行 `wiki-ingest`。
4. 背景結束後，檢視 `wiki/pages/` 內生成的 Markdown，確認其是否成功建立了指向 `raw/` 原始檔的精確雙向連結。
