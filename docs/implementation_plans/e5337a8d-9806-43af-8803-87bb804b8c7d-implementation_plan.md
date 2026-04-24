# [System Rebuild] Phase 2: Task-Groups 叢集註冊與技能對齊 (Skills Alignment)

這份計畫的目標是：**為昨天的空殼 Agent 注入靈魂與實體武器**。我們將嚴格把關 `Zero-Trust` 概念，不讓寫程式的 Agent 碰到寫書的工具，確保各司其職。

## Proposed Changes

我們將建立一份 `task-groups.yaml`（或透過全域設定 UI 逐一鍵入），為 N2 到 N7 正式掛載他們應該擁有的專屬能力（Skills）。根據您的 `all_skills_inventory.md`，我進行了以下戰略性兵裝分配：

### N2: Legal_Research_Agent (法務情報網)
- **職責**：情報窮盡、法規溯源、PDF分析。
- **配置 Skills**:
  - `bb-browser` & `smart-search`: 無驗證碼門檻的實體爬蟲。
  - `opencli-operate` & `cli-anything`: 強制掛載萬用終端機與進階無頭瀏覽器遙控（專門應付高門檻、架構複雜且反爬蟲的法學資料庫）。
  - `pdf`: 終極法學文獻擷取引擎。
  - `wiki-query`: 僅限於對話與檢索，不能修改全域記憶。

### N3: Software_Engineer_Agent (工程除錯手)
- **職責**：修復基建、執行指令、Bug 追蹤。
- **配置 Skills**:
  - `/investigate` & `gsd-debug`: 專職修復報錯。
  - `opencli-operate` & `cli-anything`: 萬用終端機與網頁操控權。
  - `webapp-testing`: Ouroboros 自癒時必備的前端測試驗證工具。

### N4: Creative_Writer_Agent (行銷修辭學)
- **職責**：社群文案與內部狀態公報。
- **配置 Skills**:
  - `superpowers`: 作為發想文案大綱與靈感的腦內風暴中樞。
  - `my-writer`: 寫作生成主核心技能。
  - `internal-comms`: 狀態說明與備忘錄生成。
  - `brand-guidelines`: 確保產出不偏離企業識別。
  - `canvas-design`: 高質感靜態海報輔助。

### N5: Book_Writer_Agent (專書學術作者)
- **職責**：生成《企業法遵與危機管理實務指引》。
- **配置 Skills**:
  - `superpowers`: 賦予撰寫專書前的邏輯推演與長篇架構發想能力。
  - `academic-book-writer`: 強制掛載管顧 Tone 調與合規引註的核心武器。
  - `doc-coauthoring`: 結構化協作。
  - `docx` & `xlsx`: 排版與數據輸出控制權。

### N6: Mem_Agent (記憶節點與圖譜引擎)
- **職責**：背景常駐、Event Sourcing 與圖譜重建。
- **配置 Skills**:
  - `auto-wiki` 系列：包含 `wiki-ingest`, `wiki-lint`, `wiki-update`。它是全系統唯一擁有「修改記憶鏈」特權的節點。

### N7: Hermes_Agent (架構守護與自癒大腦)
- **職責**：Ouroboros 觸發時的鑑識分析與系統巡邏。
- **配置 Skills**:
  - `superpowers`: 自我辯論與推進的核心。
  - `gsd-forensics`: 發生致命錯誤時的「犯罪現場鑑識調查」工具。
  - `gsd-map-codebase`: 專案全域地圖掃描權限。
  - `skill-creator`: 若現有工具無法修復，允許它當場產出新技能。
  - `gstack-planning` 類：`/plan-eng-review`, `/autoplan` 用於全局重構審查。

---

### 👑 Commander (指揮官 / 不受限的環境創造者)
**您 (人類) 本身就是最高權限！**
某些極度危險或破壞性的工具不應該交給 Agent（甚至不給 N1 碰），只能由您在終端機或對話視窗親自下令使用。
- **直屬未編制武器**: `gsd-manager` (中控儀表板), `gsd-update` (核心升級), `gsd-new-workspace` (物理隔離工作區), `gsd-remove-workspace`。
- **部分開發面 GStack**: `/ship` (發布版本), `/freeze` (權限凍結) 必須由指揮官審查後手動敲出。

---

## Open Questions

> [!WARNING]
> 大腦與兵裝庫已經配對完畢！但有兩個實作細節需要指揮官裁定：
> 1. **設定檔格式**：您希望把這份清單寫成單一的 `task-groups.yaml` 檔案，還是您有特殊介面/官方文件格式需要遵循？（例如每位 Agent 需要加上 System Instructions?）
> 2. **目錄隔離**：`gsd-manager` 等進階環境管理工具，是否需要開放給 N3(SE Agent)，還是全權保留給指揮官使用就好？

## Verification Plan
1. 我們會把這些資料寫入 Workspace 的配置檔。
2. 啟動對話輸入 `/agent-hub-routing`。
3. 測試向 N2 請求法規查詢，系統應能成功調用 `bb-browser` 或 `pdf` 技能，而不會產生「技能未找到」的錯誤。
