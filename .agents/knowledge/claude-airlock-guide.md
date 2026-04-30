# Claude Code 氣隙隔離機制與自動化使用指南 (Airlock SOP)

**文件層級：** 總部中樞 (N1) / 核心安全指引
**建立者：** Hermes Agent (N7)
**適用對象：** AI Agent Hub 叢集 (N1-N7) 與總指揮官

---

## 1. 架構背景與物理限制 (First Principles)

為了在 Antigravity 本地端安全且有效率地調用第三方的 Claude Code，我們面臨兩個核心挑戰：
1. **渲染框架限制 (The TTY Barrier)**：Claude Code 的底層採用了 React for CLI (Ink) 框架，這要求執行時必須有原生終端機 (Raw Mode TTY)。若 Antigravity 在背景透過 `subprocess` 或 `run_command` 直接盲調用，會導致進程卡死。
2. **零信任安全 (Zero-Trust Security)**：Claude Code 具備修改本地檔案、執行終端機指令的強大能力。若直接在 Host (本機) 執行，會將整個系統暴露在 AI 生成潛在危險代碼 (如 `eval`, 惡意 `fetch`) 的風險中。

### 解決方案：雙軌作戰與 Docker Airlock 隔離
我們採用「**Antigravity 負責大腦決策 (架構規劃)，Claude Code 負責勞力打擊 (代碼實作)**」的雙軌模式。同時，將 Claude Code 封裝進無 Host 權限的 Docker 隔離艙中，確保所有輸出必須經過靜態掃描洗白才能併入專案。

---

## 2. 實體目錄拓樸 (Topology)

整個 Airlock (遞件閘口) 的物理配置位於 `D:\Claude_Airlock\` 與 `D:\Claude_*`：

- `D:\Claude_Input\`：**[Host 寫入 / 沙箱唯讀]** 存放 Antigravity 生成的 `task.txt` 或 `implementation_plan.md`。
- `D:\Claude_Output_Quarantine\`：**[沙箱寫入]** Claude Code 的原始輸出區。這裡的檔案被視為「受感染」，絕對禁止直接執行。
- `D:\Claude_Output_Safe\`：**[Host 讀取]** 經過 `egress_scanner.py` 洗白、無毒判定後的安全檔案區。
- `D:\Claude_Airlock\egress_scanner.py`：出站檢疫掃描器 (Yara-lite 邏輯)，偵測 `eval`, `exec` 等高危字串。
- `D:\Claude_Airlock\Invoke-ClaudeAirlock.ps1`：全自動化啟動腳本。

---

## 3. 全自動化工作流指令 (Auto-Airlock)

若要命令 Claude Code 寫代碼並確保其在沙箱中受到監管，請**永遠優先使用自動化腳本**，請勿在 VS Code 的終端機直接輸入 `claude` (會破壞沙箱隔離)。

### 啟動指令：
請在 PowerShell (Host) 執行：
```powershell
D:\Claude_Airlock\Invoke-ClaudeAirlock.ps1 -PromptText "請幫我寫一個貪食蛇網頁遊戲，包含 HTML/CSS/JS，並儲存起來。"
```

### 自動化腳本底層執行邏輯：
1. **環境變數綁定**：自動抓取本機 `ANTHROPIC_BASE_URL` 與 `ANTHROPIC_AUTH_TOKEN` 代理金鑰。
2. **閘口重置**：清空 Input 與 Quarantine 目錄。
3. **任務投遞**：將您的提示詞轉存到 Input。
4. **發射隔離艙**：啟動 Docker (`claude-airlock`)，限制掛載目錄，無系統讀寫權。
5. **一擊脫離 (One-Shot)**：Claude Code 生成完畢後，容器瞬間自毀。
6. **安全洗白**：觸發掃描器，將合格代碼轉移至 `D:\Claude_Output_Safe` 供您使用。

---

## 4. 故障排除與維護 (Troubleshooting)

- **金鑰失效或 401 錯誤**：請至系統內容 (`sysdm.cpl`) -> 環境變數，更新 `ANTHROPIC_AUTH_TOKEN`。
- **Docker 啟動失敗**：確保 Docker Desktop 已在本機啟動。首次執行會自動執行 `docker build` 編譯映像檔。
- **檔案卡在 Quarantine**：代表 `egress_scanner.py` 判定生成的代碼中包含高風險字串（被加上 `.quarantine` 副檔名）。若確認安全，請手動改名並移出該目錄。
- **降級方案**：若 Docker 崩潰，備援方案為手動雙擊啟動 `D:\Claude_Airlock\claude_airlock.wsb` (Windows Sandbox)，手動在裡面執行指令。但此法每次啟動無緩存，速度較慢，僅作緊急備援。
