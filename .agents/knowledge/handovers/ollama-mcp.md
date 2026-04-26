# Ollama MCP 本地算力部署手冊 (Ouroboros Last Line)

## 1. 部署狀態
- **模型狀態**：本地已安裝 gemma4:latest (9.6 GB)。
- **MCP 伺服器**：建議使用標準 mcp-server-ollama 容器或本地 Node.js 橋接。
- **API Endpoint**：預設為 http://localhost:11434。

## 2. N1 (中樞) 交接要點
- **定位**：最後守護者 (Last Defense)。
- **使用場景**：
    - 無網路環境。
    - 處理極度敏感、不宜上雲的隱私數據。
    - 網路 API (Antigravity/Gemini) 全部 429 或 500 時。

## 3. N5/N8 設定建議
- **N5/N8**：通常不作為主力撰寫，但可用於「基礎拼字檢查」或「格式格式化」等不需要高智慧但頻率極高的微小任務，以節省雲端 Token。