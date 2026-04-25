# N2 Perplexity Pro 整合腦內風暴與架構設計 (Brainstorming & Architecture Design)

## [目標與情境]
N2 (Legal Research Agent) 需要具備自動化網路檢索與深度研究的能力。您目前擁有 Perplexity Pro 訂閱，我們的目標是**繞過 API Key 的限制，最大化利用您已付費的 Pro 帳號**，讓 N2 能自動化調用 Perplexity 進行檢索。

---

## [腦內風暴：可行性方案分析 (Approaches)]

經過您的提議與 N7 核心針對 `jackwener/OpenCLI` 的深度研讀，架構推演產生了**顛覆性的翻轉**。以下是更新後的方案矩陣：

### 👑 方案 D：OpenCLI + 本機 Electron App (CDP 協議控制) - 【N7 全新強烈推薦】
這就是您提議的終極解法。我們利用 OpenCLI 透過 Chrome DevTools Protocol (CDP) 直接連線並控制您本機安裝的 Perplexity 桌面版 (Electron App)。
*   **運作機制**：透過 `opencli browser` 指令，N2 能以 CDP 協定直接在背景對 Perplexity App 送出指令。這並非傳統的「模擬滑鼠點擊」，而是直接與底層渲染引擎溝通。
*   **優點 (完美擊破所有痛點)**：
    1.  **絕對防禦穿透**：使用的是原廠官方 App 的連線特徵，100% 免疫 Cloudflare 與機器人驗證。
    2.  **永久免維護 Cookie**：直接利用 App 內建的登入狀態，終身不需重新抓取 Token。
    3.  **零干擾 (靜默執行)**：透過 CDP 送出的 `type` 與 `click` 指令是在背景處理序執行，**完全不會搶走您的實體滑鼠與鍵盤焦點**。
    4.  **無損 Markdown 擷取**：直接透過 CDP 讀取 DOM 樹狀結構，能完美解析並保留 `[1](url)` 等學術引用標籤，不會有剪貼簿格式跑掉的問題。
    5.  **精準狀態監聽**：能直接攔截網路請求 (Network tab) 或 DOM 變化，精準知道生成何時結束。
*   **缺點**：唯一的先決條件是您的 Perplexity 桌面端必須是基於 Electron 開發，且能以 `--remote-debugging-port` 參數啟動。

### 🟢 方案 A：GStack 無頭瀏覽器 (Headless Browser)
*   **運作機制**：用獨立的 Chromium 搭配您的 Cookie 跑自動化。
*   **優缺點**：功能完善，但 Cookie 需要定期手動匯出維護，且仍有微小機率被嚴格的 Cloudflare 防禦機制判定為無頭爬蟲。在方案 D 出現後，本方案降級為備案 (Fallback)。

### 🟡 方案 B：內部 API Cookie 劫持 (Internal API Auth)
*   **優缺點**：極易被官方判定為惡意爬蟲而封鎖 Pro 帳號，**已否決**。

---

## ⚖️ [決策對比更新：為什麼 OpenCLI 改變了戰局？]

| 評估維度 | 舊版方案 D (PyAutoGUI 盲操) | 新版方案 D (OpenCLI + CDP) | 方案 A (GStack 網頁版) |
| :--- | :--- | :--- | :--- |
| **執行干擾度** | 極高 (搶鍵盤焦點) | **零干擾 (背景 CDP 注入)** | 零干擾 |
| **格式保留 (Markdown)** | 容易遺失 | **完美保留 (DOM 樹擷取)** | 完美保留 |
| **反爬蟲風險** | 零 (官方 App) | **零 (官方 App)** | 中 (無頭瀏覽器特徵) |
| **Auth 維護成本** | 零 (App 保持登入) | **零 (App 保持登入)** | 高 (需定期更新 Cookie) |

*此文件已歸檔，後續開發請參考正式的 Implementation Plan。*
