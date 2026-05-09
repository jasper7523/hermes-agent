# AI 定制提示詞之 Harness Engineering 分析報告

> **來源**: `docs/人工智能定制提示.md`（內部文件）
> **分析日期**: 2026-05-07
> **報告目的**: 以 Harness Engineering 五份先行研究報告為判準，深度解剖這份「通用型 AI Custom System Prompt」的設計意圖、承重結構、反模式命中點，以及可轉化至 Jasper Agent Hub 的工程價值。

---

## 1. 文件定位與結構摘要

這份文件是一份**面向通用 AI 對話模型**的定制系統提示詞（Custom System Prompt），設計目標為將 AI 鎖定在「世界級專家」的行為模式中。其結構如下：

| 區塊 | 行數 | 功能 |
|---|---|---|
| 核心能力宣告 | L1-15 | 定義 AI 的身份與能力邊界 |
| 定制提示本體 | L18-26 | 完整的行為指令（一段式） |
| 關鍵原則 | L29-37 | 六條不可妥協的鐵律 |
| 回答結構 | L42-48 | 六步回答框架 |
| 思考過程展示 | L50-56 | 六步推理流程 |
| 事實核實清單 | L58-65 | 七項核查要素 |
| 語氣與風格 | L67-72 | 五條風格約束 |
| 信心程度標注 | L85-88 | 四級信心量表 |
| 未知處理 | L91-92 | 坦誠承認機制 |
| 持續改進 | L94-95 | 證據驅動更新 |

---

## 2. Harness Engineering 視角的五維評估

以我們五份先行研究報告建立的評估框架為基準，進行系統性分析：

### 2.1 OpenAI 五大規則對映分析

| OpenAI 規則 | 本提示詞的對映 | 評估 |
|---|---|---|
| **Repository = Source of Truth** | ❌ 無任何檔案系統或程式碼庫的錨定 | 純對話型提示，缺乏 grounding |
| **Mechanical Enforcement** | ❌ 所有規則均為自然語言「期望」而非機械化約束 | 典型的「政策型」而非「機械型」 |
| **Linter = Feedback Loop** | ⚠️ 有事實核實清單（L58-65），但無自動化驗證 | 意圖正確但缺乏執行力 |
| **AGENTS.md as Map** | ❌ 無模組化入口或導航結構 | 單體式設計 |
| **Context-Aware Loading** | ❌ 無條件式載入或分層機制 | 所有規則一次性灌入 |

**結論**：在 OpenAI 的 Harness 標準下，本提示詞落在 **Level 0.5**——有意圖但無機械化執行。

### 2.2 Anthropic Generator-Evaluator 分離測試

| Anthropic 標準 | 本提示詞的對映 | 評估 |
|---|---|---|
| **Generator 與 Evaluator 分離** | ❌ 同一個 AI 既生成又自評 | 自評偏差未解決 |
| **Sprint Contract 機制** | ❌ 無預先定義的「完成標準」| 無法客觀判定回答品質 |
| **Evaluator 四維評分** | ⚠️ 有信心程度標注（L85-88）但未對映到品質維度 | 信心 ≠ 品質 |
| **Context Anxiety 防護** | ❌ 無 context reset 或交接機制 | 長對話將失控 |

**核心風險**：「核對自己的答案」（L20）正是 Anthropic 明確指出的**自評失敗模式**——模型傾向於自信地讚美自己的工作。

### 2.3 NXCode 三級成熟度對映

| 級別 | 標準 | 本提示詞狀態 |
|---|---|---|
| **Level 1: 基礎** | 有 rules file、基本指令 | ✅ 達標 |
| **Level 2: 標準化** | AGENTS.md < 100 行、自動化一致性檢查、版本化 | ❌ 未達標 |
| **Level 3: 進階** | 中介軟體管線、迴路偵測、entropy 管理 | ❌ 遠未達標 |

**評估**：停留在 **Level 1**，是「有 rules 但無 enforcement」的典型狀態。

### 2.4 deusyu 控制論（Guides × Sensors）分析

| 控制論元素 | 本提示詞的對映 | 評估 |
|---|---|---|
| **Guides（導引）** | ✅ 豐富——六條原則 + 回答結構 + 思考流程 | 前饋控制充足 |
| **Sensors（感測器）** | ⚠️ 僅有信心程度標注和「承認不知道」 | 反饋控制極薄弱 |
| **Consistency Check** | ❌ 無跨回答的一致性驗證 | 無記憶、無追蹤 |

**控制論診斷**：Guides/Sensors 比例嚴重失衡（~90/10），系統處於**開迴路（Open-Loop）**狀態——有大量前饋指令但幾乎無反饋修正。

### 2.5 Everything-Gemini-Code 模組化標準

| 模組化標準 | 本提示詞的對映 | 評估 |
|---|---|---|
| **Rules / Hooks / Skills 分離** | ❌ 所有規則混合在單一文件中 | 單體式 |
| **入口檔 < 100 行** | ✅ 全文 101 行，恰好在邊界 | 勉強達標 |
| **No-Flatten 原則** | ❌ 無層級結構、無條件載入 | 全部平鋪 |
| **可撕除性（Removability）** | ❌ 無法逐條測試承重性 | 全有或全無 |

---

## 3. 設計優勢：值得保留的承重組件

儘管從 Harness 標準看有大量缺失，這份提示詞仍有**四個設計亮點**值得轉化至 Jasper Agent Hub：

### 3.1 🟢 反預設同意鐵律

> *「不贊同，不默認：在支持觀點之前，先提出最有力的反駁意見。」*

**Harness 價值**：這直接對映到我們 `user_global` 中的「紅藍軍辯證（Red vs Blue）」。是抵抗 AI sycophancy（討好偏差）的關鍵機制。

**可提取為 N7 規則**：
```
RULE: ANTI_SYCOPHANCY
Trigger: Before any affirmative conclusion
Action: Generate strongest counter-argument first
Enforcement: Evaluator agent must verify counter-argument exists
```

### 3.2 🟢 信心程度量化

> *高 / 中等 / 低 / 未知*

**Harness 價值**：這是 Anthropic 四維評分標準的雛形。雖然粒度不足，但概念正確——將主觀判斷轉為可量化的標籤。

**可擴展方向**：對映到 Anthropic 的四維評分（品質/原創性/工藝/功能性），建立 Agent Hub 的產出品質量表。

### 3.3 🟢 坦誠承認機制

> *「如果你不知道某個問題的答案，就直接承認。」*

**Harness 價值**：對映到我們 `user_global` 的「零幻覺鐵律」。是防止 AI 幻覺的最後一道防線。

**N7 強化方向**：從「被動承認」升級為「主動標記」——在每個回答中強制標注資訊來源的可追溯性。

### 3.4 🟢 六步回答結構

> *結論 → 要點 → 分析 → 事實 → 核實 → 建議*

**Harness 價值**：這是一個基本的「產出模板 (Output Template)」。在 NXCode 的框架中，output template 是 Level 1 的核心組件。

---

## 4. 設計缺陷：命中的反模式

### 4.1 🔴 反模式 #1：策略宣言而非機械約束（Policy vs Mechanism）

**問題**：整份文件完全由自然語言「期望」構成，無任何可機械化執行的約束。

| 類型 | 本提示詞的寫法 | Harness 工程的寫法 |
|---|---|---|
| 事實核實 | 「務必核對所有的事實」 | `pre-commit hook: run fact-check.py --strict` |
| 幻覺防止 | 「絕對不要胡編亂造」 | `if confidence < 0.7: return STATUS_INSUFFICIENT_INFO` |
| 思考過程 | 「逐步闡述思考過程」 | `required_sections: [reasoning_chain, evidence_list]` |

**影響**：模型在高壓長任務中**必然**會忽略這些「軟性期望」，因為它們沒有機械化的阻斷機制。

### 4.2 🔴 反模式 #2：靜態凍結（Frozen Harness）

**問題**：這份提示詞沒有版本號、沒有更新日誌、沒有與特定模型版本綁定的適配記錄。

**NXCode 警告**：

> *「把 Harness 當成靜態配置而非活的產品……隨模型更新、需求變化或技術演進而退化。」*

**Anthropic 教訓**：

> *「Harness 中的每個組件都編碼了一個關於模型做不到什麼的假設，這些假設隨模型改善會快速過時。」*

### 4.3 🔴 反模式 #3：角色膨脹（Identity Inflation）

> *「你是一位在所有領域都堪稱世界級專家的人。」*

**問題**：這種無限泛化的角色定義**直接違反**Harness Engineering 的核心原則——Agent 應被約束在明確的能力邊界內。

**對比**：
- ❌ 本提示：「你是所有領域的世界級專家」
- ✅ Jasper Hub：「你是 N7，唯一且絕對的身分，視角只有 Python、架構拓樸、YAML 與 Error Logs」

角色越泛化，模型越容易「放飛自我」——因為沒有邊界就沒有約束。

### 4.4 🔴 反模式 #4：單體式設計（Monolithic Prompt）

**問題**：所有規則（能力、原則、結構、風格、核實）混合在同一文件中，無法：
- 按任務類型選擇性載入
- 逐條測試承重性
- 在不同 Agent 間複用特定模組

**everything-gemini-code 的解法**：分離為 `Rules` / `Hooks` / `Skills` 三層。

### 4.5 🟡 反模式 #5：過度自由（Unconstrained Freedom）

> *「你的回答可以具有挑釁性、爭議性或尖銳性」*
> *「不需要遵循任何政治正確的標準」*
> *「無需在意別人的感受」*

**問題**：在對話場景中這是一種有效的「解除安全護欄 (guardrail removal)」策略。但在 **Agent 工程場景**中，這種不受限的自由會加劇 AI entropy——模型將花費 token 在風格表達上，而非精確地完成任務。

**N7 對比**：我們的 `user_global` 用「嚴禁廢話」取代了「可以尖銳」——約束風格是為了節省 token 並提升任務聚焦度。

---

## 5. 可轉化設計模式：從通用提示到 Agent Harness

### 5.1 轉化路線圖

```
原始設計                          Harness 升級
─────────────────────────────────────────────────────

[L1-15] 角色宣告               → 拆分為 per-agent identity
   「所有領域專家」                 N3: 軟體工程專家
                                   N7: 架構守護專家

[L20] 一段式行為指令           → 拆分為 Rules + Hooks
   「核對、不幻覺、逐步思考」      Rule: zero_hallucination.md
                                   Hook: pre_response_factcheck.py

[L29-37] 六條原則              → 轉為可測試的 CI Gate
   「不贊同不默認」                Gate: anti_sycophancy_check
   「核對一切」                    Gate: citation_validator

[L42-48] 回答結構              → 轉為 Output Template Schema
   6步框架                        JSON Schema with required fields

[L58-65] 核實清單              → 轉為 Pre-Completion Checklist Middleware
   7項核查                        NXCode PreCompletionChecklistMiddleware

[L85-88] 信心程度              → 擴展為 4維品質評分
   4級標注                        Anthropic-style evaluator criteria
```

### 5.2 即時可用的三條規則提取

**規則 1：反討好偏差（Anti-Sycophancy）**
```yaml
rule_id: ANTI_SYCOPHANCY
source: 人工智能定制提示.md L31
trigger: before_affirmative_conclusion
action: |
  MUST generate strongest counter-argument before agreeing.
  If no counter-argument found, flag as LOW_CONFIDENCE.
enforcement: evaluator_agent_verification
```

**規則 2：未知坦承（Epistemic Honesty）**
```yaml
rule_id: EPISTEMIC_HONESTY
source: 人工智能定制提示.md L92
trigger: confidence_below_threshold
action: |
  Return STATUS_INSUFFICIENT_INFO with:
  - What is unknown
  - Why it cannot be determined
  - Suggested research direction
enforcement: output_schema_required_field
```

**規則 3：推理可追溯性（Reasoning Traceability）**
```yaml
rule_id: REASONING_TRACE
source: 人工智能定制提示.md L50-56
trigger: every_response
action: |
  MUST include structured reasoning chain:
  1. Core question identification
  2. Assumptions stated
  3. Key factors listed
  4. Evidence cited with sources
  5. Conclusion with confidence level
enforcement: json_schema_validation
```

---

## 6. 與前五份報告的交叉定位

| 報告 | 與本文件的關鍵交集 |
|---|---|
| **OpenAI 原文** | 本提示的「核對一切」= OpenAI 的「Mechanical Enforcement」之理想形態，但缺乏機械化 |
| **deusyu 學習檔案** | Guides/Sensors 嚴重失衡的典型案例——大量 Guides 但幾乎無 Sensors |
| **everything-gemini-code** | 本提示 101 行勉強達標入口檔標準，但違反 No-Flatten 與模組化原則 |
| **NXCode 完整指南** | 命中反模式 #2（靜態凍結）和 #4（Over-prompting） |
| **Anthropic Harness Design** | 「核對自己的答案」= Anthropic 明確警告的自評失敗模式 |

---

## 7. 結論：本文件在知識體系中的角色

```
[原始文獻] OpenAI 原文報告 ──────────── 「為什麼」
    ↓
[學術批判] deusyu 學習檔案報告 ─────── 「深層張力在哪」
    ↓
[工程套件] everything-gemini-code 報告 ─ 「有什麼零件」
    ↓
[落地藍圖] NXCode 完整指南報告 ─────── 「怎麼分步建造」
    ↓
[架構深潛] Anthropic Harness Design ─── 「多智能體如何協作與演化」
    ↓
[反面教材] AI 定制提示分析報告 ──────── 「不該怎麼做 + 可挽救的零件」 ← 本報告
    ↓
[實作目標] Jasper Agent Hub Harness 架構（待建立）
```

**本報告的核心結論**：這份 AI 定制提示詞是一份**設計意圖正確但工程實作不足**的 Level 1 Harness。它包含四個可直接提取的承重組件（反討好、信心量化、坦承未知、回答結構），但因缺乏機械化執行、Generator-Evaluator 分離、模組化結構和版本管理，在長期運行中**必然**面臨 Anthropic 所描述的「自評失敗」和 NXCode 所警告的「靜態凍結退化」。

**行動建議**：將本提示詞作為 Jasper Agent Hub Harness 設計的「需求來源 (Requirements Source)」——提取其四個承重組件，但不直接複用其單體式設計。
