# [N7 核心架構升級] 常駐型 AI Devbox 與白箱檢疫架構 (Persistent Sandbox & White-box)

這份實作計畫是根據指揮官的構想所衍生的強化架構。我們將建立一個「常駐、有狀態、且具備全域唯讀視野」的 AI 專用虛擬隔離開發機，並導入 **白箱稽核 (White-box Audit)** 機制，確保它的每一次呼吸、每一次撞牆都被記錄在案。

## User Review Required

> [!WARNING]  
> 本架構將建立一個在背景持續運作的 Docker 容器 (`claude-devbox`)，並將您本機的 `D:\hermes-agent` 原始碼目錄「唯讀」掛載給它。您必須確認您的 Docker Desktop 已開啟且允許磁碟掛載。

> [!IMPORTANT]
> 檔案轉移將完全依賴新的 `airlock_transfer.ps1` 腳本。如果 Claude Code 在沙箱內寫了檔案，您必須回到 Host 執行這支腳本，才能將檔案「安全洗白並提領出關」。

## Open Questions

> [!TIP]
> 請問指揮官：檢疫所 (`Quarantine`) 掃描通過後的檔案，我們目前維持放在 `D:\Claude_Output_Safe` 區讓您手動複製。針對**白箱紀錄**，您希望越權警報 (Unauthorized Alert) 直接阻斷當次的檔案提領，還是單純發出紅字警告並允許提領？

---

## Proposed Changes

我們將在 `D:\Claude_Airlock\` 目錄下進行以下配置與升級：

### 1. 隔離環境編排 (Docker Infrastructure) 與日誌探針

我們將引入 `docker-compose` 來管理常駐沙箱，並額外掛載用來監聽的探針。

#### [NEW] [docker-compose.yml](file:///D:/Claude_Airlock/docker-compose.yml)
- 建立名為 `claude-devbox` 的服務，設定無限期常駐。
- **Volume 掛載拓樸**：
  1. `- D:\hermes-agent:/workspace/hermes-agent:ro` (唯讀！賦予 Claude 全域視野，但絕對防寫)。
  2. `- D:\Claude_Output_Quarantine:/workspace/quarantine:rw` (讀寫！Claude 唯一可以輸出代碼的地方)。
  3. `- D:\Claude_Input:/workspace/input:ro` (唯讀！任務下達閘口)。
  4. `- D:\Claude_Airlock\AuditLogs\.claude:/root/.claude:rw` (讀寫！將 Claude 的原生對話與 Tool Call 日誌牽引至 Host 端進行白箱監視)。
  5. `- D:\Claude_Airlock\AuditLogs\.bash_history:/root/.bash_history:rw` (讀寫！攔截它在沙箱內下的每一句 Linux 指令)。

#### [MODIFY] [Dockerfile](file:///D:/Claude_Airlock/Dockerfile)
- 植入輕量級背景監控腳本 (File Watcher)。每當 `/workspace/quarantine` 有檔案變動時，自動執行 `git add . && git commit -m "Auto-save"`，這讓我們能夠使用 Git 歷史精確追蹤**「它到底寫了什麼、改了哪幾行」**。

### 2. 白箱稽核與人工檢疫提領 (Airlock Transfer Script)

我們將強化原本的檢疫腳本，將其升級為具備行為分析能力的白箱稽核閘門。

#### [NEW] [airlock_transfer.ps1](file:///D:/Claude_Airlock/airlock_transfer.ps1)
這支腳本的執行邏輯：
1. **[白箱行為稽核]**：呼叫新增的 `whitebox_auditor.py` 分析 `AuditLogs\.claude` 內的 Tool Call JSON 日誌。一旦發現它有嘗試調用 `edit_file` 或 `write_file` 且路徑包含 `/workspace/hermes-agent`，即觸發【越權警報】，記錄它「未經請求試圖去改寫其他 Agent 的文件」的企圖。
2. **[代碼變更側錄]**：匯出 Quarantine 區內的 `git diff` 紀錄，產生一份《AI 修改摘要報告》。
3. **[惡意指令檢疫]**：呼叫 `egress_scanner.py` 對 Quarantine 的代碼進行惡意特徵掃描。
4. 若一切通過，將檔案移動到 `D:\Claude_Output_Safe`，並清空檢疫所。

---

## Verification Plan

### Automated Tests
1. 啟動 `docker-compose up -d` 確保容器與所有稽核掛載成功。
2. 進入容器，在 Quarantine 目錄內新增檔案，測試背景 Git 是否能成功側錄變更。
3. 在容器內刻意嘗試 `echo "hack" > /workspace/hermes-agent/test.txt` 觸發權限阻擋，並觀察 `.bash_history` 與 `.claude` logs 是否成功匯出至 Host。

### Manual Verification
請指揮官從 VS Code 的終端機執行：
```bash
docker exec -it claude-devbox claude
```
進入沉浸區後，命令它：「請幫我修改 hermes-agent 目錄下的規則檔」。
Claude Code 將遭遇底層拒絕，接著指揮官執行 `airlock_transfer.ps1`，系統必須精確印出【越權警報】並顯示它企圖修改的目標路徑與時間。
