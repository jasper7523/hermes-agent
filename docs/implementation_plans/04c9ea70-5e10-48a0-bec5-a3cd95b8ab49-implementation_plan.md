# 雙引擎無縫熱切換與極致壓縮翻譯架構
*(Vault-Swap Protocol + JSON Dynamic Batching)*

長官，我已針對「如何用最少次數達到最佳翻譯品質」的戰略目標，完成了系統的架構推演，並採納了您提議的「30年 CCEP 資深專家」人設。

---

## 🛠 Proposed Changes (架構解法)

### 1. 動態批次合併與強型別回傳 (JSON Dynamic Batching)
* **不再單段落發送**：引擎將把相連的 15 個段落打包成一組 (Batching)，一次性發送給 Gemini。
* **次數暴降 93%**：4,184 個段落除以 15，**總請求次數將降至僅約 279 次**！
* **JSON 強制對齊防呆**：利用 `cli_bridge.py` 內建的 `expect_json=True` 參數，強迫 AI 以嚴格的 JSON 格式回傳，例如 `{"P-1": "翻譯", "P-2": "翻譯"}`，確保 100% 精準對位回填。

### 2. 頂級專家 One-Pass 隱性思維鏈 (CCEP Persona)
* **[採用長官建議]** 取消三次校對，將 Prompt 壓縮到極致：
  > *"You are a highly respected Certified Compliance & Ethics Professional (CCEP) with over 30 years of experience. Translate the following English compliance text into Traditional Chinese (Taiwan). Your translation must be authoritative, precise, and fluent. You MUST translate 'Compliance' exclusively as '法遵'. NEVER translate it as '合規'. Do not output your thinking process; return ONLY a JSON object mapping paragraph IDs to their translations."*

### 3. 底層對接 Vault-Swap 雙帳號輪轉 (Enterprise Auth Switch)
* **[MODIFY]** `d:\AI_Agent_Hub\.tmp\ccem_docx_translator.py`
* 改為調用您的心血結晶 `from scripts.cli_bridge import ask_gemini_cli`。
* 執行前主動清除 `os.environ` 內的 `GEMINI_API_KEY`，確保程式走入 `Secondary Route: Enterprise Vault Auth`。
* 若觸發 `QUOTA_EXHAUSTED` (429 Error)，您的 `cli_bridge.py` 將全自動執行 `oauth_B.json` 與 `A` 的熱切換，無縫重送批次。
