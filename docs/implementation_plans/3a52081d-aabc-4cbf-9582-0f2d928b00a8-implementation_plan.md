# Epic 6 MVP: Airiti Library Auto-Scraper Pipeline Plan

此為 Airiti Library (華藝線上圖書館) 爬蟲實體管線執行的藍圖。

## User Review Required

> [!IMPORTANT]
> 系統已完成第一階段【戰略文件建置】: `docs/playbooks/airiti_sop.md`。
> 礙於系統防護機制（Planning Mode Boundary），在產生 `src/skills/airiti_scraper.py` 以及更動 `tasks.md` 金流總帳前，必須請求指揮官進行實體批准。

## Proposed Changes

### 1. 戰略文件 (Phase 1)
#### [NEW] [airiti_sop.md](file:///d:/AI_Agent_Hub/docs/playbooks/airiti_sop.md)
* 包含了 `id="_Search_檢索列"` 以及 Cookie 消除等防禦戰略的 Single Source of Truth。

### 2. 爬蟲管線實體施工 (Phase 2 - Pending Approval)
#### [NEW] [airiti_scraper.py](file:///d:/AI_Agent_Hub/src/skills/airiti_scraper.py)
* **框架**: 強制使用 `playwright.async_api`。
* **可見性**: `headless=False` 供現地除錯觀測。
* **流程**:
  1. `page.goto("https://www.airitilibrary.com/")`
  2. 嘗試點擊 Cookie consent `_Cookie_ok`。
  3. 自動點選登入 (`.ustyle_topLogin`) 進入機構 SSO。
  4. 回到首頁並向 `id="_Search_檢索列"` 填入「公司法」。
  5. 擷取清單欄位。
  6. 引入嚴格的 Try-Except，防堵 Timeout 死鎖。

### 3. 進度與核銷 (Phase 3 - Pending Approval)
#### [MODIFY] [tasks.md](file:///d:/AI_Agent_Hub/docs/tasks.md)
* 將 Epic 6 進度更新為 `[x]` 並產出終端機點火指令。

## Open Questions

* **機構登入層的帳密交握**：華藝的東吳 SSO 是否需要我們額外寫入教戰守則？還是直接套用目前 `SCU_SSO_USERNAME` 與 `SCU_SSO_PASSWORD` 並交由通用 SSO login 模組接管？(目前計劃直接在腳本中讀取這兩個環境變數進行填充)。

## Verification Plan

### Manual Verification
1. 指揮官將在核准後收到點火指令：`python -m src.skills.airiti_scraper`。
2. 指揮官親自觀測 `headless=False` 彈出的 Chromium 視窗，審查是否能無死鎖登入並搜索出「公司法」文獻清單。
