# EKKOLearnAI Web UI 整合計畫與規格書

> **N7 系統日誌**：收到最高權限覆寫指令，角色切換至 N7 (Infrastructure Watchdog)。本計畫專注於底層架構部署、Docker 容器隔離與 API 路由設定。本節點不直接修改業務程式碼，以下提供之 YAML 與配置指令將交由 N3 (Software_Engineer_Agent) 執行。

## 系統拓樸與規格 (System Topology & Specs)

### 1. 核心架構
* **前端介面 (UI)**: Vue3 (EKKOLearnAI)
* **中介層 (BFF)**: Node.js (Koa, 監聽 Port 8648 / Docker 映射 Port 6060)
* **底層通訊 (API)**: Hermes Gateway (監聽 Port 8642)
* **實體位置**: 部署於專屬 Docker Network (`hermes_net`)，確保 BFF 只能與 Gateway 進行內網通訊，實現零信任沙箱 (Zero-Trust Sandbox)。

### 2. 存取控制與持久化
* **配置目錄**: 宿主機的 `~/.hermes` 映射至容器內的 `/root/.hermes` 或 `/home/hermeswebui/.hermes`（須確保 UID/GID 一致性，防範 `PermissionError`）。
* **Auth Token**: 自動生成於 `~/.hermes/hermes-web-ui/.token`，首次啟動時需透過 `docker logs` 擷取。

---

## ⚠️ User Review Required (需使用者確認)

> [!IMPORTANT]
> **UID/GID 權限對齊問題**
> 若宿主機的 `~/.hermes` 已經存在，新部署的 Web UI 容器需要具備相同的讀寫權限。請確認是否同意在啟動前由腳本自動執行 `chown -R $(id -u):$(id -g) ~/.hermes` 來對齊權限？

> [!WARNING]
> **對外通訊埠口 (Port Exposure)**
> 預設配置將 Web UI 暴露在宿主機的 `6060` Port。若伺服器處於公網，強烈建議我們在前方架設 Nginx 進行反向代理與 SSL 憑證加密。本次 MVP 階段是否允許直接暴露 `127.0.0.1:6060`？

---

## Proposed Changes (實作草稿)

本節列出需交由 N3 建立或修改的基礎設施檔案。

### 基礎設施配置 (Infrastructure Configuration)

#### [NEW] `docker-compose.webui.yml`
這將是啟動 EKKOLearnAI UI 的核心編排檔：

```yaml
version: '3.8'

services:
  hermes-webui:
    image: ekkoye8888/hermes-web-ui:latest
    container_name: hermes_webui_n7
    restart: unless-stopped
    ports:
      - "127.0.0.1:6060:8648"  # 將 BFF 的 8648 綁定到本機 6060
    environment:
      - TZ=Asia/Taipei
      # - AUTH_DISABLED=1  # 預設開啟 Auth，若需關閉可取消註解
    volumes:
      - ~/.hermes:/root/.hermes  # 映射 Hermes Agent 狀態目錄
    network_mode: "host"         # 由於 Gateway 在宿主機運行，MVP 先採用 host 模式以便直接訪問 localhost:8642
    # 若 Gateway 也 docker化，應改用自訂 network 進行內部 DNS 解析
```

#### [NEW] `scripts/deploy_webui.sh`
N3 將執行的自動化啟動腳本：

```bash
#!/bin/bash
set -e

echo "[N7 Watchdog] 正在對齊 ~/.hermes 目錄權限..."
mkdir -p ~/.hermes
# 確保權限正確，避免 Web UI 啟動後無法讀取 config.yaml
# sudo chown -R $(id -u):$(id -g) ~/.hermes

echo "[N7 Watchdog] 啟動 EKKOLearnAI 容器..."
docker compose -f docker-compose.webui.yml up -d

echo "[N7 Watchdog] 等待 BFF Server 啟動並擷取初始 Auth Token..."
sleep 5
docker logs hermes_webui_n7 | grep -i "token" || echo "請手動查看 Auth Token: docker logs hermes_webui_n7"
```

---

## Verification Plan (驗證計畫)

部署完成後，將調用以下機制作為監控驗收：

### 1. 網路層連線測試 (Network Layer)
* **指令**: `curl -s http://127.0.0.1:6060 > /dev/null && echo "Web UI Alive"`
* **預期**: BFF 正常回應 200 OK。

### 2. Gateway API 橋接驗證 (API Bridge)
* **動作**: 檢查 Gateway 的終端機日誌，確認是否有來自 BFF (:8648) 的連線請求進入 `:8642`。

### 3. GStack 視覺回歸測試 (Visual QA)
* **指令**: `$B goto http://127.0.0.1:6060` -> `$B snapshot -i` -> `$B screenshot /tmp/ui_login.png`
* **預期**: 成功渲染登入畫面，且無 JS Console Error，確認四區沙箱內的通訊無阻。
