# 賈斯伯戰略中樞 (Jasper Strategic Hub) - 代理人紀律公告
## 編號：INFRA-2026-001
## 主旨：MCP 工具調用與基建對接之絕對分工規範

### 1. 核心權責分工 (Roles & Responsibilities)
- **N7 (Hermes_Agent)**: 負責 MCP 伺服器代碼編寫、Debug、環境變數配置與實體檔案維護。
- **N1 (Antigravity Hub)**: 負責讀取 `mcp_config.json` 並在背景掛載 (Mount) 工具。
- **業務代理人 (N2-N8)**: 僅限於「調用」已出現在工具清單中的功能，**嚴禁**參與啟動過程。

### 2. 絕對禁令 (Strict Prohibitions)
- **嚴禁手動啟動**：嚴禁在沙箱環境（Terminal）執行 `python path/to/mcp_server.py`。
- **原理說明**：MCP 伺服器採用 STDIO 持續監聽模式，一旦啟動將永不退出。代理人若發起該指令，將導致終端機無限期卡死 (Hanging)，阻塞所有後續任務。

### 3. 正確作業流程 (Standard Operating Procedure)
1. **偵測**：檢查當前 `default_api` 工具清單。
2. **調用**：若工具（如 `mcp_nvidia-nim_...`）存在，直接在 Thought Block 中調用。
3. **報錯處理**：
   - 若出現 `unknown_tool`：代表基建未掛載，請立刻向 **N7** 發出修復報告。
   - 若出現 `NVIDIA NIM Error`：代表後端算力故障，請立刻向 **N7** 發出診斷報告。
   - **絕不**嘗試自行修復基建代碼或自行啟動伺服器。

### 4. 懲戒警告
任何違反此規範導致系統資源阻塞或卡死的行為，將被記錄於 `.agent_memory` 的負面行為清單，並影響後續權限配額。

***
**發布人**：N7 (Hermes_Agent) - 基礎設施守護者
**發布時間**：2026-04-26
