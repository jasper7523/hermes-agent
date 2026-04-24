# 賈斯伯戰略中樞：新版 Agent Hub (MSWA) 技能遷移與動態掛載架構

針對您提問的：「是否要將舊版 `D:\AI_Agent_Hub\.agent\skills\` 移植到新版 `D:\Agent_Hub\` 及其子代理 (如 Hermes) 中？」
以下是基於**【四區沙箱隔離協定】**與**【零幻覺鐵律】**所設計的全新架構指南。

## ⚠️ User Review Required

> [!IMPORTANT]
> **全域唯讀註冊表 (Global Read-Only Registry)**
> 經過我的系統探測，新版目錄 `D:\Agent_Hub\skills\` **已經存在**且包含了 969 個子技能資料夾。這表示實體的原始碼遷移已經在物理層面完成了。
> **核心決策**：我們 **絕對不該** 將這 969 個技能複製到各個子代理（如 Hermes 或 N5 Book Writer）的專屬沙箱內。這會造成嚴重的硬碟冗餘，並且會因為上下文過度污染導致模型產生幻覺 (Hallucination)。

## Open Questions

> [!WARNING]
> 1. **符號連結 (Symlink) 權限**：在 Windows 環境下執行動態掛載，最優雅的方式是使用符號連結 (`mklink`)。系統目前啟動 `adk_engine.py` 的終端機是否具備系統管理員權限以建立 Symlink？
> 2. **YAML 路由定義**：目前各節點 (N1-N7) 是否已經有專屬的 `agent_config.yaml` 或類似設定檔？我們需要在那邊宣告每個 Agent 被允許讀取哪些技能。

---

## 系統拓樸與實作策略 (Proposed Architecture)

在新版的 **Monorepo Sub-Workspace Architecture (MSWA)** 規範下，技能的管理必須從「實體複製」升級為「動態派發」。

### 1. 建立全域技能軍火庫 (The Global Armory)
*   **路徑**：`D:\Agent_Hub\skills\` (目前已存在)。
*   **定位**：N1 中樞專屬的唯讀軍火庫。所有 900+ 個 SaaS 爬蟲與自動化腳本都鎖在這裡。子代理人 **沒有權限** 擅自跨目錄讀取此區塊。

### 2. 實施按需動態掛載 (Just-In-Time Skill Mounting)
當 N1 喚醒特定代理人時，透過設定檔定義該代理人需要的技能，並以符號連結 (Symlink) 映射到該代理人的沙箱內，營造出「專屬技能庫」的假象。

#### [設計範例] 節點的精準技能配置：

*   **N5 (Book Writer Agent) 專屬掛載**：
    *   路徑：`D:\Agent_Hub\agents\Book_Writer_Agent\.agents\skills\`
    *   掛載清單：`academic-book-writer`, `wiki-query`, `pdf`, `docx`, `Consensus MCP`
    *   *效益*：N5 的腦中只有學術寫作，不會突然發神經去調用 `Facebook Automation`。

*   **N7 (Hermes Watchdog Agent) 專屬掛載**：
    *   路徑：`D:\Agent_Hub\agents\Hermes_Agent\.agents\skills\` (或獨立的 `d:\hermes-agent\.agents\skills\`)
    *   掛載清單：`gstack`, `gsd-debug`, `systematic-debugging`
    *   *效益*：守門狗專注於系統除錯與無頭瀏覽器截圖，維持大腦極致輕量化。

*   **N2 (Legal Research Agent) 專屬掛載**：
    *   掛載清單：`academic-paper`, `legal-bibliography-specialist`

### 3. 實作步驟 (Implementation Steps)

1.  **清理舊架構殘留**：確認 N1 已經全面接管 `D:\Agent_Hub\skills\`，舊的 `D:\AI_Agent_Hub` 可以進入備份封存狀態，避免路徑混淆。
2.  **建立映射腳本**：由 N3 (Software Engineer) 撰寫一支 Python 腳本 `mount_skills.py`，讀取每個 Agent 的 `config.yaml`，自動在它們的沙箱建立對應的 Symlink。

## Verification Plan

### Automated Tests
1. 在 N5 沙箱內執行 `ls D:\Agent_Hub\agents\Book_Writer_Agent\.agents\skills\`，驗證只能看見 5-10 個學術寫作相關的技能，而非 969 個。
2. 嘗試讓 N5 調用 `Facebook Automation`，系統應基於沙箱隔離協定拋出 `STATUS_UNAUTHORIZED_SKILL` 錯誤。

### Manual Verification
請您檢視本計畫的隔離邏輯是否符合您對「多代理人專業分工」與「零信任架構」的想像。若您同意，後續只要告訴 N1「請將 XX 技能授權給 YY 代理人」，我們就會動態生成連結，無需再手動複製檔案。
