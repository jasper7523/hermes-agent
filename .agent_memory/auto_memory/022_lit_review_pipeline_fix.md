# Issue 022: 文獻綜述批處理管線 (V6) 幻覺與冗餘修復報告

## 1. 問題成因 (Root Cause)
- **幻覺來源**：爬蟲抓取到 Cloudflare 或 JavaScript 封鎖頁面（Access Denied），但腳本未進行內容品質檢查，LLM 依據標題強行生成摘要，導致內容空泛與年份錯誤（如文獻 33）。
- **重複處理**：腳本未過濾 URL 中的 PDF 連結，導致與先前已下載的本地 PDF（如文獻 34）重複處理，造成浪費。
- **檢索死角**：部分學術網址（如 Semantic Scholar）一般爬蟲難以抓取，且缺乏自動備援機制。

## 2. 解決方案 (Solution)
- **實施 Quality Gate**：
    - 引入長度過濾（< 500 字視為無效）。
    - 關鍵字偵測（封鎖頁面關鍵字）。
- **多層次檢索 (Tiered Retrieval)**：
    - 第一層：標準 Requests。
    - 第二層：Perplexity CDP (透過 `perplexity_search.py` 繞過封鎖)。
    - 第三層：Gemini Web Oracle (針對 API 429 限流)。
- **PDF 預過濾**：
    - 偵測 URL 結尾與 Content-Type，若是 PDF 則直接跳過。

## 3. 學習與進化 (Lessons Learned)
- 在處理外部 Web 資源時，**必須實施內容品質檢查 (Validation Step)**，不能假設爬蟲成功即代表獲得有效文本。
- 備援機制應具備「階梯式」設計，優先使用成本較低、速度較快的 CDP，最後才使用 Web Oracle。

## 4. 指令備忘
- 核心修復腳本：`d:\Agent_Hub\agents\Book_Writer_Agent\.tmp\ch1.4_lit_batch_v6.py`
- 依賴項：`d:\hermes-agent\scripts\perplexity_search.py` (Port 9222 需開啟)
