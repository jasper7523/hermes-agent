# deusyu/harness-engineering — 駕韁工程學習檔案研究報告

> **來源**: [deusyu/harness-engineering](https://github.com/deusyu/harness-engineering) (⭐ 2.4k, Fork 226)
> **分析日期**: 2026-05-07
> **報告目的**: 深度剖析該倉庫對 OpenAI「Harness Engineering」範式的系統性拆解，萃取可直接應用於 Jasper Agent Hub (N1-N7) 的理論框架與工程實踐。

---

## 1. 專案定位與差異化

### 1.1 與 everything-gemini-code 的根本差異

| 面向 | everything-gemini-code | deusyu/harness-engineering |
|---|---|---|
| **性質** | 工程套件 (Toolkit) — 直接拿來用的 rules/hooks/skills | 學習檔案 (Archive) — 理論拆解 + 獨立思考 + 實踐驗證 |
| **核心價值** | 「怎麼配置」(How to configure) | 「為什麼這樣設計」(Why it works) |
| **內容深度** | 寬：14 語言 × 44 agents × 100+ skills | 深：8 篇概念 × 6 篇批判思考 × 19 篇文獻摘要 |
| **理論基礎** | 無（純實作） | OpenAI + Martin Fowler 控制論 + Anthropic + LangChain + Stanford |
| **原創貢獻** | 模組化配置架構 | 8 個跨文獻洞見 + 5 個框架張力分析 |

### 1.2 核心命題

> **Harness Engineering（駕韁工程）= 工程師不再寫程式碼，而是設計環境、明確意圖、構建反饋迴路，讓 AI 智能體可靠地完成工作。**

一句話公式：
```
傳統工程：人類寫程式碼 → 機器執行程式碼
Harness Engineering：人類設計約束 → 智能體寫程式碼 → 機器執行程式碼
```

**核心轉變**：工程師的產出從程式碼變成了**約束系統**——AGENTS.md、架構規則、自訂 linter、反饋迴路。

---

## 2. 六大核心概念（Phase 1）

源自 OpenAI 2026-02-11 原文（Ryan Lopopolo），3 人團隊用 Codex 從空倉庫到 100 萬行程式碼，5 個月，零手寫程式碼。

### 2.1 倉庫即記錄系統 (Repo as System of Record)

**核心**：不在倉庫裡的東西，對智能體不存在。

| 位置 | 對人類 | 對智能體 |
|---|---|---|
| Google Docs / Slack | ✅ | ❌ |
| 團隊成員腦中 | ✅ | ❌ |
| 倉庫內 Markdown | ✅ | ✅ |
| Lint 規則 | 間接 ✅ | ✅（強制） |

**文件結構範本**：
```
AGENTS.md              ← 入口目錄 (~100行)
ARCHITECTURE.md        ← 頂層地圖
docs/
├── design-docs/       ← 設計決策，帶驗證狀態
├── exec-plans/        ← 執行計劃，帶進度日誌
├── product-specs/     ← 產品規格
├── generated/         ← 自動生成（DB schema 等）
└── QUALITY_SCORE.md   ← 每個領域的品質評分
```

**Symphony 延伸**：任務追蹤器也是記錄系統。代碼與文件放倉庫；在飛工作放追蹤器。兩者都對智能體可見，缺一不可。

### 2.2 地圖而非手冊 (Map, Not Manual)

- AGENTS.md ≈ 目錄頁（~100行），不是百科全書
- **漸進式披露**：從小入口開始，指向更深層文件
- 巨型指令文件的三個死因：擠占上下文、無法維護、無法機械驗證

### 2.3 機械化執行 (Mechanical Enforcement)

> **文件會腐爛，lint 規則不會。**

**兩類約束**：

| 類型 | 範例 | 執行方式 |
|---|---|---|
| **架構約束** | Types → Config → Repo → Service → Runtime → UI 分層順序 | CI 阻塞合併 |
| **品味不變式** | 結構化日誌、命名約定、檔案大小限制 | 自訂 linter |

**關鍵設計 — lint 錯誤訊息 = 修復指令**：
```
❌ 普通做法：Error: File exceeds 500 lines.
✅ Harness 做法：Error: File exceeds 500 lines.
   Fix: Split into domain-specific modules following docs/ARCHITECTURE.md#splitting-guide.
```

**哲學**：在中央層面強制執行邊界，在本地層面允許自主權。機械化層約束「結果形態」，目標層約束「意圖與邊界」。

### 2.4 智能體可讀性 (Agent Readability)

- 優先選「無聊」技術（API 穩定、訓練集覆蓋好）
- 有時重新實作子集比包裝不透明的上游行為更划算
- 讓應用可以按 git worktree 啟動

### 2.5 熵管理 = 垃圾回收 (Entropy & Garbage Collection)

**問題**：智能體會復現倉庫中已有的模式——**包括壞模式**。

**失敗方案**：人工清理（每週五花 20% 時間清「AI 殘渣」→ 不可擴展）。

**成功方案**：品味傳播路徑：
```
人類審查評論 → 文件更新 → lint 規則 → 自動應用於所有程式碼
```

### 2.6 人類掌舵，智能體執行

出問題時，答案不是「更努力」，而是「缺什麼上下文 / 工具 / 約束」。

---

## 3. Harness 的精確定義（Fowler 控制論擴展）

> **Agent = Model + Harness**
> Harness = 模型之外的一切程式碼、配置和執行邏輯。

### 3.1 三大知識來源的組件對照

| 來源 | 組件 |
|---|---|
| **LangChain** | System Prompts、Tools & MCP、Skills、沙箱基礎設施、編排邏輯、Hooks/中間件 |
| **HumanLayer** | 六個配置槓桿：AGENTS.md（≤60行）、MCP Servers、Skills、Sub-Agents、Hooks、Back-Pressure |
| **Martin Fowler** | 三層框架：Context Engineering → Architectural Constraints → Garbage Collection Agents |

### 3.2 Guides × Sensors 控制論框架（Böckeler 正式版）

|  | 計算性（確定性，CPU） | 推理性（語義，LLM） |
|--|---|---|
| **引導器/前饋** | bootstrap 腳本、OpenRewrite、LSP | AGENTS.md、Skills、architecture.md |
| **傳感器/反饋** | linter、ArchUnit、類型檢查、覆蓋率 | AI code review、LLM-as-judge |

**關鍵洞察**：單獨使用任一維度都不行——只有反饋 = 反覆犯同樣錯誤；只有前饋 = 不知道規則是否生效。

### 3.3 三個規制維度

| 維度 | 成熟度 | 說明 |
|---|---|---|
| 可維護性 Harness | **最成熟** | 內部程式碼品質，現有工具豐富 |
| 架構適應度 Harness | 中等 | 本質是 Fitness Functions |
| 行為 Harness | **最弱** | 「房間裡的大象」— 功能正確性驗證仍無可靠答案 |

### 3.4 Model-Harness 耦合（關鍵發現）

- 模型在 post-training 階段與特定 harness 共同訓練
- 模型可能 **overfit 到特定 harness**，換 harness 後表現暴跌
- Terminal Bench 2.0 數據：**純 harness 優化**可以把排名從 Top 30 拉到 Top 5

### 3.5 Ashby 必要多樣性定律

> 調節器必須至少擁有與被調節系統同等的多樣性。

LLM 能生成幾乎任何東西（高多樣性）→ 選定拓撲結構 = 削減多樣性 → 全面 harness 變得可行。**「約束越嚴，自主性越強」的控制論根基。**

---

## 4. 約束即產品 (Spec as Product)

第七個概念，由 OpenAI Symphony 衍生。

> 當編碼智能體能從規範生成實作時，**可分發的產品形態從「程式碼」反轉為「規範」**。

- **SPEC.md**：定義問題（要解決什麼、形態、取捨邊界），刻意不寫語言/庫/部署方式
- **WORKFLOW.md**：把隱式人類流程顯式化
- **多語言驗證**：用 Elixir/TS/Go/Rust/Java/Python 各實作一遍，從差異定位規範歧義

**哲學**：
> *「good engineers worry about constraints and their composability」*

---

## 5. 跨文獻八大洞見（Phase 2 獨立思考）

這是該倉庫最高價值的原創內容，對 19 篇文獻的交叉批判分析。

### 洞見 1：Harness 有完整的生命週期

| 階段 | 證據 |
|---|---|
| 誕生 | OpenAI：從零設計 AGENTS.md + linter |
| 成長 | Anthropic：V1 三智能體 + Sprint 合同（$200, 6h） |
| 瘦身 | Anthropic：V2 去掉 Sprint（$125, 4h） |
| 過時 | Anthropic：context reset 在 Opus 上變死重 |
| 被替換 | Anthropic：harness 是牲畜，可隨時換掉 |

**Harness 保質期 ≈ 一個模型代際（3-6 個月）**。需要 **Harness Gardening**——像程式碼一樣被持續修剪。

### 洞見 2：存在四個學派

| 學派 | 代表 | 瓶頸觀 | 作用層次 |
|---|---|---|---|
| **約束派** | OpenAI、HumanLayer | 解空間太大 | 戰術層 |
| **控制論派** | Fowler/Böckeler | 前饋與反饋失衡 | 方法層 |
| **架構派** | Anthropic | 單體限制擴展 | 戰略層 |
| **懷疑派** | YDD | 在解錯問題 | 元層 |

### 洞見 3：Model-Harness 共演化是循環依賴

```
模型訓練時適配 harness → harness 為模型量身設計 → 模型升級 → harness 過時
         ↑                                                    │
         └────────────── 重新設計 harness ←──────────────────┘
```

**跨模型可攜的 harness 可能是幻覺。**

### 洞見 4：評估問題是阿基里斯之踵

背壓機制（lint、測試、型別檢查）只能捕獲**結構性和迴歸性錯誤**。「程式碼能編譯和通過測試，但做錯了事」→ 整個體系沒有可靠答案。Böckeler 直言：行為 Harness 是「房間裡的大象」。

### 洞見 5：人類角色漸次消解

| 文章 | 人類做什麼 |
|---|---|
| OpenAI 原文 | 設計環境 + 拆解任務 + 提示智能體 + 驗證結果 |
| Anthropic #4 | 寫 1-4 句提示詞 |
| Symphony | 任何能描述需求的人（PM、設計師、遠端工程師用手機） |

### 洞見 6：OpenAI 數據與 YDD 數據直接矛盾

| 來源 | 個體效率 | 組織效率 |
|---|---|---|
| OpenAI | 人均 3.5 PR/天 ↑ | ✅ 正向 |
| YDD/METR | 客觀慢 19% | ❌ 負向 |
| YDD/Faros | 個體 PR +98% | DORA 四指標無一改善 |

**啟示**：不應拿 OpenAI 數據做基準，應拿 YDD 數據做底線。

### 洞見 7：技術棧收斂 vs 分化

收斂/分化是雙層結構：**規範層（SPEC.md）會收斂，實作層會分化**。

### 洞見 8：Harness Engineering 本質上是 AI 輸出的供應鏈管理

```
製造業供應鏈              AI 程式碼供應鏈
工廠 = 模型              生產程式碼
質檢 = 背壓              攔截壞程式碼
倉庫 = Session           持久化中間產物
物流 = Harness           編排和路由
零售 = 交付              最終價值產出
```

**下一個高槓桿點不在模型端或約束端，而在評審自動化和整合編排上。**

---

## 6. Guides × Sensors 框架的五個張力（實務驗證）

基於 claude-code-harness v4.2 對 Böckeler 理論的端到端壓力測試：

| 張力 | 發現 | 對框架的衝擊 |
|---|---|---|
| **張力 1** | Advisor Strategy 是「條件觸發推理性傳感器」 | 框架需要新軸：控制的啟動策略（always-on / per-commit / conditional） |
| **張力 2** | guardrail 越嚴，前饋和反饋邊界越模糊 | PreToolUse hook 層同時承擔兩者，形成連續光譜 |
| **張力 3** | 行為 Harness 被繞過而非解決 | 是認識論問題而非工程問題；v4.2 策略是「把行為判斷高品質地交還給人類」 |
| **張力 4** | 95% 迭代精力在追上游變更 | Harness 是**對宿主運行時變化的被動追趕產物**，不是靜態設計產物 |
| **張力 5** | Harness 必然帶價值觀鎖定 | 任何成熟 harness 攜帶設計者的語言/審美/文化假設，非技術中立 |

---

## 7. 機械化自校驗系統（工程實踐亮點）

### 7.1 七層一致性檢查 (`check-consistency.sh`)

| 編號 | 檢查項 |
|---|---|
| C1 | `articles.md` 編號 1..N 連續 |
| C2 | N 與下游 4 處引用同步（README badge × 2 + tracker + AGENTS） |
| C3 | `concepts/` `thinking/` `feedback/` 實際 .md 數 = README 宣稱數 |
| C4 | `works/*-translation.md` 數量 = 所有翻譯計數宣稱 |
| C5 | README 結構樹的 concepts 子樹 = 實際檔案數 |
| C6 | `articles.md` 末尾排除計數 = C1 權威值 |
| C7 | 三脈絡 per-track 計數在 4 處下游宣稱一致 |

### 7.2 雙層守護

```
開發期：git config core.hooksPath .githooks  → pre-commit hook
合併門：.github/workflows/consistency.yml    → CI 兜底
```

本地 hook 是開發反饋，CI 是合併門——兩層獨立，本地未啟用 hook 不會繞過檢查。

---

## 8. REVIEW.md — 自我審計方法論

該倉庫建立了完整的 Review 流程，針對四類問題：

| 問題類型 | 說明 |
|---|---|
| **導航失真** | 根入口和子目錄說明是否一致 |
| **事實漂移** | README、AGENTS、索引中的數量/狀態是否一致 |
| **可復現性不足** | practice/ 中的實驗是否真能被復跑 |
| **機械化維護不足** | 哪些問題只能靠人工發現 |

**五步執行順序**：凍結權威來源 → 結構與導航審查 → 元資料一致性審查 → 內容約定審查 → 高頻問題變機械檢查。

---

## 9. N7 視角：與 Jasper Agent Hub 的映射與啟示

### 9.1 架構映射

| deusyu/harness-engineering 概念 | Jasper Agent Hub 對應 |
|---|---|
| 倉庫即記錄系統 | `.agents/knowledge/hermes-dev-guide.md` + KI 系統 |
| 地圖而非手冊 | `<RULE[hermes-agent.md]>` 動態知識庫載入協定 |
| 機械化執行 | N7 自癒迴圈 + Pre-flight Hooks |
| 智能體可讀性 | `user_rules` 中的 TAIDE 在地化防線 |
| 熵管理 | `.agent_memory/auto_memory/` 降落備忘錄 |
| 人類掌舵 | N1 總部中樞 → N3 分派模式 |
| Guides × Sensors | 缺乏（**最大差距**） |
| 約束即產品 | GSD workflow 的 PLAN.md 模式 |

### 9.2 關鍵啟示

**A. 我們已經在做但可以做得更好的**：

1. **品味傳播路徑**：我們的 `user_rules` 已經捕捉了品味（如「法遵」取代「合規」），但缺乏從「審查評論 → 規則更新」的自動化迴路。
2. **漸進式披露**：我們的 `.agents/knowledge/hermes-dev-guide.md` 是正確的入口設計，但可能需要精簡至 ~100 行。

**B. 我們缺乏且應該引入的**：

1. **Guides × Sensors 控制論框架**：我們目前的 N7 只有「反饋」（自癒迴圈），沒有系統化的「前饋」（引導器）。應設計計算性引導器（bootstrap 腳本）+ 推理性引導器（AGENTS.md 精簡版）的配對。
2. **七層一致性檢查**：我們的多文件系統（rules、knowledge、workflows）同樣面臨「事實漂移」風險，應建立等價的 `check-consistency` 腳本。
3. **Harness Gardening 意識**：每次模型升級（Gemini 版本更新），應壓測現有 rules 是否仍在承重。
4. **行為 Harness 的務實策略**：承認行為正確性不可全自動化，把人類批准做成強制 gate（對應我們的 N1 審批流程）。

**C. 該倉庫的局限性**：

1. 偏向理論與學習筆記，缺乏可直接拿來用的配置檔
2. 主要聚焦 Claude Code / Codex 生態，Gemini / Antigravity 的適用性需要我們自行轉譯
3. 中文內容使用簡體中文，需依 TAIDE 防線轉換為繁體中文與台灣法務語境

---

## 10. 關鍵數據點

| 指標 | 數據 |
|---|---|
| 團隊規模 | 3 人 → 7 人 |
| 時間跨度 | 5 個月 |
| 程式碼量 | ~100 萬行 |
| PR 數量 | ~1,500 個 |
| 人均日 PR | 3.5 個 |
| 單次運行時長 | 6+ 小時 |
| 效率估算 | 手工編寫的 ~1/10 時間 |
| Ralph Demo 成本 | 321 秒，$0.31 |

---

## 附錄 A：原始資料索引

| 資料 | 爬取來源 | 分析重點 |
|---|---|---|
| README.md | raw.githubusercontent.com | 專案結構、學習路線、Ralph 六條信條 |
| AGENTS.md | raw.githubusercontent.com | 倉庫導航入口、機械化檢查宣稱 |
| concepts/00-overview.md | raw.githubusercontent.com | 六大核心概念總覽、架構模型 |
| concepts/01-repo-as-source-of-truth.md | raw.githubusercontent.com | 知識位置矩陣、Symphony 延伸 |
| concepts/02-mechanical-enforcement.md | raw.githubusercontent.com | 兩類約束、lint=修復指令設計 |
| concepts/03-entropy-and-garbage-collection.md | raw.githubusercontent.com | 黃金規則、垃圾回收流程 |
| concepts/06-harness-definition.md | raw.githubusercontent.com | Agent=Model+Harness、控制論框架、Ashby 定律 |
| concepts/07-spec-as-product.md | raw.githubusercontent.com | SPEC.md/WORKFLOW.md 範式、多語言驗證 |
| thinking/cross-article-insights.md | raw.githubusercontent.com | 8 個跨文獻洞見、4 學派分析 |
| thinking/guides-sensors-meets-claude-code-harness.md | raw.githubusercontent.com | 5 個框架張力、v4.2 端到端剖析 |
| REVIEW.md | raw.githubusercontent.com | 自我審計方法論、5 步 Review 流程 |
| scripts/check-consistency.sh | raw.githubusercontent.com | 7 層一致性檢查 Shell 腳本 |

## 附錄 B：Ralph 六條信條與 Harness Engineering 映射

| Ralph 信條 | Harness Engineering 對應概念 |
|---|---|
| Fresh Context Is Reliability | 智能體可讀性 — 每次迭代重新讀取 |
| Backpressure Over Prescription | 機械化執行 — 不規定怎麼做，但門控拒絕壞結果 |
| The Plan Is Disposable | 熵管理 — 重新生成的成本只是一次 planning loop |
| Disk Is State, Git Is Memory | 倉庫即記錄系統 — 文件是交接機制 |
| Steer With Signals, Not Scripts | 人類掌舵 — 加路標，不加腳本 |
| Let Ralph Ralph | 智能體執行 — 坐在迴圈上，不坐在迴圈裡 |
