# Ouroboros 算力路由器交接紀錄 (Step 3-4: NVIDIA NIM 實作完成)

本紀錄詳細記載了 NVIDIA NIM 作為「影子算力」主力引擎的掛載過程、配置規範與驗證結果。

---

## 1. 基礎設施配置 (Infrastructure Configuration)

### **環境變數 (.env)**
- **文件路徑**: [d:\hermes-agent\.env](file:///d:/hermes-agent/.env)
- **更新內容**:
    ```bash
    NVIDIA_API_KEY=nvapi-YbQn...  # 已更名以符合 PROVIDER_REGISTRY 規範
    NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
    ```
- **規範**: 必須使用 `NVIDIA_API_KEY` 而非原先規劃的 `NVIDIA_NIM_API_KEY`，以確保 `hermes_cli/auth.py` 能正確自動識別。

### **供應商註冊 (Provider Registry)**
- **註冊位置**: [d:\hermes-agent\hermes_cli\auth.py](file:///d:/hermes-agent/hermes_cli/auth.py)
- **狀態**: `nvidia` 供應商已在系統核心註冊，支援 `api_key` 驗證。

---

## 2. 代碼掛載實作 (Code Implementation)

### **輔助算力路由更新**
- **文件路徑**: [d:\hermes-agent\agent\auxiliary_client.py](file:///d:/hermes-agent/agent/auxiliary_client.py)
- **修改內容**:
    - 在 `_API_KEY_PROVIDER_AUX_MODELS` 映射表中新增 `"nvidia": "meta/llama-3.1-405b-instruct"`。
- **效益**: 當主要付費算力 (如 OpenAI/Claude) 額度耗盡或發生 Error 402/429 時，系統會自動 fallback 至 NVIDIA NIM 並調用 Llama-3.1-405B 執行背景任務（如文獻壓縮、摘要、視覺分析）。

---

## 3. 驗證與冒煙測試 (Verification & Smoke Test)

### **測試環境**
- **Python 環境**: 全域 Python 3.13 (已手動補齊 `openai`, `python-dotenv`, `httpx` 依賴以利測試)。
- **測試入口**: `agent.auxiliary_client.call_llm`

### **測試結果**
1. **供應商解析**: ✅ 成功識別 `NVIDIA_API_KEY` 並正確解析 Base URL。
2. **端到端通訊**: ✅ 成功發送請求至 NVIDIA 集成端點。
3. **模型身份確認**: ✅ 經 `call_llm` 呼叫後，回傳內容確認為 `Llama 3` 模型（符合 `llama-3.1-405b-instruct` 配置）。
4. **輸出範例**:
    > "I'm an artificial intelligence model known as Llama..."

---

## 4. N1 交接指令 (Instruction for N1)

N1 (總部中樞) 在後續維護或切換模型時，請知悉以下指令與機制：

1. **查看當前路由狀態**:
    ```powershell
    # 檢查 NVIDIA 是否正確載入
    python -c "from agent.auxiliary_client import _resolve_api_key_provider; from dotenv import load_dotenv; load_dotenv('d:/hermes-agent/.env'); print(_resolve_api_key_provider())"
    ```
2. **強制使用 NVIDIA 執行特定任務**:
    當你發現 Gemini 額度吃緊時，可以手動指派任務給 nvidia 提供者：
    ```python
    from agent.auxiliary_client import call_llm
    call_llm(task="compression", provider="nvidia", messages=...)
    ```
3. **配額警示**:
    NVIDIA NIM 免費額度為 **40 RPM** (約每 1.5 秒一次請求)。若背景任務併發過高觸發 429，`auxiliary_client.py` 已具備自動避讓與重試機制。

---

## 5. 待辦事項 (Pending Items)

- [ ] **CDP 影子伺服器聯動**: 確保 `D:\Agent_Hub\tools` 下的 `gemini_web_mcp_server.py` 已啟動，並與 `mcp_tool.py` 正式橋接。
- [ ] **Ollama 本地熱備援**: 驗證 11434 端口通訊正常。

---
**簽署**: N7 (Hermes Agent) 代行 N3 (Software Engineer) 職能
**日期**: 2026-04-26
