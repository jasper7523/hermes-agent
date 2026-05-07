# Everything Gemini Code — Harness Engineering 研究報告

> **來源**: [Jamkris/everything-gemini-code](https://github.com/Jamkris/everything-gemini-code)
> **分析日期**: 2026-05-07
> **報告目的**: 拆解該專案的「Harness Engineering」設計哲學與技術架構，作為我們 Antigravity Agent Hub (N1-N7) 自建 Harness 架構的決策依據。

---

## 1. 專案概覽與核心哲學

### 1.1 什麼是 Harness Engineering？

> **"Tune the runtime around the model, not the model itself."**
> 調整執行環境以適應模型，而非調整模型本身。

這是 `everything-gemini-code` 的核心設計理念。該專案並非一個獨立的 AI Agent，而是一個**工程套件 (Toolkit)**，專門針對 **Gemini CLI** 與 **Antigravity** 平台設計，透過以下三層機制約束與引導 AI 模型的行為：

| 層級 | 機制 | 控制面向 |
|---|---|---|
| **靜態規約層 (Rules)** | `.gemini/rules/` 目錄 | 定義「做什麼」(What) — 標準、規範、檢核清單 |
| **動態執行層 (Hooks)** | `hooks.json` 事件鉤子 | 定義「何時做」(When) — 在 Tool 使用前後觸發自動化動作 |
| **深度參考層 (Skills)** | `skills/` 目錄 | 定義「如何做」(How) — 特定任務的完整執行指南 |

**輔助機制**: `agents/` 目錄提供專職 Agent 角色定義（如 code-reviewer、security-reviewer），作為上述三層架構的消費者。

### 1.2 與傳統 Prompt Engineering 的差異

| 面向 | Prompt Engineering | Harness Engineering |
|---|---|---|
| **作用點** | 單一對話的 System Prompt | 專案級的持久化配置 |
| **持久性** | 隨對話結束消失 | 存檔於 `.gemini/` 目錄，版本控制 |
| **粒度** | 粗粒度的行為指引 | 細粒度的語言/框架/安全/測試規約 |
| **自動化** | 無 | `PostToolUse` hooks 自動觸發 linter/formatter |
| **可組合性** | 手動拼接 | `common` 基底 + 語言專屬疊加 |

---

## 2. 架構深度剖析

### 2.1 Rules 層 — 靜態規約系統

```
rules/
├── common/           # 語言無關的通用原則（必裝基底）
│   ├── coding-style.md
│   ├── git-workflow.md
│   ├── testing.md
│   ├── performance.md
│   ├── patterns.md
│   ├── hooks.md
│   ├── agents.md
│   └── security.md
├── typescript/       # TypeScript/JavaScript 專屬
├── python/           # Python 專屬
├── golang/           # Go 專屬
├── cpp/              # C++ 專屬
├── csharp/           # C# 專屬
├── dart/             # Dart/Flutter 專屬
├── java/             # Java 專屬
├── kotlin/           # Kotlin 專屬
├── perl/             # Perl 專屬
├── php/              # PHP 專屬
├── rust/             # Rust 專屬
├── swift/            # Swift 專屬
├── web/              # Web 前端專屬
├── zh/               # 中文語境規則
└── README.md
```

#### 關鍵設計原則

1. **階層式繼承 (Layered Inheritance)**
   - `common/` 為基底層，定義所有專案通用的原則（不含語言特定的程式碼範例）
   - 語言目錄擴充 `common/` 規則，每個檔案開頭必須包含：
     ```
     > This file extends [common/xxx.md](../common/xxx.md) with <Language> specific content.
     ```

2. **優先順序 (Priority = CSS Specificity 模型)**
   - 語言專屬規則 > 通用規則（specific overrides general）
   - 範例：`common/coding-style.md` 推薦不可變性(immutability)，但 `golang/coding-style.md` 允許 pointer receiver mutation

3. **相對路徑不可破壞 (No Flattening)**
   - 安裝時**嚴禁**展平目錄結構（`cp -r rules/* .gemini/rules/`），否則會破壞 `../common/` 引用鏈
   - 正確安裝：`cp -r rules/common ~/.gemini/rules/common && cp -r rules/python ~/.gemini/rules/python`

### 2.2 Hooks 層 — 動態事件系統

Hooks 基於 Gemini CLI 的 `PostToolUse` 事件機制，在 AI 模型使用工具（如 `edit_file`、`run_terminal_command`）後自動觸發外部指令。

**目錄結構**：`hooks/hooks.json`（單一 JSON 配置檔）

**典型應用場景**：

| Hook 觸發點 | 自動執行 | 效果 |
|---|---|---|
| `edit_file` 完成後 | `prettier --write`, `eslint --fix` | 自動格式化+修復程式碼 |
| `edit_file` (Python) 完成後 | `black`, `ruff check --fix` | Python 自動格式化 |
| `edit_file` (Go) 完成後 | `gofmt -w`, `go vet` | Go 慣例格式化+靜態分析 |
| `run_terminal_command` 完成後 | Test runner 驗證 | 確保測試仍然通過 |

### 2.3 Agents 層 — 專職角色定義

`agents/` 目錄包含 **44 個專職 Agent 角色定義**，每個角色是一份 Markdown 文件，定義該 Agent 的專長、職責邊界與行為準則。

#### 分類總覽

| 類別 | Agent 角色 | 數量 |
|---|---|---|
| **通用架構** | architect, code-architect, planner, chief-of-staff | 4 |
| **程式碼審查** | code-reviewer, python-reviewer, typescript-reviewer, go-reviewer, rust-reviewer, java-reviewer, kotlin-reviewer, csharp-reviewer, cpp-reviewer, flutter-reviewer, database-reviewer | 11 |
| **建置除錯** | build-error-resolver, cpp-build-resolver, dart-build-resolver, go-build-resolver, java-build-resolver, kotlin-build-resolver, pytorch-build-resolver, rust-build-resolver | 8 |
| **程式碼品質** | code-simplifier, code-explorer, comment-analyzer, refactor-cleaner, type-design-analyzer, silent-failure-hunter | 6 |
| **安全/合規** | security-reviewer, healthcare-reviewer | 2 |
| **效能/SEO** | performance-optimizer, seo-specialist, harness-optimizer | 3 |
| **測試** | tdd-guide, e2e-runner, pr-test-analyzer | 3 |
| **文件** | doc-updater, docs-lookup | 2 |
| **GAN 工作流** | gan-planner, gan-generator, gan-evaluator | 3 |
| **開源治理** | opensource-forker, opensource-packager, opensource-sanitizer | 3 |
| **自動化** | loop-operator, conversation-analyzer, a11y-architect | 3 |

### 2.4 Skills 層 — 深度可操作指南

`skills/` 目錄包含 **100+ 個技能模組**，每個模組是一個目錄，提供特定工程任務的完整指南。

#### 關鍵技能分類

| 分類 | 代表性技能 |
|---|---|
| **Agent 工程** | `agent-harness-construction`, `autonomous-agent-harness`, `agent-introspection-debugging`, `agent-eval`, `agentic-engineering`, `ai-first-engineering` |
| **自主迴圈** | `autonomous-loops`, `continuous-agent-loop`, `continuous-learning`, `continuous-learning-v2` |
| **程式語言** | `golang-patterns`, `golang-testing`, `python-patterns` (推測), `cpp-coding-standards`, `cpp-testing`, `csharp-testing`, `java-coding-standards`, `dart-flutter-patterns` |
| **架構模式** | `hexagonal-architecture`, `backend-patterns`, `frontend-patterns`, `design-system`, `api-design`, `docker-patterns`, `deployment-patterns` |
| **領域專屬** | `healthcare-phi-compliance`, `hipaa-compliance`, `healthcare-cdss-patterns`, `healthcare-emr-patterns`, `customs-trade-compliance`, `defi-amm-security` |
| **成本/效率** | `cost-aware-llm-pipeline`, `context-budget`, `ecc-tools-cost-audit`, `content-hash-cache-pattern` |
| **前端/設計** | `frontend-design`, `frontend-slides`, `design-system`, `click-path-audit`, `browser-qa` |
| **GIT/協作** | `git-workflow`, `github-ops`, `architecture-decision-records`, `codebase-onboarding`, `code-tour` |

---

## 3. 安裝與配置機制

### 3.1 自動安裝（推薦）

```bash
# 安裝 common 基底 + 語言專屬規則
./install.sh typescript
./install.sh python
./install.sh golang

# 一次安裝多語言
./install.sh typescript python
```

### 3.2 手動安裝（進階）

```bash
# 1. 必裝：common 基底層
cp -r rules/common ~/.gemini/rules/common

# 2. 按需疊加語言專屬層
cp -r rules/typescript ~/.gemini/rules/typescript
cp -r rules/python ~/.gemini/rules/python

# ⚠️ 嚴禁：cp -r rules/* ~/.gemini/rules/  ← 會覆蓋 common 檔案
```

### 3.3 安裝路徑

所有規則安裝至 `~/.gemini/rules/` 目錄，Gemini CLI / Antigravity 會自動載入。

---

## 4. N7 視角：與 Jasper Agent Hub 的對照分析

### 4.1 架構映射

| Everything Gemini Code | Jasper Agent Hub (N1-N7) | 對應關係 |
|---|---|---|
| `rules/common/` | `<RULE[user_global]>` | 全域基底規約 |
| `rules/<language>/` | `<RULE[hermes-agent.md]>` | 專案/Agent 級覆寫 |
| `agents/*.md` | N1-N7 拓樸定義 | 專職 Agent 角色 |
| `hooks/hooks.json` | N7 自癒迴圈 + Pre-flight Hooks | 自動化事件驅動 |
| `skills/` | `.agents/skills/`, `.agents/workflows/` | 深度可操作指南 |
| `GEMINI.md` | `.agents/knowledge/hermes-dev-guide.md` | 專案核心指南 |

### 4.2 差距分析 (Gap Analysis)

| 面向 | Everything Gemini Code | Jasper Agent Hub | 差距 |
|---|---|---|---|
| **規則階層** | 2 層 (common + language) | 2 層 (global + project) | ✅ 對等 |
| **Hook 自動化** | `PostToolUse` JSON 配置 | N7 自癒迴圈 (概念層) | ⚠️ 我們缺乏標準化的 hooks.json |
| **Agent 角色數量** | 44 個專職角色 | 7 個拓樸節點 (N1-N7) | ⚠️ 我們較粗粒度 |
| **Skills 庫** | 100+ 模組 | ~300+ 外部 Skills | ✅ 我們更豐富（但非內建） |
| **語言覆蓋** | 14 種語言 | Python 為主 | ⚠️ 我們的多語言支援較弱 |
| **安裝工具** | `install.sh` 腳本 | 手動配置 | ⚠️ 我們缺乏自動化安裝 |
| **版本控制整合** | Git-native (`.gemini/` 目錄) | 混合式 | ⚠️ 我們需要更清晰的目錄規約 |

### 4.3 可借鑑的設計模式

1. **CSS Specificity 規則優先順序**: 通用 < 語言專屬 < 專案覆寫。可直接映射至我們的 `user_global → hermes-agent.md → 任務覆寫` 三層體系。

2. **PostToolUse Hooks 標準化**: 將 linter/formatter/test 自動觸發機制從概念層落地為 `hooks.json` 配置檔，讓每個工具操作後自動驗證程式碼品質。

3. **Rules vs Skills 分離**: 明確區分「規約 (What)」與「執行指南 (How)」，避免規則文件過於冗長。我們目前的 `user_rules` 混合了兩者，可參考此模式拆分。

4. **Agent 角色細粒度化**: 44 個專職角色比我們的 7 個拓樸節點細粒度得多。可考慮在 N3 下轄建立語言專屬的 sub-agent 角色（如 Python-Reviewer、TypeScript-Reviewer）。

5. **No-Flatten 原則**: 目錄結構中的相對路徑引用（`../common/`）是一個精妙的設計，確保了繼承鏈的完整性。

---

## 5. 結論與下一步行動建議

### 5.1 立即可用 (Quick Wins)

- [ ] 引入 `rules/common/security.md` 的安全規約至 N7 的 pre-flight 檢查
- [ ] 建立 `hooks.json` 標準格式，定義 N7 的 PostToolUse 自動驗證機制

### 5.2 中期規劃

- [ ] 基於 `agent-harness-construction` 和 `autonomous-agent-harness` skill 模組，設計 Jasper Hub 的 Harness 配置標準
- [ ] 建立語言專屬的 sub-agent 角色（至少涵蓋 Python、TypeScript）

### 5.3 長期願景

- [ ] 開發 `install.sh` 等價的自動化安裝工具，讓 N1-N7 的規則集可一鍵部署
- [ ] 建立 Skill 市集機制，允許跨專案複用 Skills

---

## 附錄 A：原始資料索引

| 資料來源 | 爬取內容 | 分析重點 |
|---|---|---|
| [GEMINI.md](https://github.com/Jamkris/everything-gemini-code/blob/main/GEMINI.md) | 專案核心指南 | 編碼原則、品質標準 |
| [agents/](https://github.com/Jamkris/everything-gemini-code/tree/main/agents) | 44 個 Agent 角色定義 | 職責邊界、專長分類 |
| [hooks/](https://github.com/Jamkris/everything-gemini-code/tree/main/hooks) | hooks.json 配置 | PostToolUse 事件機制 |
| [rules/](https://github.com/Jamkris/everything-gemini-code/tree/main/rules) | 14 語言 + common 規則集 | 階層繼承、優先順序 |
| [skills/](https://github.com/Jamkris/everything-gemini-code/tree/main/skills) | 100+ 技能模組 | 分類、深度指南 |
| [rules/README.md](https://github.com/Jamkris/everything-gemini-code/blob/main/rules/README.md) | 安裝與配置文件 | 目錄規約、No-Flatten 原則 |
