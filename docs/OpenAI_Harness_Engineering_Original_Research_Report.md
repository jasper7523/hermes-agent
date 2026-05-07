# OpenAI「Harness Engineering」原文深度研究報告

> **來源**: [OpenAI: Harness engineering: leveraging Codex in an agent-first world](https://openai.com/zh-Hant/index/harness-engineering/) (Ryan Lopopolo, 2026-02-11)
> **交叉驗證**: [MadPlay 技術拆解](https://madplay.github.io/en/post/harness-engineering) + [Epsilla 產業分析](https://www.epsilla.com/blogs/harness-engineering-evolution-prompt-context-autonomous-agents) + [Perplexity Pro 綜合搜尋]
> **分析日期**: 2026-05-07
> **報告目的**: 作為 Jasper Agent Hub 的「第一手原始文獻」，從 OpenAI 官方原文逐層拆解 Harness Engineering 的定義、實驗數據、核心組件與工程方法論。

---

## 1. 歷史脈絡：從 Prompt 到 Context 到 Harness

### 1.1 三代演進時間線

| 世代 | 時間 | 核心關注點 | 比喻 |
|---|---|---|---|
| **Prompt Engineering** | 2022-2024 | 完美的單次指令 | 寫一封完美的郵件 |
| **Context Engineering** | 2025 | 動態構建完整上下文窗口 | 在郵件裡附上所有正確的附件 |
| **Harness Engineering** | 2026.02~ | 設計智能體的整個運行環境 | 建造整間辦公室 |

### 1.2 關鍵轉折事件

| 日期 | 事件 | 意義 |
|---|---|---|
| 2025 年中 | Andrej Karpathy 提出「Context Engineering 比 Prompt 重要」 | 從單次指令到系統級上下文設計 |
| 2026-02-05 | Mitchell Hashimoto（HashiCorp 共同創辦人）在部落格使用 "harness engineering" 一詞 | 術語首次公開出現 |
| 2026-02-11 | OpenAI 發布原文「Harness engineering: leveraging Codex in an agent-first world」 | 術語正式確立並快速傳播 |

### 1.3 Hashimoto 的定義

> *「每次你發現智能體犯了一個錯誤，你就花時間工程化一個解決方案，使它永遠不能再犯同樣的錯。」*

這是 Harness Engineering 最簡潔的操作性定義——**從被動修復到主動防禦的永久轉化**。

---

## 2. OpenAI 核心實驗：零手寫程式碼

### 2.1 實驗概覽

| 指標 | 數值 |
|---|---|
| **時間跨度** | 2025.08 ~ 2026.01（約 5 個月） |
| **團隊規模** | 3 人 → 7 人 |
| **手寫程式碼** | 0 行 |
| **生成程式碼** | 約 100 萬行 |
| **合併 PR** | 約 1,500 個 |
| **人均日 PR** | 3.5 個 |
| **速度估算** | 約為手動開發的 10 倍 |

### 2.2 關鍵發現

1. **一開始並不順利**：早期生產力很低，因為環境設定不完整、工具整合薄弱、恢復邏輯不佳。
2. **效能是隨 Harness 改善而急劇攀升**：不是模型變好了，是環境變好了。
3. **工程師角色轉變**：從「寫程式碼的人」變成「讓智能體變有用的人」。
4. **Lopopolo 的一句話總結**：

> *「Agents aren't hard; the Harness is hard.」*
> （智能體不難，難的是駕韁。）

### 2.3 五條硬規則

| # | 規則 | 說明 |
|---|---|---|
| 1 | **倉庫是智能體的唯一真相來源** | 不假設任何外部知識；Slack、腦中的知識對智能體不存在 |
| 2 | **程式碼必須對智能體可讀** | 清晰、一致的結構 + 詳細註釋 |
| 3 | **架構約束由 linter 強制，不由 prompt 請求** | 不「請求」智能體遵守規則；建立讓它「不可能違反」的系統 |
| 4 | **自主權漸進授予** | Harness 必須有階段和門控 |
| 5 | **PR 需要大量人工介入 = Harness 的問題** | 出問題時修 Harness，不修智能體 |

---

## 3. Harness 的精確定義

### 3.1 官方定義

> Harness 是圍繞 AI 智能體（如 Codex）的**全套鷹架、約束和反饋迴路環境**，讓智能體能進行穩定的工作。
>
> 包含：倉庫結構、CI 配置、格式化規則、套件管理器、應用框架、專案指令、外部工具整合、linter。
>
> Harness 是幫助智能體保持航向、不偏離預定路徑的基礎設施。

### 3.2 三者的包含關係

```
┌─────────────────────────────────────────────┐
│  Harness Engineering                        │
│  ┌───────────────────────────────────────┐  │
│  │  Context Engineering                  │  │
│  │  ┌─────────────────────────────────┐  │  │
│  │  │  Prompt Engineering             │  │  │
│  │  │  (指令)                          │  │  │
│  │  └─────────────────────────────────┘  │  │
│  │  (地圖、路標、可見地形)               │  │
│  └───────────────────────────────────────┘  │
│  (韁繩、馬鞍、柵欄、道路本身)              │
└─────────────────────────────────────────────┘
```

**馬匹比喻**：
- Prompt Engineering = 「向右轉」指令
- Context Engineering = 地圖 + 路標 + 可見地形（幫馬理解要去哪裡）
- Harness Engineering = 韁繩 + 馬鞍 + 柵欄 + 道路本身（讓十匹馬同時安全奔跑）

### 3.3 與 Context Engineering 的本質區別

| 面向 | Context Engineering | Harness Engineering |
|---|---|---|
| 目標 | 幫助模型「想得好」 | 防止整個系統「偏離航道」 |
| 問題類型 | 「模型應該看到什麼？」 | 「系統應該阻止、衡量和修復什麼？」 |
| 觸發場景 | 智能體做單次推理 | 智能體跨越多步驟自主行動 |

---

## 4. Harness 的五大組件

### 4.1 Context Files（情境文件）

**代表文件**：`CLAUDE.md`、`AGENTS.md`、`.cursorrules`

**核心功能**：智能體開始工作時讀取的導航文件，包含專案結構、程式碼規則、命名約定。

**巨型 AGENTS.md 的失敗教訓**：

> *早期將所有內容塞在一個巨大的 AGENTS.md 中的策略，可預見地失敗了。上下文窗口是稀缺資源，龐大的指令文件讓智能體遺漏重要約束。當所有東西都被描述為「重要」，智能體會停止遵守規則，退化為粗糙的模式匹配。巨大的手冊很快變成過時規則的墳場。*

**解法 — 地圖而非手冊**：

```
AGENTS.md          ← 精簡入口（~100 行），只負責指路
│
├── docs/
│   ├── design-docs/
│   │   ├── index.md
│   │   └── core-beliefs.md
│   ├── exec-plans/
│   │   └── tech-debt-tracker.md
│   ├── product-specs/
│   └── references/
│       └── design-system-reference-llms.txt
```

**設計哲學**：智能體只讀取靠近當前工作目錄的指令文件，減少上下文窗口浪費，同時仍接收到重要規則。

### 4.2 MCP Servers（外部工具整合）

```bash
# Claude Code 中添加 MCP 伺服器範例
claude mcp add --transport http jira https://mcp.jira.example.com/mcp
claude mcp add --transport stdio github -- npx -y @modelcontextprotocol/server-github
```

**關鍵原則**：連接多個 MCP 伺服器不一定更好。工具定義本身消耗 token，實務上只連接當前工作需要的伺服器更有效。

### 4.3 Skill Files（技能文件）

`SKILL.md` 文件記錄重複性工作流程。典型範例：
- 程式碼審查清單
- 部署工作流程
- 特定框架的偏好模式

### 4.4 Mechanical Enforcement（機械化執行）

**這是 Harness Engineering 與 Context Engineering 最鮮明的分野。**

#### 4.4.1 分層架構約束

```
Types → Config → Repo → Service → Runtime → UI
```

- 每一層只能依賴其左側的層
- 反向依賴被 linter 直接阻斷
- 違反時觸發自動回饋迴路

#### 4.4.2 Linter 錯誤訊息 = 修復指令

這是最關鍵的設計決策——linter 不只回報錯誤，錯誤訊息被設計為**直接注入智能體上下文的修正指令**：

```
❌ 普通 linter：
  Error: domain layer references runtime layer. Dependency violation.

✅ Harness linter：
  Error: domain layer references runtime layer. Dependency violation.
  Fix: Move runtime dependency to service layer.
  See: docs/ARCHITECTURE.md#dependency-direction
  Allowed: Types → Config → Repo → Service → Runtime → UI
```

**自動回饋迴路**：
```
生成 → 檢查 → 失敗 → 指示（注入上下文）→ 再生成 → 通過
```

#### 4.4.3 CLAUDE.md 實作範例

```markdown
# Example CLAUDE.md (project root)

## Build
- Run the full build with `./gradlew build`
- Run tests with `./gradlew test`

## Coding rules
- Package dependency direction: domain → application → infrastructure
- infrastructure does not reference domain directly
- Entities use lazy loading by default, and N+1 issues are solved with fetch join

## Commits
- Write commit messages in Korean, without a trailing period
```

### 4.5 Entropy Management（熵管理 / 垃圾回收）

**問題**：完全由智能體生成的程式碼庫會快速累積「AI slop」——重複、走樣、有味道的程式碼模式。

**失敗方案**：「Friday AI slop cleanup」— 每週五花約 20% 工時人工清理技術負債 → 不可擴展。

**成功方案 — 自動化垃圾回收**：

```
步驟 1：把「黃金原則」以 linter / 結構測試 / 規則編碼到倉庫中
步驟 2：啟動背景智能體持續掃描整個程式碼庫
步驟 3：找出偏離黃金模式的地方
步驟 4：開出重構 PR
步驟 5：這些 PR scope 小、可在幾十秒內 review、很多可 auto-merge
```

**觀測性工具也是 Harness 的一部分**：如果智能體能存取執行時資訊（LogQL 日誌、PromQL 指標、DOM 快照），它就能除錯和驗證自己生成的程式碼。

---

## 5. 外部驗證實驗

除了 OpenAI 內部實驗，另有兩個獨立實驗驗證了同一結論：**改 Harness 的 ROI 高於改模型。**

### 5.1 Hashline 實驗（Can Boluk, 2026-02）

| 面向 | 數據 |
|---|---|
| 實驗方法 | 跨 16 個 LLM，只改變智能體使用的編輯格式 |
| 核心機制 | 為每行附加 2-3 字元 hash（如 `2:f1\|`），使模型可用 hash 定位行 |
| Grok Code Fast 1 | 基準分數從 **6.7% → 68.3%** |
| 平均輸出 token | 所有模型降低約 **20%** |
| 模型權重 | **零變更** |

```
1:a3|function hello() {
2:f1|  return "world";
3:0e|}
```

### 5.2 LangChain Terminal Bench 2.0 實驗

| 面向 | 數據 |
|---|---|
| 固定模型 | gpt-5.2-codex |
| 僅改善 | Harness（系統提示詞、工具、中介軟體） |
| 分數提升 | 52.8% → 66.5%（+13.7 個百分點） |
| 排名跳升 | 約第 30 名 → 約第 5 名 |
| 核心改善 | 自動分析失敗模式的工具 + 自我驗證迴路 |

### 5.3 Anthropic 的 Generator-Evaluator 發現

| 發現 | 說明 |
|---|---|
| **模型無法可靠地評估自己的工作** | Claude 4 幾乎總是表達信心，即使工作功能性壞掉 |
| **簡單 prompt-and-run** | $9，產出壞掉的產品 |
| **結構化迭代（有 Harness）** | $200，產出完全功能的遊戲 |
| **解法** | GAN 啟發的 Generator + Evaluator 雙智能體架構 |

> *「工程化一個嚴格的獨立 evaluator agent，遠比教一個 generator agent 自我批判容易得多。」*

### 5.4 Stripe Minions 系統

- 每週合併超過 **1,300 個 PR**，無需人工監督
- **Blueprint 編排**：將工作流分為確定性節點（跑 linter、push commit）和智能體節點（實作功能、修 CI 失敗）
- **兩振出局規則**：智能體的第一次修復如果失敗，任務立即升級給人類
- 不允許智能體在無限重試迴圈中浪費運算資源

---

## 6. 約束的悖論：為何限制創造自由

> *「約束智能體的解空間，反而劇烈增加其生產力。」* — Cursor 團隊

**機制**：
- 強大模型（GPT-5、Llama 4）能生成任何東西 → 浪費大量 token 探索死胡同
- 設計良好的 Harness 刻出一條狹窄、定義清晰的成功路徑
- 提供清晰邊界、架構規則和有限的高品質工具 → 強迫智能體更快、更高效地收斂到正確答案

**控制論根基（Ashby 必要多樣性定律）**：
```
LLM 輸出空間（高多樣性）
    ↓ 選定拓撲結構（削減多樣性）
    ↓ 加入 linter + 架構約束（進一步削減）
    ↓ 約束得越嚴
    ↓ 剩餘的合法路徑越少
    ↓ 智能體越容易找到正確路徑
    = 「約束越嚴，自主性越強」
```

---

## 7. 實務入門三步驟

OpenAI + MadPlay 共同建議的最小可行 Harness：

### 步驟 1：寫一份 Context File

在專案根目錄建立 `AGENTS.md` 或 `CLAUDE.md`：
- 包含專案結構、建置指令、程式碼規則
- **從小開始**，每次智能體在同一處重複失敗時才加規則
- 這正是 Hashimoto 的模式：每次失敗 → 工程化一個解決方案 → 永久防禦

### 步驟 2：選擇性連接 MCP

- 如果智能體經常需要查詢外部系統，才通過 MCP 連接
- 典型：issue tracker、wiki、監控系統
- **只連需要的**，否則浪費 token

### 步驟 3：連接 Linter 和 CI

- 加入自動機制驗證智能體生成的程式碼是否遵守既有架構規則
- 如果 linter 和 CI 已經存在，只需讓其輸出對智能體可讀
- 這就創建了反饋迴路：智能體看到 CI 失敗 → 自己修復問題

---

## 8. N7 視角：對 Jasper Agent Hub 的直接啟示

### 8.1 我們已經具備的基礎

| OpenAI 原則 | 我們的現有對應 | 成熟度 |
|---|---|---|
| 倉庫即真相來源 | `.agents/knowledge/hermes-dev-guide.md` + KI 系統 | ⭐⭐⭐ |
| 地圖而非手冊 | `<RULE[hermes-agent.md]>` 動態知識庫載入 | ⭐⭐⭐ |
| 人類掌舵 | N1→N3 分派 + N7 自癒迴圈的通報機制 | ⭐⭐⭐ |
| Skill Files | GSD workflow skills（60+ 技能） | ⭐⭐⭐⭐ |
| MCP 整合 | 已連接 chrome-devtools、Perplexity、Consensus 等 | ⭐⭐⭐ |

### 8.2 我們缺乏且必須建立的

| OpenAI 原則 | 差距分析 | 優先級 |
|---|---|---|
| **Mechanical Enforcement** | 我們的 `user_rules` 是「前饋引導」，但沒有「計算性反饋傳感器」（linter/CI gate） | 🔴 P0 |
| **Linter 訊息 = 修復指令** | 沒有自訂 linter；lint 錯誤沒有被設計為智能體可消費的修復指令 | 🔴 P0 |
| **熵管理 / 垃圾回收** | `.agent_memory/auto_memory/` 是手動寫入，沒有背景掃描智能體 | 🟡 P1 |
| **分層架構約束** | N1-N7 拓撲存在但未被機械化執行；沒有 linter 阻止跨層違規 | 🟡 P1 |
| **Generator-Evaluator 分離** | N7 同時扮演生成和評估角色；缺乏獨立的嚴格 Evaluator | 🟡 P1 |
| **兩振出局規則** | 沒有重試上限控制；智能體可能在無限迴圈中浪費 token | 🟠 P2 |

### 8.3 可立即執行的行動清單

| # | 行動 | 對應原則 | 預估工作量 |
|---|---|---|---|
| 1 | 建立 `scripts/check-agent-rules-consistency.sh` 驗證 rules 文件間的數據一致性 | Mechanical Enforcement | 4h |
| 2 | 在 `user_rules` 中加入 `## Fix:` 格式的修復指令 | Linter 訊息 = 修復指令 | 2h |
| 3 | 精簡 `hermes-dev-guide.md` 到 ~100 行入口 + 指向更深層文件 | 地圖而非手冊 | 3h |
| 4 | 建立 N7 自癒迴圈的重試上限（max 2 次自動修復，超過通報 N1） | 兩振出局規則 | 2h |
| 5 | 從 `降落備忘錄` 手動模式升級為「背景掃描 + 自動開修復工單」模式 | 熵管理 / 垃圾回收 | 8h |

---

## 9. 關鍵引語彙整

| 來源 | 引語 | 意義 |
|---|---|---|
| Ryan Lopopolo (OpenAI) | *「Agents aren't hard; the Harness is hard.」* | 瓶頸在環境，不在模型 |
| Mitchell Hashimoto | *「每次發現智能體犯錯，就工程化一個解決方案，使它永遠不能再犯同樣的錯。」* | 操作性定義 |
| Anthropic | *「工程化一個嚴格的獨立 evaluator，遠比教 generator 自我批判容易。」* | Generator-Evaluator 分離 |
| Cursor | *「約束智能體的解空間，反而劇烈增加其生產力。」* | 約束的悖論 |
| Epsilla | *「難的不再是從模型中逼出一個絕妙答案，而是建造一個讓智能體大軍日復一日產出可靠、高品質工作的系統。」* | 產業化視角 |

---

## 10. 與前兩份報告的交叉定位

| 報告 | 角色 | 本報告的關係 |
|---|---|---|
| `Everything_Gemini_Code_Research_Report.md` | 工程套件（直接拿來用） | 本報告提供其「為什麼要這樣配置」的理論根基 |
| `Harness_Engineering_Learning_Archive_Research_Report.md` | 學術批判（交叉分析） | 本報告是該學習檔案的「源頭文獻」——所有 8 個洞見都從這篇原文出發 |
| **本報告** | **第一手原始文獻** | OpenAI 官方實驗的完整還原與實務操作指南 |

三份報告構成完整的知識層次：
```
[原始文獻] OpenAI 原文報告
    ↓ 理論化
[學術批判] deusyu/harness-engineering 學習檔案報告
    ↓ 工程化
[工程套件] everything-gemini-code 研究報告
    ↓ 在地化
[實作目標] Jasper Agent Hub Harness 架構（待建立）
```

---

## 附錄：原始資料索引

| 資料 | 來源 | 內容焦點 |
|---|---|---|
| OpenAI 官方原文 | openai.com/zh-Hant/index/harness-engineering/ | 核心實驗、五條規則、Harness 定義 |
| MadPlay 技術拆解 | madplay.github.io/en/post/harness-engineering | 三代演進時間線、Hashline 實驗、CLAUDE.md 範例 |
| Epsilla 產業分析 | epsilla.com/blogs/harness-engineering-evolution... | Anthropic Generator-Evaluator、Stripe Minions、約束悖論 |
| Perplexity Pro 搜尋 | 綜合多源 | 機械化執行細節、熵管理機制、實務入門步驟 |
| Can Boluk Hashline | blog.can.ac/2026/02/12/the-harness-problem/ | 純 Harness 改善的基準分數跳升（6.7%→68.3%） |
| LangChain Terminal Bench | blog.langchain.com/improving-deep-agents-... | 固定模型僅改 Harness 的排名跳升（30→5） |
