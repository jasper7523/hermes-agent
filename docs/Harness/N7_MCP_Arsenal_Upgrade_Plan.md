# 升級目標：巨量 MCP 武器庫 (Python/Node 雙核心) 沙箱整合方案

為了解決指揮官高達 20 款跨語言、跨環境的 MCP 伺服器掛載需求，我們必須對 `claude-devbox` 進行底層架構的「火力升級」。原先的輕量級 Alpine Linux 將無法承受 Playwright 瀏覽器核心與複雜的 Python 依賴，必須升級為全功能的 Debian/Ubuntu 基礎環境。

## 🚨 User Review Required (嚴重架構警告與決策)

> [!WARNING]
> **物理限制警告：Desktop Commander 與 Docker Hub**
> 1. **Desktop Commander**: 這個工具如果是用來操控滑鼠/桌面，它裝在沙箱裡**只能操控 Docker 內部的無頭系統 (Headless Linux)**，無法操控您的 Windows 本機桌面！(這正是零信任沙箱的物理屏障)。
> 2. **Docker Hub**: 它通常需要呼叫主機的 Docker API。在零信任原則下我們沒有掛載 `docker.sock`，因此這個 MCP 在沙箱內可能只具備讀取公開 API 的能力，無法操作您的容器。

> [!IMPORTANT]
> **本地檔案存取：Obsidian**
> 既然您要在沙箱內用 Obsidian MCP，我們必須把您本機的 Obsidian Vault (筆記資料夾) 掛載進去。請在下一步告訴我您本機的 Obsidian 資料夾路徑！

> [!IMPORTANT]
> **API 密鑰安全 (Secret Management)**
> Perplexity, LINE, API Gateway 等都需要 Token。我們必須在 `D:\Claude_Airlock` 建立一個 `.env` 檔案把密鑰餵進去，以免被記錄在指令日誌中。

## 📝 Proposed Changes (預計修改檔案)

### 核心基礎設施 (Infrastructure Layer)

#### [MODIFY] [Dockerfile](file:///D:/Claude_Airlock/Dockerfile)
- 棄用 `node:20-alpine`，改用 `node:20-bookworm` (Debian) 以支援 Playwright 瀏覽器相依性。
- 寫入 Python 3, `pip`, 與神器 `uv` 的安裝指令。
- 安裝 Playwright 所需的系統函式庫 (`npx playwright install-deps`)。

#### [MODIFY] [docker-compose.yml](file:///D:/Claude_Airlock/docker-compose.yml)
- 新增 `env_file: .env` 載入機制。
- 新增 Obsidian 的 Volume 掛載點 (需等待您提供路徑)。

### 自動化武器庫部署 (Deployment Scripts)

#### [NEW] [mcp_installer.sh](file:///D:/Claude_Airlock/mcp_installer.sh)
- 建立一個一鍵安裝腳本。因為要敲 20 次 `claude mcp add` 太浪費時間，我會幫您寫一個 Bash 腳本。
- 自動判別 `npx` (Node.js 工具) 或 `uvx` (Python 工具) 並執行掛載。

## 🔍 Verification Plan (驗證計畫)
1. 指揮官提供 Obsidian 路徑與確認架構警告後。
2. 我將覆寫檔案並請您重新執行 `docker compose up -d --build`。
3. 進入沙箱執行 `./mcp_installer.sh`。
4. 執行 `claude mcp list` 確認 20 款武器皆成功上線。
