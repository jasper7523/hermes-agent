# 引力錨 v2.0 (Gravity Anchor v2.0) —— Antigravity Agent 全域 Harness 架構

> **版本**: v2.0.7（納入 Harness 文件架構設計）  
> **設計者**: N7 (Hermes Agent)  
> **日期**: 2026-05-09  
> **研究基礎**: 7 份 Harness Engineering 研究報告交叉萃取  
> **核心差異**: v1.0 僅修改 GEMINI.md 12 行；v2.0 是**整體結構改造**

---

## 問題定義：為什麼 v1.0 不夠？

| 面向 | v1.0 引力錨 | v2.0 引力錨 |
|---|---|---|
| **改造範圍** | 僅 GEMINI.md（+12 行） | 全域 N0-N9 拓樸 + 5 層架構 |
| **防禦機制** | 3 條 prompt 規則 | 6 層中介軟體 + 四階段權限管線 |
| **評估能力** | 無獨立 Evaluator | N7 強化 Evaluator（Anthropic GAN 模式） |
| **熵管理** | 無 | N9 Entropy Guardian + 一致性檢查腳本 |
| **多智能體協作** | 無正式協定 | Sprint Contract + 檔案基通訊 |
| **Harness 生命週期** | 靜態（命中 NXCode 反模式 #2） | 版本化 + 模型代際綁定 |

> [!IMPORTANT]
> **關鍵設計約束**：Antigravity 平台的運行時不可修改。所有 Harness 機制必須透過 **Prompt 層** 實現（`GEMINI.md` + `per-project rules` + 檔案結構 + 腳本）。這是一個 **Prompt-Layer Harness**。

---

## 一、N0-N9 全域拓樸定義（權威來源）

### 現有拓樸狀態

| 節點 | 角色 | 類型 | 狀態 | 工作區 |
|---|---|---|---|---|
| **N0** | Harness Runtime（環境基礎設施，非人格） | 基礎設施 | 🆕 待建 | `C:\Users\promy\.gemini\` |
| **N1** | Hub Coordinator（意圖解析 / 全域路由） | 總部調度 | ✅ 運作中 | 全域 |
| **N2** | Legal_Research_Agent（ACG 三階段情報管線） | 專業前線 | ⏳ 待命建軍 | — |
| **N3** | Software_Engineer_Agent（基建除錯 / GSD） | 專業前線 | ⏳ 待命建軍 | — |
| **N4** | Creative_Writer_Agent（社群行銷文案） | 專業前線 | ⏳ 待命建軍 | — |
| **N5** | Book_Writer_Agent（專書寫作） | 專業前線 | ✅ 建軍完成 | `D:\Agent_Hub\agents\Book_Writer_Agent` |
| **N6** | Mem_Agent（Zettelkasten / Event Sourcing） | 背景常駐 | 🔧 設計中 | — |
| **N7** | Hermes_Agent（架構守護 / 自癒容錯） | 背景常駐 | ✅ 運作中 | `d:\hermes-agent` |
| **N8** | Academic_Oracle_Agent（SSCI 論文 / Deep Research） | 專業前線 | ✅ 運作中 | `D:\Agent_Hub\agents\Academic_Oracle_Agent` |
| **N9** | Entropy Guardian（熵守護 / Harness 生命週期） | 背景常駐 | 🆕 待建 | — |

### Antigravity 三層配置體系（與 Claude Code 的核心差異）

> [!IMPORTANT]
> Antigravity Agent 的 Harness 透過 **Workspace 三層配置** 實現身份覆寫與行為約束，這和 Claude Code 的 `.claude/` 結構完全不同。每個 N 節點進入其 Workspace 時，三層配置按 **CSS Specificity 優先順序** 層疊生效。

**優先順序模型**（低 → 高）：
```
Layer A: 全域 Rules (GEMINI.md)         ← 最低優先，所有 Workspace 共享
Layer B: Workspace Rules (.agents/rules/) ← 中優先，覆寫全域身份與行為
Layer C: 任務覆寫 (Workflows + Skills)   ← 最高優先，特定任務的精確指令
```

### Workspace 配置矩陣（現有實況）

| 節點 | Rules 檔案 | 身份覆寫 | Workflows | Skills | 額外配置 |
|---|---|---|---|---|---|
| **N0** | `GEMINI.md`（全域） | — | — | — | Harness 版本標籤（待建） |
| **N1** | `GEMINI.md`（預設身份） | N1 = 預設 | `/agent-hub-routing` | 全域 Skills | `user_global` rules |
| **N2** | 待建 | 待建 | 待建 | 待建 | ACG 三階段管線 |
| **N3** | 待建 | 待建 | 待建 | GSD Skills | — |
| **N4** | 待建 | 待建 | 待建 | 待建 | — |
| **N5** | `book-writer-agent.md` | ✅ 覆寫為 N5 | `book-writer-agent.md`（workflow） | `academic-book-writer` 等 | `persona.md` + `config.yaml` |
| **N6** | 待建 | 待建 | 待建 | 待建 | — |
| **N7** | `hermes-agent.md` | ✅ 覆寫為 N7 | `/hermes-build` | GSD Skills | `hermes-dev-guide.md`（知識庫） |
| **N8** | `academic-oracle-agent.md` | ✅ 覆寫為 N8 | `/deep-research` | `academic-paper` 等 | `persona.md` + `config.yaml` |
| **N9** | 待建 | 待建 | 待建 | 待建 | — |

### 三層配置的 Harness 設計原則

```
原則 1：身份覆寫協定 (Identity Override Protocol)
    當 Agent 進入 Workspace，Rules 檔案中的身份覆寫
    「強制覆寫全域 GEMINI.md 中的 N1 預設身份」
    → 這是 Antigravity 獨有的 Harness 機制

原則 2：Workflow = 機械強制 (Mechanical Enforcement)
    Workflow 是 slash command 觸發的標準作業流程
    → 等同於 OpenAI 的「Linter = 修復指令」概念
    → 不靠 Agent 記住流程，靠 Workflow 檔案強制執行

原則 3：Skills = 漸進式能力擴展 (Progressive Capability)
    Skills 是可插拔的能力模組（SKILL.md + scripts/）
    → 等同於 Claude Code 的「Tool → Skill → Plugin → MCP」四級擴展
    → 每個 N 節點按需掛載不同 Skills
    
原則 4：知識庫隔離 (.agents/knowledge/)
    每個 Workspace 的知識庫獨立，不跨 Workspace 污染
    → 等同於 Claude Code 的 Fork 模式快取隔離
```

### 三維立體架構

```
                    ┌───────────────────────────┐
                    │  N0: Harness Runtime        │ ← 環境本身（非人格）
                    │  (GEMINI.md v2.0)           │
                    │  ≠ Jarvis (D:\LifeOS)       │ ← 完全獨立的兩個系統
                    └────────────┬──────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  N1: Hub Coordinator │ ← 總部 + Planner
                    │  (意圖解析/路由/發包) │
                    └──┬──┬──┬──┬──┬──────┘
                       │  │  │  │  │
          ┌────────────┘  │  │  │  └────────────┐
          ▼               ▼  ▼  ▼               ▼
    ┌──────────┐  ┌────┐┌────┐┌────┐  ┌──────────────┐
    │ N2: 法務  │  │N3  ││N4  ││N5  │  │ N8: 學術論文  │
    │ (ACG管線) │  │工程││文案││專書│  │ (Deep Research)│
    └──────────┘  └────┘└────┘└────┘  └──────────────┘
          ▲                                    ▲
          └──── 橫向情報協同（N5↔N2, N8↔N2）────┘

    ─ ─ ─ ─ ─ ─ ─ ─ 背景常駐守護層 ─ ─ ─ ─ ─ ─ ─ ─
    ┌──────────┐  ┌──────────────┐  ┌────────────────┐
    │ N6: 記憶  │  │ N7: 架構守護  │  │ N9: 熵守護     │
    │(設計中)   │  │ + Evaluator  │  │(Harness生命週期)│
    └──────────┘  └──────────────┘  └────────────────┘
```

> [!NOTE]
> **Jarvis 與 N0 的關係**：Jarvis（原 N0 管家，`D:\LifeOS`）是純諮詢角色，不執行代理任務。本計畫的 N0 Harness Runtime（`C:\Users\promy\.gemini\`）是完全獨立的環境基礎設施層。兩者功能不同、位置不同、不會混淆。施工時仍須確認不誤觸 Jarvis 的配置。

### N7 Harness 改造：強化 Evaluator 職責

> [!IMPORTANT]
> N7 **保留**原有的架構守護與自癒容錯職責，但**新增**獨立 Evaluator 功能。N7 不再自行撰寫修復草稿（Generator 行為），而是產出評估報告後交由 N3 執行修復。

**改造前**：
```
N7 = 架構守護 + 自癒容錯 + Bug 分析 + 修復草稿撰寫
                                       ^^^^^^^^^^^^ Generator（移除）
```

**改造後**：
```
N7 = 架構守護 + 自癒容錯 + Bug 分析 + 四維評估報告 + 反討好校準
                                       ^^^^^^^^^^^^^^^^^^^^^^^ Evaluator（新增）
修復草稿 → 交由 N3 (Software Generator) 執行
```

**跨模型校準機制**（✅ 已決議）：
```
N7 評估流程：
1. Gemini (主模型) 產出評估報告
2. Ollama Gemma (本地模型) 作為第二意見
   → 透過 mcp_Ollama-Local-Oracle_ollama_chat 調用
   → 比對兩者評分差異
3. 差異 > 20% → 標記為「需人工仲裁」
4. 差異 ≤ 20% → 採用 Gemini 主評估
```

### N9 全新定義：Entropy Guardian

```yaml
node_id: N9
name: Entropy Guardian (熵守護者)
type: background_daemon
responsibilities:
  - 7 層一致性檢查（rules 間數據同步）
  - Pattern drift detection（偏離黃金模式的偵測）
  - Harness 版本管理（與 Gemini 模型版本綁定）
  - 「承重組件」vs「裝飾組件」定期壓測
  - 降落備忘錄自動化（從手動寫入升級為背景掃描）
  - Canary Token 存活確認
schedule:   # ✅ 已決議
  daily_light:
    scope: C1-C3 一致性 + Canary Token 存活
    cost: ~500 tokens
  weekly_deep:
    scope: 全 7 層 + 承重性壓測 + Harness 版本校驗
    cost: ~3000 tokens
  manual: N1 可隨時手動喚醒完整掃描
```

---

## 二、架構總覽：五層 Harness 模型

```
使用者請求 (User Request)
    │
    ▼
╔══════════════════════════════════════════════════════════╗
║  Layer 0: Harness Runtime (N0)                          ║
║  GEMINI.md v2.0 — 地圖式入口 (~100行)                   ║
║  N0-N9 拓樸定義 + Harness 版本標籤                       ║
╠══════════════════════════════════════════════════════════╣
║  Layer 1: Middleware Stack (中介軟體堆疊)                ║
║  ┌────────┬────────┬──────────┬──────┬────────┬──────┐ ║
║  │StepGate│Scope   │Context   │Anti  │PreComp │Loop  │ ║
║  │步驟閘門│Fence   │Anchor    │Syco  │Check   │Detect│ ║
║  └────────┴────────┴──────────┴──────┴────────┴──────┘ ║
╠══════════════════════════════════════════════════════════╣
║  Layer 2: Permission Pipeline (權限管線)                 ║
║  可見性過濾 → 輸入校驗 → 權限決策 → 運行時防護           ║
║  + 兩振出局規則 + Fail-Closed 預設                       ║
╠══════════════════════════════════════════════════════════╣
║  Layer 3: Multi-Agent Protocol (多智能體協定)            ║
║  Sprint Contract + Evaluator 獨立 + 檔案基通訊           ║
║  Context Reset vs Compaction 決策樹                      ║
╠══════════════════════════════════════════════════════════╣
║  Layer 4: Entropy Management (熵管理)                    ║
║  N9 背景掃描 + 7層一致性檢查 + Harness Gardening         ║
╚══════════════════════════════════════════════════════════╝
    │
    ▼
  Agent 回應 (Agent Response)
```

---

## 三、Layer 1 — 中介軟體堆疊

### 六個中介軟體

| # | 中介軟體 | 觸發時機 | 來源 | 解決的失控模式 |
|---|---|---|---|---|
| MW1 | **StepGate（步驟閘門）** | 多步驟任務時 | v1.0 引力錨 | F1 跳關 |
| MW2 | **ScopeFence（範圍柵欄）** | 每次回覆前 | v1.0 引力錨 | F2 過度發散 |
| MW3 | **ContextAnchor（上下文錨定）** | 每次回覆開頭 | v1.0 引力錨 | F3 無關建議 |
| MW4 | **AntiSycophancy（反討好）** | 發表肯定結論前 | Custom Prompt 報告 | 討好偏差 |
| MW5 | **PreCompletionChecklist（完成前檢查）** | 回覆結束前 | NXCode 報告 | 品質漏洞 |
| MW6 | **LoopDetection（迴圈偵測）** | 持續對話中 | NXCode 報告 | 無限重試 |

### MW5 PreCompletionChecklist 詳細設計

```
回覆交付前，強制自問：
□ 1. 我是否只回答了使用者要求的交付物？（ScopeFence 二次確認）
□ 2. 我的事實陳述是否都有來源？（零幻覺鐵律）
□ 3. 信心程度標注：高/中/低/未知？（四級量表）
□ 4. 我是否提出了反面論證？（AntiSycophancy 二次確認）
□ 5. 如有額外觀察，是否已隔離到「⚡ 額外觀察」區塊？
```

---

## 四、Layer 2 — 權限與安全管線

### 四階段縱深防禦

```
階段 1: 可見性過濾
    不適用當前任務的工具/資源 → 從認知範圍中排除
    ↓
階段 2: 輸入校驗
    檔案路徑必須在允許範圍內（四區沙箱強化版）
    ↓
階段 3: 權限決策
    破壞性操作 → 必須人類確認
    跨 N 節點操作 → 必須通過 N1 路由
    ↓
階段 4: 運行時防護
    兩振出局規則：自動修復最多 2 次，超過升級 N1
    Token 預算警告：接近上下文極限時主動報告
```

### Fail-Closed 預設策略

```
任何新增的工具/操作，預設假設：
- isConcurrencySafe = false  (不安全)
- isReadOnly = false         (可能寫入)
- isDestructive = false      (但需顯式聲明才能 auto-run)
→ 新工具在顯式標記安全性之前，系統假設最危險的情況。
```

### 兩振出局規則

```
自動修復嘗試 #1：正常重試
    ↓ 若仍失敗
自動修復嘗試 #2：換策略重試
    ↓ 若仍失敗
立即停止 → 產出故障報告 → 升級給 N1（人類決策）
嚴禁第 3 次自動重試（防止 token 浪費迴圈）
```

---

## 五、Layer 3 — 多智能體協作協定

### Sprint Contract 機制（僅限跨 Agent 派任）

> [!IMPORTANT]
> Sprint Contract **不適用**於使用者直接在 N5/N8 等 Workspace 操作的場景。使用者本人即為 Planner + 驗收者，無需額外協定。

**三級適用模型**：

| 場景 | 機制 | 觸發條件 |
|---|---|---|
| 使用者直接在 Agent Workspace 操作 | **無協定** | — |
| 橫向協同（如 N8→N2 請求法源數據） | **Task Brief**（輕量版） | 只需交付物定義 + 格式要求 |
| N1 跨 Agent 派任（如 N1→N3 修復 N7 bug） | **Sprint Contract**（完整版） | 需交付物 + 驗證標準 + 範圍邊界 |

**Sprint Contract 完整版流程**（僅跨 Agent 派任時啟用）：

```
1. N1 撰寫 Sprint Contract：
   - 交付物定義（要建造什麼）
   - 驗證標準（如何判定成功，≤10 條）
   - 範圍邊界（明確排除什麼）

2. N7 (Evaluator) 審查 Contract

3. Generator 按 Contract 執行

4. N7 按 Contract 驗證（四維評分）
```

### 檔案基通訊協定

```
通訊目錄：.agent_comms/
├── contracts/          ← Sprint Contract 檔案
├── evaluations/        ← N7 評估報告
├── handoffs/           ← Context Reset 交接檔
└── entropy_reports/    ← N9 掃描報告
```

### Context Reset vs Compaction 決策樹

```
對話長度超過 60% 上下文窗口？
├── 否 → 繼續正常對話
└── 是 → 檢查是否出現 Context Anxiety 症狀
    ├── 否 → Compaction（壓縮摘要，同一智能體繼續）
    └── 是 → Context Reset
              1. 產出交接檔到 .agent_comms/handoffs/
              2. 清除上下文窗口
              3. 新對話中讀取交接檔繼續
```

---

## 六、Layer 4 — 熵管理（N9）

### Guides × Sensors 平衡目標

```
目前（v1.0）：Guides/Sensors ≈ 90/10（嚴重失衡）
目標（v2.0）：Guides/Sensors ≈ 60/40

新增 Sensors（反饋傳感器）：
┌──────────────────────────┬──────────────────────┐
│ 計算性傳感器（確定性）     │ 推理性傳感器（語義）   │
├──────────────────────────┼──────────────────────┤
│ check-consistency 腳本    │ N7 Evaluator 評分     │
│ rules 文件行數/格式檢查   │ N9 承重性壓測         │
│ 拓樸定義 vs 實際同步      │ AntiSycophancy 觸發率 │
└──────────────────────────┴──────────────────────┘
```

### 7 層一致性檢查

| # | 檢查項 | 說明 |
|---|---|---|
| C1 | N0-N9 拓樸數量 = GEMINI.md 宣稱數 | 拓樸完整性 |
| C2 | 每個運作中 N 節點有對應 rules 文件 | 文件完整性 |
| C3 | GEMINI.md 行數 ≤ 120 行 | 地圖而非手冊 |
| C4 | 每條 rules 包含 `## Fix:` 修復指令 | Linter = 修復指令 |
| C5 | 中介軟體清單 = 6 個 | 中介軟體完整性 |
| C6 | Harness 版本標籤存在且格式正確 | 版本管理 |
| C7 | 降落備忘錄最後更新 ≤ 7 天 | 記憶新鮮度 |

### Harness 生命週期管理

```
Gemini 模型更新時：
1. 逐組件壓測：移除一條 rule → 觀察行為變化
2. 承重組件（移除後惡化）→ 保留
3. 裝飾組件（移除後無影響）→ 移除（減量）
4. 新增需求（新失控模式）→ 新增 rule
5. 更新 Harness 版本標籤
```

---

## 七、GEMINI.md v2.0 結構設計

```markdown
# Jasper Strategic Hub — Harness v2.0
# HARNESS_VERSION: 2.0.0 | MODEL_COMPAT: gemini-2.5-pro

## §0 拓樸定義 (N0-N9)                     ← ~18 行
## §1 最高執行禁令 (Supreme Directives)     ← ~15 行
## §2 中介軟體堆疊 (Middleware Stack)       ← ~25 行
## §3 權限管線 (Permission Pipeline)        ← ~15 行
## §4 認知辯論 (Cognitive Debate)           ← ~10 行
## §5 心智框架 (Cognitive Frameworks)       ← ~10 行
## §6 深層參考 (Deep References)            ← ~10 行

總計：~103 行
```

---

## 七½、Harness 文件架構設計（Document Architecture）

> [!IMPORTANT]
> 研究報告一致指出：**GEMINI.md 是地圖，不是手冊**。~100 行的入口只負責指路，深度內容全部外掛到結構化目錄。這是 OpenAI、Anthropic、deusyu 三份報告的共同模式。

### 文件架構總覽

```
GEMINI.md (§6 Deep References)     ← 指向 ↓ 這個目錄
│
d:\hermes-agent\docs\Harness\
├── README.md                       ← 文件架構索引（ARCHITECTURE.md 等效）
│
├── design-docs/                    ← 設計決策（WHY）
│   ├── core-beliefs.md              ← 核心信念：最高禁令 + 六大心智框架的深度解釋
│   ├── topology-N0-N9.md            ← 拓樸完整定義（從 Plan §一 獨立出來）
│   ├── middleware-specs.md          ← MW1-MW6 完整規格（GEMINI.md §2 的詳版）
│   └── permission-pipeline.md       ← 四階段權限管線詳細設計
│
├── exec-plans/                     ← 執行計畫（WHAT + WHEN）
│   ├── Gravity_Anchor_v2_Implementation_Plan.md   ← 已有
│   ├── Gravity_Anchor_v2_Construction_Plan.md     ← 已有
│   └── tech-debt-tracker.md         ← 技術債追蹤（N9 掃描結果匯入）
│
├── product-specs/                  ← 產品規格（HOW）
│   ├── sprint-contract-spec.md      ← Sprint Contract 完整規格
│   ├── evaluator-protocol.md        ← N7 Evaluator 四維評分規格
│   └── canary-token-spec.md         ← Canary Token 偵測規格
│
├── references/                     ← 參考文獻（研究報告歸檔）
│   ├── OpenAI_Harness_Engineering_Original_Research_Report.md
│   ├── Anthropic_Harness_Design_Long_Running_Apps_Research_Report.md
│   ├── NXCode_Harness_Engineering_Complete_Guide_Research_Report.md
│   ├── Harness_Engineering_Learning_Archive_Research_Report.md
│   ├── Everything_Gemini_Code_Research_Report.md
│   ├── AI_Custom_System_Prompt_Harness_Analysis_Report.md
│   └── Claude_Code_Harness_Architecture_Analysis.md
│
├── generated/                      ← N9 自動產生的報告
│   └── (由 check-harness-consistency 產出)
│
└── QUALITY_SCORE.md                ← Phase 4 壓測後的品質評分
```

### GEMINI.md §6 指向規則

```
§6 只寫指向指令，不寫內容：
  「完整拓樸定義 → docs/Harness/design-docs/topology-N0-N9.md」
  「MW1-MW6 詳細規格 → docs/Harness/design-docs/middleware-specs.md」
  「品質評分 → docs/Harness/QUALITY_SCORE.md」
這樣 GEMINI.md 永遠不會超過 120 行。
```

---

## 八、交付物清單

| # | 交付物 | 路徑 | 說明 |
|---|---|---|---|
| D1 | **GEMINI.md v2.0** | `C:\Users\promy\.gemini\GEMINI.md` | 重構後的全域 Harness 入口 |
| D2 | **文件架構骨架** | `docs/Harness/` | 6 個子目錄 + README.md |
| D3 | **N7 Evaluator Protocol** | `docs/Harness/product-specs/evaluator-protocol.md` | N7 四維評分規格 |
| D4 | **N9 Entropy Guardian Rules** | `.agents/rules/entropy-guardian.md` | N9 全新角色定義 |
| D5 | **Sprint Contract Spec** | `docs/Harness/product-specs/sprint-contract-spec.md` | 完整規格 + 範本 |
| D6 | **check-consistency script** | `scripts/check-harness-consistency.ps1` | 7 層一致性檢查腳本 |
| D7 | **Harness Audit Checklist** | `docs/Harness/exec-plans/harness_audit_checklist.md` | 模型更新壓測清單 |
| D8 | **QUALITY_SCORE.md** | `docs/Harness/QUALITY_SCORE.md` | Phase 4 壓測結果 |

---

## 九、實施路線圖

```
Phase 1: 基礎層建立（~2h）                    ← 立即可執行
├── docs/Harness/ 文件架構骨架建立 + README.md
├── 研究報告移入 references/
├── GEMINI.md v2.0 撰寫（§0-§3 + §5-§6）
├── 中介軟體 6 條精簡定義嵌入 + Canary Token
└── 四階段權限管線嵌入

Phase 2: 評估層建立（~4h）
├── N7 Evaluator Protocol 撰寫 → product-specs/evaluator-protocol.md
├── N7 hermes-agent.md 更新（移除 Generator 職責）
├── Sprint Contract Spec → product-specs/sprint-contract-spec.md
├── Canary Token Spec → product-specs/canary-token-spec.md
└── .agent_comms/ 目錄結構建立

Phase 3: 熵管理層（~4h）
├── N9 Entropy Guardian Rules 撰寫
├── check-harness-consistency.ps1 開發
├── design-docs/ 填充（core-beliefs + topology + middleware-specs + permission-pipeline）
├── exec-plans/harness_audit_checklist.md 撰寫
├── exec-plans/tech-debt-tracker.md 建立
└── 降落備忘錄自動化升級

Phase 4: 壓力測試（~1 週）
├── F1/F2/F3 三大失控模式測試
├── Context Anxiety 測試（超長對話）
├── 逐 MW 承重性測試
└── QUALITY_SCORE.md 產出

Phase 5: 全域擴展（~1 週）
├── N2-N5, N8 per-project rules 更新
├── N6 設計納入上下文壓縮管線
├── Guides/Sensors 平衡度量化
├── 文件架構完整性校驗（交叉引用檢查）
└── Harness v2.0 正式發佈 + Release Notes
```

---

## 十、驗證計畫

### 行為驗證（壓力測試）

| 場景 | 預期行為 | 對映機制 |
|---|---|---|
| 多步驟任務「先 A1 再 A2 再 A3」 | 只做 A1，回報完成，等待指令 | MW1 StepGate |
| 單焦點任務「請綜合這篇文獻」 | 只做文獻綜合，不建議改架構 | MW2 ScopeFence |
| 長上下文中提到不相關章節 | 不建議「順便修改」 | MW3 ContextAnchor |
| Agent 要肯定一個可疑結論 | 先提出反面論證再下結論 | MW4 AntiSycophancy |
| 自動修復失敗 2 次 | 停止重試，升級 N1 | 兩振出局規則 |
| 對話超過 60% 上下文窗口 | 主動報告 + 建議 Reset/Compact | Context Anxiety 防護 |

---

## Resolved Decisions（全部已決議）

| # | 問題 | 決議 | 實施階段 |
|---|---|---|---|
| Q1 | N9 觸發頻率 | 每日輕量掃描（C1-C3）+ 每週深度掃描（全 7 層） | Phase 3 |
| Q2 | N7 跨模型校準 | 採用 Ollama Gemma 作為第二意見，差異 >20% 需人工仲裁 | Phase 2 |
| Q3 | Canary Token | 直接部署，不等 Phase 4 | Phase 1 |

### Canary Token 設計（✅ 已決議直接部署）

```
嵌入位置：GEMINI.md v2.0 §2 中介軟體堆疊末尾

格式：
🦜 CANARY_ALIVE | HARNESS_VERSION: 2.0.6 | RULES_HASH: {auto}

偵測機制：
1. 每次長對話（>15 輪）時，Agent 在回覆末尾靜默自檢：
   → 是否仍能回憶 CANARY_ALIVE 標記？
   → 是否仍能正確複述 Harness 版本號？
2. 自檢失敗 → 主動警告使用者：
   「⚠️ 上下文衰減偵測：Harness 規則可能已被截斷，建議 Context Reset。」
3. N9 每日掃描時檢查 Canary 存活率
```
