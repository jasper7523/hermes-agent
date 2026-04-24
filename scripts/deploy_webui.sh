#!/bin/bash
set -e

echo "[N7 Watchdog] 正在對齊 ~/.hermes 目錄權限..."
mkdir -p ~/.hermes
# 確保權限正確，避免 Web UI 啟動後無法讀取 config.yaml
# Windows WSL 或純 Linux 環境可根據需要解除下行註解
# sudo chown -R $(id -u):$(id -g) ~/.hermes

echo "[N7 Watchdog] 啟動 EKKOLearnAI 容器..."
docker compose -f docker-compose.webui.yml up -d

echo "[N7 Watchdog] 等待 BFF Server 啟動並擷取初始 Auth Token..."
sleep 5
docker logs hermes_webui_n7 | grep -i "token" || echo "請手動查看 Auth Token: docker logs hermes_webui_n7"
