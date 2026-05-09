# NXCode「Harness Engineering 完整指南」研究報告

> **來源**: [NXCode: Harness Engineering — The Complete Guide to Building Systems That Make AI Agents Actually Work (2026)](http://nxcode.io/resources/news/harness-engineering-complete-guide-ai-agent-codex-2026)
> **分析日期**: 2026-05-07
> **報告目的**: 萃取該文的三級成熟度模型、五大反模式、LangChain 中介軟體架構等實作框架，補全 Jasper Agent Hub 的 Harness 落地路線圖。

---

## 1. 文章定位

NXCode 這篇文章是 Harness Engineering 領域目前最完整的「實務操作手冊」。相對於 OpenAI 原文的實驗報告性質、deusyu/harness-engineering 的學術批判性質，**本文的獨特價值在於：**

| 面向 | 其他來源 | NXCode 獨特貢獻 |
|---|---|---|
| 理論框架 | 有 | 補充 Martin Fowler 的精確引語 |
| 實作層級模型 | 無 | ✅ 三級成熟度模型（個人→團隊→組織） |
| 反模式 | 零星提及 | ✅ 五大系統性反模式 |
| 中介軟體架構 | 概念級 | ✅ LangChain 的可組合式中介軟體管線圖 |
| 跨供應商策略 | 未提及 | ✅ Multi-provider harness design |
| 實務時間估算 | 無 | ✅ 每級建置時間和預期影響 |

---

## 2. 核心命題

### 2.1 The Model Is Commodity. The Harness Is Moat.

> *模型是大宗商品。Harness 才是護城河。*

NXCode 用一句話點破整個範式的經濟學本質：**模型品質正在快速收斂**（GPT 領先 → Claude 追上 → Gemini 跟隨），而 Harness 是每個團隊必須自己打造的資產。

### 2.2 馬匹比喻（正式化）

| 組件 | 比喻 | 說明 |
|---|---|---|
| 🐎 模型 | 馬匹 | 強大、快速，但自己不知道要去哪 |
| ⚙️ Harness | 韁繩 + 馬鞍 + 圍欄 | 約束、護欄、反饋迴路，引導馬匹的力量往正確方向走 |
| 🧑 工程師 | 騎手 | 提供方向，不負責跑步 |

> *「沒有 harness 的 AI 智能體，就是在空曠草原上的純種馬。快、令人印象深刻、但完全無法做任何有用的事。」*

### 2.3 正式定義（四面向）

Harness Engineering 是設計和實作以下四類系統的學科：

| # | 面向 | 功能 |
|---|---|---|
| 1 | **約束** (Constrain) | 限制智能體能做什麼（架構邊界、依賴規則） |
| 2 | **告知** (Inform) | 告訴智能體應該做什麼（上下文工程、文件） |
| 3 | **驗證** (Verify) | 驗證智能體做對了嗎（測試、linting、CI 驗證） |
| 4 | **糾正** (Correct) | 智能體做錯時糾正它（反饋迴路、自我修復機制） |

**Fowler 的精確引語**：

> *「The tooling and practices we can use to keep AI agents in check.」*
> （讓 AI 智能體保持受控的工具和實踐。）

NXCode 補充：好的 Harness 讓智能體**更有能力**，而不僅是更受控。

---

## 3. 三大支柱（OpenAI 框架細化）

### 3.1 Context Engineering（情境工程）

分為兩類：

**靜態上下文**：
- 倉庫內文件（架構規格、API 契約、風格指南）
- `AGENTS.md` / `CLAUDE.md`（專案規則編碼）
- 交叉連結的設計文件（由 linter 驗證）

**動態上下文**：
- 可觀測性數據（日誌、指標、追蹤）供智能體存取
- 智能體啟動時的目錄結構映射
- CI/CD 管線狀態和測試結果

**鐵律**：

> *從智能體的視角看，任何它在上下文中無法存取的東西都不存在。Google Docs、Slack 對話串或人腦中的知識對系統不可見。倉庫必須是唯一真相來源。*

### 3.2 Architectural Constraints（架構約束）

**依賴分層**：
```
Types → Config → Repo → Service → Runtime → UI
```
每一層只能 import 其左側的層。**不是建議——由結構測試和 CI 驗證強制執行。**

**約束執行工具矩陣**：

| 工具類型 | 說明 | 範例 |
|---|---|---|
| **確定性 linter** | 自動標記違規的自訂規則 | ESLint custom rules、Ruff custom checkers |
| **LLM 審計器** | 審查其他智能體程式碼的架構合規性的智能體 | AI code reviewer agent |
| **結構測試** | 類似 ArchUnit，但針對 AI 生成的程式碼 | 依賴方向測試 |
| **Pre-commit hooks** | 任何程式碼提交前的自動檢查 | husky + lint-staged |

**約束的悖論**（再次確認）：

> *「約束解空間使智能體更有生產力，而非更少。當智能體可以生成任何東西，它浪費 token 探索死胡同。當 harness 定義了清晰邊界，智能體更快收斂到正確解。」*

### 3.3 Entropy Management（熵管理 / 垃圾回收）

**問題類型**：文件偏離現實、命名約定分歧、死程式碼累積。

**四類清理智能體**：

| 智能體類型 | 功能 |
|---|---|
| 文件一致性智能體 | 驗證文件是否與當前程式碼匹配 |
| 約束違規掃描器 | 找出早期檢查遺漏的程式碼 |
| 模式強制智能體 | 識別並修復偏離既定模式的程式碼 |
| 依賴審計器 | 追蹤和解決循環或不必要的依賴 |

**運行策略**：排程運行（每日、每週）或由特定事件觸發。

---

## 4. 三級成熟度模型（核心獨創貢獻）

這是本文最高價值的框架——為不同規模的團隊提供分層落地路線。

### Level 1：Basic Harness（個人開發者）

**適用場景**：使用 Claude Code、Cursor 或 Codex 的個人專案

| 組件 | 說明 |
|---|---|
| `CLAUDE.md` / `.cursorrules` | 專案約定檔 |
| Pre-commit hooks | linting 和格式化 |
| 測試套件 | 智能體可自行運行以自我驗證 |
| 清晰目錄結構 | 一致的命名 |

**建置時間**：1-2 小時
**影響**：防止最常見的智能體錯誤

### Level 2：Team Harness（小型團隊 3-10 人）

**在 Level 1 基礎上增加**：

| 組件 | 說明 |
|---|---|
| `AGENTS.md` | 團隊級約定 |
| CI 強制架構約束 | 不只建議，而是阻斷 |
| 共享 prompt 模板 | 常見任務的標準化提示詞 |
| Documentation-as-code | 由 linter 驗證的文件 |
| 智能體生成 PR 的專屬審查清單 | AI 程式碼的失敗模式與人類不同 |

**建置時間**：1-2 天
**影響**：跨團隊的一致智能體行為

### Level 3：Production Harness（工程組織）

**在 Level 2 基礎上增加**：

| 組件 | 說明 |
|---|---|
| 自訂中介軟體層 | 迴圈偵測、推理優化 |
| 可觀測性整合 | 智能體讀取日誌和指標 |
| 排程熵管理智能體 | 自動清理 |
| Harness 版本控制 + A/B 測試 | 測試不同 harness 配置 |
| 智能體績效監控儀表板 | 追蹤成功率 |
| 升級政策 | 智能體卡住時的處理策略 |

**建置時間**：1-2 週
**影響**：智能體作為自主貢獻者運作

---

## 5. LangChain 中介軟體架構（獨特發現）

NXCode 提供了 LangChain 的可組合中介軟體管線圖，這在其他來源中沒有被完整呈現：

```
Agent Request
    │
    ▼
┌─────────────────────────────┐
│ LocalContextMiddleware      │ ← 映射程式碼庫
├─────────────────────────────┤
│ LoopDetectionMiddleware     │ ← 防止重複
├─────────────────────────────┤
│ ReasoningSandwichMiddleware  │ ← 優化計算
├─────────────────────────────┤
│ PreCompletionChecklistMW    │ ← 強制驗證
└─────────────────────────────┘
    │
    ▼
Agent Response
```

**設計原則**：每個中介軟體層添加特定能力，不修改核心智能體邏輯。模組化使 Harness **可測試且可演化**。

---

## 6. 五大反模式

### 反模式 1：過度工程化控制流

> *「如果你過度工程化控制流，下一次模型更新就會破壞你的系統。」*

**解法**：Build **rippable**（可撕除的）harness。模型能力提升時，應能隨時移除「聰明」邏輯。

### 反模式 2：把 Harness 當作靜態物

> Harness 需要隨模型演化。新模型版本改善推理能力時，你的推理優化中介軟體可能變成反效果。

**解法**：每次主要模型更新時，審查並更新 Harness 組件。

### 反模式 3：忽略文件層

> 最有影響力的 Harness 改善往往最簡單：**更好的文件**。

**解法**：如果 `AGENTS.md` 模糊，智能體的輸出就模糊。投資精確、機器可讀的文件。

### 反模式 4：沒有反饋迴路

> 沒有反饋的 Harness 是**牢籠**，不是**導軌**。

**解法**：
- 任務完成前的自我驗證步驟
- 測試執行作為智能體工作流的一部分
- 按任務類型追蹤智能體成功率的指標

### 反模式 5：僅人類可讀的文件

> 如果架構決策活在人腦或智能體無法存取的 Confluence 頁面中，Harness 就有缺口。

**解法**：智能體需要的一切必須在倉庫中。

---

## 7. Stripe Minions 系統（補充細節）

NXCode 補充了 Stripe 內部系統的五步工作流：

```
步驟 1：開發者在 Slack 發布任務
步驟 2：Minion 撰寫程式碼
步驟 3：Minion 通過 CI
步驟 4：Minion 開 PR
步驟 5：人類審查並合併
```

**關鍵**：步驟 1 和步驟 5 之間**零開發者互動**。Harness 處理所有事情——測試執行、CI 驗證、風格合規、文件更新。

每週產出：**超過 1,000 個合併的 PR**。

---

## 8. 跨供應商 Harness 設計（關鍵實踐洞察）

NXCode 分享了他們在多智能體系統（Claude Code、Codex、Cursor）中的四個核心模式：

| # | 模式 | 說明 |
|---|---|---|
| 1 | **Repository-first documentation** | 每個架構決策、命名約定、部署流程都在倉庫中。沒有東西活在 Slack 或 Google Docs |
| 2 | **Incremental constraint building** | 從基本 linting 開始，隨模式出現再加架構約束。不要試圖一開始就設計完美 Harness |
| 3 | **Agent-specific review checklists** | AI 生成的程式碼有不同的失敗模式（過度抽象、不必要的錯誤處理、文件漂移） |
| 4 | **Multi-provider harness design** | Harness 與 Claude、GPT、Gemini 模型都能配合。供應商無關設計 = 不需重建就能切換模型 |

**第 4 點對我們尤其關鍵**：Jasper Agent Hub 底層使用 Gemini，但 Harness 設計不應鎖定於單一模型供應商。

---

## 9. 工程師角色演變

NXCode 識別出五個新的核心技能：

| # | 技能 | 說明 |
|---|---|---|
| 1 | **系統思維** | 理解約束、反饋迴路和文件如何交互 |
| 2 | **架構設計** | 定義可執行且有生產力的邊界 |
| 3 | **規格寫作** | 精確表達意圖，使智能體能執行 |
| 4 | **可觀測性** | 建構揭示智能體行為模式的監控 |
| 5 | **迭代速度** | 快速測試和優化 Harness 配置 |

---

## 10. N7 視角：Jasper Agent Hub 成熟度評估

根據 NXCode 的三級模型，評估我們目前的狀態：

### 10.1 當前成熟度定位

| Level | 組件 | 我們的狀態 | 評估 |
|---|---|---|---|
| **L1** | Context files | ✅ `user_rules` + `hermes-dev-guide.md` | 已具備 |
| **L1** | Pre-commit hooks | ❌ 無 | **缺失** |
| **L1** | 測試套件 | ⚠️ 部分（GSD 測試） | 不完整 |
| **L1** | 清晰目錄結構 | ✅ `.agents/` 結構 | 已具備 |
| **L2** | AGENTS.md | ⚠️ 有 `user_rules` 但非標準 `AGENTS.md` 格式 | 需標準化 |
| **L2** | CI 強制架構約束 | ❌ 無 | **缺失** |
| **L2** | 共享 prompt 模板 | ✅ GSD skills | 已具備 |
| **L2** | Agent-specific review | ❌ 無專屬清單 | **缺失** |
| **L3** | 中介軟體層 | ❌ 無 | **缺失** |
| **L3** | 排程熵管理 | ❌ 無 | **缺失** |
| **L3** | Harness 版控 + A/B | ❌ 無 | **缺失** |
| **L3** | 升級政策 | ⚠️ N7 有自癒但無明確升級閾值 | 不完整 |

**結論**：我們目前處於 **Level 1 ～ Level 2 之間**，具備基本上下文檔案和技能模板，但缺乏機械化執行（linter/CI gate）和自動化反饋迴路。

### 10.2 五大反模式自我檢查

| 反模式 | 我們是否命中？ | 說明 |
|---|---|---|
| 1. 過度工程化控制流 | ⚠️ 輕微 | `user_rules` 較複雜但尚可管理 |
| 2. 把 Harness 當靜態 | 🔴 **命中** | 從未因 Gemini 版本升級而審查 rules |
| 3. 忽略文件層 | ⚠️ 輕微 | `hermes-dev-guide.md` 存在但可能過長 |
| 4. 沒有反饋迴路 | 🔴 **命中** | N7 有自癒但沒有系統性反饋指標 |
| 5. 僅人類可讀文件 | ⚠️ 輕微 | KI 系統對智能體可見但格式非最佳 |

### 10.3 建議的升級路線圖

**Phase 1：鞏固 Level 1（1-2 小時）**
- [ ] 建立 `.githooks/pre-commit` 執行基本 linting
- [ ] 確保所有 user_rules 有 `## Fix:` 修復指令

**Phase 2：達成 Level 2（1-2 天）**
- [ ] 將 `user_rules` 重構為標準 `AGENTS.md` 格式入口
- [ ] 建立 `scripts/check-agent-rules-consistency.sh`
- [ ] 建立 AI 生成程式碼的專屬審查清單

**Phase 3：邁向 Level 3（1-2 週）**
- [ ] 設計中介軟體層（至少 LoopDetection + PreCompletionChecklist）
- [ ] 建立排程熵管理（每日自動掃描 rules 一致性）
- [ ] 建立 Harness 版本控制（隨 Gemini 版本更新同步審查）

---

## 11. 與前三份報告的交叉定位

| 報告 | 角色 | 本報告的增量價值 |
|---|---|---|
| `OpenAI_Harness_Engineering_Original_Research_Report.md` | 第一手原始文獻 | 本報告補充了 OpenAI 沒有的成熟度模型和反模式 |
| `Harness_Engineering_Learning_Archive_Research_Report.md` | 學術批判分析 | 本報告從「實務操作手冊」角度補全理論到落地的差距 |
| `Everything_Gemini_Code_Research_Report.md` | 工程套件拆解 | 本報告提供了 LangChain 中介軟體架構的具體設計 |
| **本報告** | **實務落地藍圖** | 三級成熟度 + 五大反模式 + 跨供應商策略 |

四份報告構成完整知識體系：
```
[原始文獻] OpenAI 原文報告 ─────────── 「為什麼」
    ↓
[學術批判] deusyu 學習檔案報告 ──────── 「深層張力在哪」
    ↓
[工程套件] everything-gemini-code 報告 ─ 「有什麼零件」
    ↓
[落地藍圖] NXCode 完整指南報告 ──────── 「怎麼分步建造」 ← 本報告
    ↓
[實作目標] Jasper Agent Hub Harness 架構（待建立）
```

---

## 附錄：原始資料索引

| 資料 | 來源 | 內容焦點 |
|---|---|---|
| NXCode 完整指南 | nxcode.io/resources/news/harness-engineering-... | 三級成熟度、五大反模式、中介軟體架構 |
| Stripe Minions 描述 | 同上，交叉引用 | 五步工作流、每週 1,000+ PR |
| LangChain 中介軟體 | 同上，交叉引用 | 四層可組合管線 |
| NXCode 實務經驗 | 同上 | 四個核心模式、跨供應商設計 |
