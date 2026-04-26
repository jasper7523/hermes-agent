# Gemini Web CDP 部署與調用手冊 (N1-N8)

## 1. 部署狀態
- **實體路徑**：D:\Agent_Hub\tools\gemini_web_mcp_server.py
- **啟動指令**：python D:\Agent_Hub\tools\gemini_web_mcp_server.py
- **依賴項**：已修正 UTF-8 編碼問題，支援繁體中文輸出。

## 2. N1 (中樞) 交接要點
- **角色分配**：N1 應將此 Server 註冊為「高容量推理節點」。
- **使用場景**：
    - 當 Prompt 超過 10k Tokens。
    - 當需要處理大量 PDF 或長文本分析。
    - 當 Antigravity 原生額度低於 20% 時。

## 3. N5 (寫手) 與 N8 (學術) 的設定建議
N1 在分發任務給 N5/N8 時，應在系統提示詞中加入以下 	ool_choice 邏輯：
- **N5 (Book Writer)**：預設撰寫長章節時，強制調用 gemini_web_mcp 進行初稿生成與潤飾。
- **N8 (Academic)**：在進行多文獻綜述 (Literature Review) 時，優先使用 Gemini Web 的長上下文視窗。