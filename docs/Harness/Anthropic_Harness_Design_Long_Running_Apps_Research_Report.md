# Anthropic「Harness Design for Long-Running Apps」研究報告

> **來源**: [Anthropic: Harness design is key to performance at the frontier of agentic coding](https://www.anthropic.com/engineering/harness-design-long-running-apps) (Prithvi Rajasekaran, Anthropic Labs, 2026-03-24)
> **分析日期**: 2026-05-07
> **報告目的**: 萃取 Anthropic 第一手工程實驗中的三智能體架構、GAN 啟發式評估迴路、Sprint Contract 機制與 Harness 減量策略，作為 Jasper Agent Hub 的高級設計參考。

---

## 1. 文章定位與獨特價值

這是目前所有 Harness Engineering 文獻中**技術深度最高**的一篇。其獨特貢獻：

| 面向 | 其他來源 | Anthropic 獨特貢獻 |
|---|---|---|
| 多智能體架構 | 概念級 | ✅ Planner→Generator→Evaluator 三智能體實作細節 |
| 自評失敗問題 | 點到為止 | ✅ 完整的失敗機制分析 + GAN 啟發解法 |
| 主觀品質量化 | 未提及 | ✅ 四維評分標準（設計品質/原創性/工藝/功能性） |
| Sprint Contract | 未提及 | ✅ Generator-Evaluator 預先談判「完成定義」 |
| Harness 減量 | 「可撕除」概念 | ✅ 逐組件移除的方法論 + 跨模型版本驗證 |
| Context Anxiety | 未提及 | ✅ 模型接近上下文極限時過早收工的行為 |
| 成本數據 | 無 | ✅ Solo $9 vs Harness $200 / DAW 實驗 $124 |

---

## 2. 兩大核心失敗模式

### 2.1 上下文一致性崩壞（Context Coherence Loss）

**現象**：模型在長任務中隨上下文窗口填滿而失去連貫性。

**Context Anxiety（上下文焦慮）**：模型接近自認為的上下文極限時，開始**過早收工**（premature wrap-up）。

**解法對比**：

| 方法 | 機制 | 效果 |
|---|---|---|
| **Compaction（壓縮）** | 摘要對話歷史，同一智能體繼續 | ❌ Context anxiety 仍然持續 |
| **Context Reset（重置）** | 完全清除上下文窗口，啟動新智能體 + 結構化交接 | ✅ 提供乾淨的石板 |

**代價**：Context Reset 增加編排複雜度、token 開銷和延遲。

**模型代際影響**：Sonnet 4.5 嚴重展現 context anxiety → 必須用 context reset。Opus 4.5/4.6 大幅改善 → 可改用 compaction。

### 2.2 自我評估失敗（Self-Evaluation Failure）

**現象**：

> *當被要求評估自己的工作時，智能體傾向於自信地讚美作品——即使對人類觀察者而言，品質明顯平庸。*

**核心洞察**：

> *「調校一個獨立的 evaluator 使其保持懷疑態度，遠比讓 generator 對自己的工作保持批判容易得多。」*

**機制**：分離本身不會立即消除寬大——evaluator 仍是傾向對 LLM 產出寬容的 LLM。但**獨立調校 evaluator 的懷疑度**比讓 generator 自我批判**更可操作**。

---

## 3. GAN 啟發的 Generator-Evaluator 架構

### 3.1 前端設計實驗：四維評分標準

| 維度 | 權重 | 說明 |
|---|---|---|
| **Design Quality** | 🔴 高 | 設計是否感覺像一個連貫整體而非零件集合？色彩、字型、排版、意象是否創造獨特氛圍？ |
| **Originality** | 🔴 高 | 是否有自訂決策的證據？還是模板排版、函式庫預設、AI 生成模式？明確懲罰「AI slop」 |
| **Craft** | 🟡 中 | 技術執行：字型層級、間距一致性、色彩和諧、對比度。能力檢查而非創意檢查 |
| **Functionality** | 🟡 中 | 與美學無關的可用性。使用者能理解、找到、完成操作嗎？ |

**設計決策**：刻意加重 Design Quality 和 Originality，因為 Claude 預設已在 Craft 和 Functionality 上表現良好，但在設計和原創性上經常產出「平淡至極」的輸出。

**校準方法**：使用 few-shot 範例和詳細的分數分解來校準 evaluator，確保其判斷與人類偏好對齊，減少跨迭代的分數漂移。

### 3.2 迴路機制

```
使用者 Prompt
    │
    ▼
┌─────────────┐
│  Generator   │ ── 產出 HTML/CSS/JS 前端
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Evaluator   │ ── 使用 Playwright MCP 操作頁面
│              │    截圖、研究、導航後打分+撰寫詳細批評
└──────┬──────┘
       │ 反饋
       ▼
┌─────────────┐
│  Generator   │ ── 策略性決策：精煉 or 完全轉向？
└──────┬──────┘
       │
       ▼
   重複 5-15 次（每輪 Evaluator 實際導航頁面 → 真實時間消耗）
   完整運行可達 4 小時
```

### 3.3 關鍵發現

| 發現 | 說明 |
|---|---|
| 分數隨迭代改善然後趨於平穩 | 仍有改進空間 |
| 非線性改善 | 有時中間迭代優於最終迭代 |
| 複雜度遞增 | Generator 因 Evaluator 反饋而嘗試更激進的方案 |
| 評分標準本身引導生成 | 「museum quality」用語導致視覺收斂到特定風格 |
| 創意突破 | 荷蘭藝術博物館案例：第 10 輪完全重構為 3D CSS 空間體驗 |

---

## 4. 三智能體全端架構

### 4.1 系統組成

```
使用者（1-4 句話）
    │
    ▼
┌─────────────────────────────────────────────────┐
│  Planner Agent                                   │
│  · 將簡短 prompt 擴展為完整產品規格              │
│  · 指示範圍野心化                                │
│  · 聚焦產品上下文和高階技術設計                  │
│  · 避免指定細粒度技術細節（防止錯誤級聯）        │
│  · 主動在規格中織入 AI 功能                      │
└──────────────────────┬──────────────────────────┘
                       │ 完整產品規格
                       ▼
┌─────────────────────────────────────────────────┐
│  Generator Agent                                 │
│  · 以 Sprint 方式逐功能實作                      │
│  · 技術棧：React + Vite + FastAPI + SQLite/PG   │
│  · 每個 Sprint 結束時自我評估                    │
│  · 使用 Git 進行版本控制                         │
└──────────────────────┬──────────────────────────┘
                       │ Sprint 產出
                       ▼
┌─────────────────────────────────────────────────┐
│  Evaluator Agent                                 │
│  · 使用 Playwright MCP 點擊測試應用              │
│  · 測試 UI 功能、API 端點、資料庫狀態            │
│  · 針對每個 Sprint 打分（產品深度/功能/視覺/品質）│
│  · 任一標準低於硬性門檻 → Sprint 失敗            │
│  · 提供具體修復反饋                              │
└─────────────────────────────────────────────────┘
```

### 4.2 Sprint Contract（衝刺合約）機制

> 這是本文最具原創性的設計模式。

**問題**：產品規格刻意保持高階，implementation 細節不足。

**解法**：每個 Sprint 開始前，Generator 和 Evaluator **談判一份合約**：

```
1. Generator 提議：將建造什麼 + 如何驗證成功
2. Evaluator 審查：確保 Generator 建造的是正確的東西
3. 雙方迭代直到達成共識
4. Generator 按合約建造
5. Evaluator 按合約驗證
```

**通訊方式**：透過檔案——一個智能體寫檔案，另一個讀取後在同一檔案中回應或寫新檔案。

**Sprint 3 範例**：單一 Sprint 的合約包含 **27 個驗證標準**（僅關卡編輯器）。

### 4.3 Solo vs Harness 對比

**Prompt**：生成一個復古電子遊戲製作器

| 面向 | Solo Run | Harness Run |
|---|---|---|
| 規格 | 原始 prompt 直接開工 | Planner 擴展為 16 功能 / 10 Sprint 規格 |
| 設計 | 浪費空間、固定高度面板 | 全視窗畫布、合理面板、一致視覺身份 |
| 功能 | 核心遊戲壞掉（實體不回應輸入） | 核心遊戲可玩（物理有粗糙邊緣但運作） |
| AI 整合 | 無 | 內建 Claude 整合，可用提示詞生成遊戲零件 |
| 成本 | **~$9** | **~$200** |
| 品質 | ❌ 中央功能壞掉 | ✅ 功能完整但有邊緣案例 |

**結論**：成本差異無關緊要，能力差異才是一切。

### 4.4 Evaluator 的調校過程

> *「開箱即用的 Claude 是糟糕的 QA 智能體。」*

**失敗模式**：
1. 識別合法問題 → 自我說服不嚴重 → 批准
2. 測試表面化 → 不探索邊緣案例 → 微妙 Bug 漏過

**調校方法**：
```
讀 Evaluator 日誌 → 找到判斷與人類分歧處 → 更新 QA prompt → 重複數輪
```

**殘留限制**：即使調校後，小型排版問題、不直覺的互動、深層功能中未發現的 Bug 仍然存在。

---

## 5. Harness 減量策略（核心方法論）

### 5.1 核心原則

> *「Harness 中的每個組件都編碼了一個關於模型做不到什麼的假設，這些假設值得壓力測試——因為它們可能是錯的，而且隨模型改善會快速過時。」*

引用 Anthropic 自身的 [Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)：

> *「找到最簡單的可行方案，只在需要時才增加複雜度。」*

### 5.2 減量方法論

| 步驟 | 說明 |
|---|---|
| 1. 不要一次全拆 | 第一次激進裁減嘗試失敗了 |
| 2. 逐組件移除 | 每次只移除一個組件，審查對最終結果的影響 |
| 3. 識別承重組件 | 區分「承重」(load-bearing) 和「裝飾」組件 |
| 4. 隨模型升級重新評估 | 新模型可能使某些組件從承重變為多餘 |

### 5.3 Opus 4.5 → Opus 4.6 的具體減量

| 組件 | Opus 4.5 | Opus 4.6 | 原因 |
|---|---|---|---|
| **Context Reset** | ✅ 必要 | ❌ 可移除 | 4.6 大幅改善長上下文連貫性 |
| **Sprint 結構** | ✅ 必要 | ❌ 可移除 | 4.6 原生處理長任務分解 |
| **Planner** | ✅ 保留 | ✅ 保留 | 沒有 Planner，Generator 會低估範圍 |
| **Evaluator** | ✅ 每 Sprint 評估 | ⚠️ 移至結尾單次 | 效用取決於任務在模型能力邊界的位置 |

### 5.4 Evaluator 的動態角色

> *「Evaluator 不是固定的是/否決策。當任務位於當前模型可靠獨立完成的邊界之外時，它才值得其成本。」*

```
模型能力邊界
    ├── 邊界內的任務 → Generator 獨立完成 → Evaluator 是不必要的開銷
    └── 邊界外的任務 → Generator 仍有弱點 → Evaluator 提供真實提升
```

**隨模型提升，邊界外移** → 更少任務需要 Evaluator → 但前沿任務仍需要。

### 5.5 DAW 實驗結果（更新後 Harness）

**Prompt**：生成一個數位音訊工作站（DAW）

| 指標 | 數值 |
|---|---|
| 運行時間 | ~4 小時 |
| 成本 | $124 |
| Builder 連續運行 | >2 小時（無 Sprint 分解） |
| QA 仍捕獲的問題 | 功能缺口、stub 功能、細節遺漏 |
| 最終產出 | 可運作的瀏覽器 DAW + AI agent 驅動作曲 |

---

## 6. 關鍵設計模式彙整

### 6.1 Planner 的設計哲學

| 原則 | 說明 |
|---|---|
| 範圍野心化 | 被指示要雄心勃勃，不要保守 |
| 高階而非細粒度 | 聚焦產品上下文和高階技術設計 |
| 避免技術細節級聯 | 如果 Planner 指定細節出錯，錯誤會級聯到下游 |
| 約束交付物，放開路徑 | 約束要生產什麼，讓智能體自己想怎麼走 |

### 6.2 檔案基通訊

智能體間不透過 API 或訊息佇列通訊，而是透過**檔案讀寫**：
- Agent A 寫檔案
- Agent B 讀取並在同一檔案中回應，或寫新檔案
- Agent A 讀取回應

**優勢**：可追溯、可除錯、無需複雜的通訊協定。

### 6.3 Evaluator 的 Playwright MCP 整合

Evaluator 不只看程式碼或靜態截圖——它使用 Playwright MCP **實際操作**運行中的應用：
- 點擊按鈕
- 檢查 API 回應
- 驗證資料庫狀態
- 導航頁面、截圖、仔細研究實作

這使 QA 從「code review」提升為「end-to-end testing」。

---

## 7. 前瞻性洞察

### 7.1 Harness 不會縮小，而是移動

> *「有趣的 harness 組合空間不會隨模型改善而縮小。相反，它會移動，AI 工程師的有趣工作是持續找到下一個新穎的組合。」*

### 7.2 三條值得帶走的教訓

| # | 教訓 |
|---|---|
| 1 | 用你正在建構的模型做實驗，讀它在真實問題上的 trace，調校以達成期望結果 |
| 2 | 對複雜任務，分解問題並對每個面向應用專門智能體，有時能帶來額外提升 |
| 3 | 新模型到來時，重新檢視 harness——剝除不再承重的部分，加入新部分以實現之前不可能的更大能力 |

---

## 8. N7 視角：對 Jasper Agent Hub 的直接啟示

### 8.1 可立即採納的設計模式

| # | 模式 | 對映到我們的系統 | 行動 |
|---|---|---|---|
| 1 | **Planner → Generator → Evaluator** | N1（規劃）→ N3（執行）→ N7（驗證） | 強化 N7 的獨立 Evaluator 角色 |
| 2 | **Sprint Contract** | GSD plan-phase → execute-phase 之間 | 加入 Generator-Evaluator 預談判步驟 |
| 3 | **檔案基通訊** | 已部分實作（GSD artifacts） | 標準化為所有 N-agent 間的通訊協定 |
| 4 | **四維評分標準** | N7 審查報告 | 建立 agent 產出的可量化評分框架 |
| 5 | **逐組件減量** | user_rules 審查 | 每次 Gemini 更新時，逐條測試 rules 的承重性 |

### 8.2 Context Anxiety 對 Gemini 的警示

Anthropic 在 Sonnet 4.5 上觀察到的 context anxiety，**極可能也發生在 Gemini 上**——這可能正是使用者觀察到「Gemini 不受控、容易放飛自我」的根本原因之一。

**建議驗證**：設計實驗測試 Gemini 在長上下文下是否展現 premature wrap-up 行為。如果確認，應在 Harness 中加入 context reset 機制。

### 8.3 Evaluator 調校的現實警告

> *「開箱即用的 Claude 是糟糕的 QA 智能體。」*

**推論**：開箱即用的 Gemini 也可能是糟糕的 QA 智能體。N7 的自癒迴圈如果沒有經過刻意調校（讀日誌 → 找分歧 → 更新 prompt → 重複），其判斷可能過於寬大。

---

## 9. 與前四份報告的交叉定位

| 報告 | 角色 | 本報告的增量 |
|---|---|---|
| OpenAI 原文報告 | 為什麼 | 本報告補充：**怎麼做 Evaluator** |
| deusyu 學習檔案 | 深層張力 | 本報告實證：張力 #1（前饋 vs 反饋）的具體解法 |
| everything-gemini-code | 有什麼零件 | 本報告補充：零件**之間如何通訊** |
| NXCode 完整指南 | 怎麼分步建造 | 本報告補充：**建完之後如何隨模型升級減量** |
| **本報告** | **多智能體架構深潛** | 三智能體系統 + Sprint Contract + Harness 減量方法論 |

五份報告構成完整知識體系：
```
[原始文獻] OpenAI 原文報告 ──────────── 「為什麼」
    ↓
[學術批判] deusyu 學習檔案報告 ─────── 「深層張力在哪」
    ↓
[工程套件] everything-gemini-code 報告 ─ 「有什麼零件」
    ↓
[落地藍圖] NXCode 完整指南報告 ─────── 「怎麼分步建造」
    ↓
[架構深潛] Anthropic Harness Design 報告 ── 「多智能體如何協作與演化」 ← 本報告
    ↓
[實作目標] Jasper Agent Hub Harness 架構（待建立）
```

---

## 附錄：原始資料索引

| 資料 | 來源 | 內容焦點 |
|---|---|---|
| Anthropic 原文 | anthropic.com/engineering/harness-design-long-running-apps | 三智能體架構、GAN 迴路、Sprint Contract |
| 前置實驗 | anthropic.com/engineering/effective-harnesses-for-long-running-agents | 初始 harness 設計（initializer + coding agent） |
| Context Engineering | anthropic.com/engineering/effective-context-engineering-for-ai-agents | Context anxiety 問題的背景 |
| Building Effective Agents | anthropic.com/research/building-effective-agents | 「最簡方案」原則 |
| Claude Agent SDK | platform.claude.com/docs/en/agent-sdk/overview | 編排基礎設施 |
| Frontend Design Skill | github.com/anthropics/claude-code/.../frontend-design/SKILL.md | 前端設計品質的基準 |
