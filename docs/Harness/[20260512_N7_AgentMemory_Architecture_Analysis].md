# N7 架構分析報告：AgentMemory

> **日期**：2026-05-12
> **來源**：https://github.com/rohitg00/agentmemory (v0.9.9)
> **分析師**：N7 Hermes Agent (Evaluator Protocol)
> **報告編號**：#6（追加於 N6 記憶層技術調研系列）

---

## 1. 專案概況

| 屬性 | 值 |
|------|-----|
| **名稱** | agentmemory |
| **定位** | Persistent memory for AI coding agents |
| **底層引擎** | [iii-engine](https://github.com/iii-hq/iii) (Rust 原生二進位) |
| **語言** | TypeScript 82.2%, HTML 8.9%, JS 6.8% |
| **規模** | 118 原始碼檔 · ~21,800 LOC · 800 測試 · 123 functions · 34 KV scopes |
| **授權** | Apache-2.0 |
| **Stars / Forks** | 4.9K / 459 |
| **Releases** | 31 (最新 v0.9.9, 2026-05-11) |
| **設計哲學** | 延伸 Karpathy LLM Wiki 模式 + 信心評分 + 生命週期 + 知識圖譜 + 混合搜尋 |

---

## 2. 記憶模型深度解析

### 2.1 四階記憶固化 (4-Tier Memory Consolidation)

受人腦睡眠固化機制啟發：

```
Working Memory → Episodic Memory → Semantic Memory → Procedural Memory
  (即時觀測)     (會話級摘要)      (跨會話事實)      (模式與規則)
```

- **記憶衰減**：Ebbinghaus 遺忘曲線，頻繁存取的記憶自動強化
- **陳舊記憶自動淘汰**：透過 decay sweep 定期清理
- **矛盾偵測與解決**：系統內建（但實作深度待確認）

### 2.2 記憶管線 (Memory Pipeline)

```
PostToolUse hook 觸發
  → SHA-256 去重 (5 分鐘窗口)
  → 隱私過濾 (移除 secrets / API keys)
  → 儲存原始觀測
  → LLM 壓縮 → 結構化 facts + concepts + narrative
  → 向量嵌入 (6 種 provider + 本地)
  → 索引至 BM25 + 向量存儲

Session 結束時：
  → 會話摘要
  → 知識圖譜抽取 (GRAPH_EXTRACTION_ENABLED)
  → Slot 反思 (SLOT_REFLECT_ENABLED)

Session 開始時：
  → 載入專案 Profile
  → 混合搜尋 (BM25 + Vector + Graph)
  → Token 預算控制 (預設 2000 tokens)
  → 注入對話上下文
```

### 2.3 搜尋策略

**三流混合檢索 (Triple-Stream Retrieval)**：
1. **BM25 全文搜尋**：關鍵字精確匹配
2. **向量語義搜尋**：`all-MiniLM-L6-v2` (本地免費) 或 6 種雲端 provider
3. **知識圖譜查詢**：實體抽取 + BFS 遍歷

融合策略：**Reciprocal Rank Fusion (RRF, k=60)** + session-diversified (每 session 最多 3 結果)

### 2.4 持久化

- **底層**：iii-engine (Rust binary) 提供 KV State、Streams、Functions、Triggers
- **無外部資料庫依賴**：不需要 PostgreSQL、Qdrant、Redis
- **Docker 備選**：`docker-compose.yml` 內含 `iiidev/iii:0.11.2`

---

## 3. 整合能力

### 3.1 MCP Server

- **51 個 MCP 工具**（core 模式 8 個 / all 模式 51 個）
- **6 個 Resources**、**3 個 Prompts**、**4 個 Skills**
- 支援所有實作 MCP 協定的 Agent

### 3.2 REST API

- **107 個端點** (port 3111)
- 支援 `AGENTMEMORY_SECRET` Bearer Token 認證
- 綁定 `127.0.0.1`

### 3.3 Hook System

12 個生命週期 Hooks：
`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PreCompact`, `SubagentStart/Stop`, `Stop`, `SessionEnd`

### 3.4 Agent 相容性

| Agent | 整合方式 |
|-------|---------|
| Claude Code | Plugin (hooks + MCP) |
| Cursor | MCP config |
| Gemini CLI | MCP config |
| Codex CLI | MCP config |
| Hermes | config.yaml + memory provider plugin |
| OpenCode | MCP config |
| OpenClaw | Plugin + MCP |
| Any MCP client | 通用 MCP |

### 3.5 多 Agent 協調

- **Leases**：分散式鎖定
- **Signals**：Agent 間訊號傳遞
- **Mesh Sync**：跨實例記憶同步
- **Checkpoints**：狀態快照

---

## 4. 基準測試

### 4.1 LongMemEval-S (ICLR 2025, 500 questions)

| 配置 | R@5 |
|------|-----|
| agentmemory (BM25 + Vector) | **95.2%** |
| agentmemory (BM25-only) | 86.2% |
| MemPalace (Vector-only, 較大模型) | ~96.6% |

> ⚠️ **跨基準警告**：Letta (83.2%) 和 Mem0 (68.5%) 使用 LoCoMo 基準，非同一基準無法直接比較。

### 4.2 Token 效率

| 策略 | Tokens/年 | 費用/年 |
|------|-----------|--------|
| 全歷史貼入上下文 | 19.5M+ | 不可行 |
| LLM 摘要式記憶 | ~650K | ~$500 |
| **agentmemory (API 嵌入)** | **~170K** | **~$10** |
| **agentmemory (本地嵌入)** | **~170K** | **$0** |

---

## 5. 可觀測性

- **即時檢視器** (port 3113)：記憶瀏覽器、知識圖譜視覺化、健康儀表板
- **iii Console** (port 3114)：OpenTelemetry 追蹤瀑布圖、KV 編輯器
- **Session Replay**：時間軸回放，支援 0.5×–4× 速度控制
- **稽核軌跡**：所有變異操作均記錄

---

## 6. 與 Hermes 現有機制對照

| 維度 | agentmemory | Hermes 現狀 | 缺口/互補 |
|------|-------------|------------|-----------|
| Raw Sources | ✅ Hook 自動擷取 | ✅ `data\workspace\` | agentmemory 更自動化 |
| Wiki Layer | 4-tier consolidation | `docs/Harness/` 報告 | agentmemory 更結構化 |
| Schema Layer | Slot system (8 slots) | GEMINI.md + per-project rules | 功能對映但設計不同 |
| index.md | ❌ 無（用 profile 替代） | ❌ **缺失** | 兩者皆缺，但 agentmemory 用 profile 補償 |
| log.md | ✅ 觀測流 (append-only) | ✅ `.planning/` | 功能等價 |
| Lint 操作 | ❌ 無內建 | N7 四維評估 + gsd-health | Hermes 佔優 |
| 矛盾偵測 | ✅ 內建（宣稱） | ❌ 缺失 | agentmemory 填補此缺口 |
| 記憶衰減 | ✅ Ebbinghaus | ❌ 無 | agentmemory 獨有 |
| 知識圖譜 | ✅ 實體抽取 + BFS | ❌ 無 | agentmemory 獨有 |
| MCP 整合 | ✅ 原生 | ✅ 已有 MCP 工具鏈 | 可直接對接 |
| 搜尋 | BM25 + Vector + Graph | 無記憶搜尋 | agentmemory 完整填補 |
| 隱私過濾 | ✅ 自動移除 secrets | ❌ 無 | agentmemory 獨有 |

---

## 7. 技術批評（反討好辯證）

### 7.1 重大疑慮

1. **iii-engine 黑箱依賴**：核心持久化完全依賴 iii-engine (Rust binary)，該引擎非開源核心元件，而是獨立專案。若 iii-hq 停止維護，agentmemory 將失去基礎設施。版本鎖定 (v0.11.2) 已經暴露了 `v0.11.6` 的 breaking change 問題。
2. **DESIGN.md 內容錯誤**：repo 中的 `DESIGN.md` 實際內容為 Lamborghini 網站設計系統規格，與 agentmemory 完全無關。這是**嚴重的文件管理疏失**，暗示文件品質控管不足。
3. **基準測試不可比**：自報的 95.2% R@5 使用 LongMemEval-S，而競品使用 LoCoMo。跨基準比較在學術上不成立，但 README 仍隱含優越性暗示。
4. **TypeScript 生態鎖定**：118 個 TS 原始碼檔 + iii-engine Rust 二進位。對 Hermes (Python 生態) 而言，深度整合需要跨語言橋接。
5. **複雜度爆炸**：51 個 MCP 工具 + 107 個 REST 端點 + 34 KV scopes + 123 functions。對 N6 的輕量化目標而言，過度工程化的風險極高。
6. **LLM 壓縮的 Token 消耗**：`AGENTMEMORY_AUTO_COMPRESS` 預設 OFF，README 警告「expect significant token spend on active sessions」。啟用核心功能需要額外的 LLM 費用。
7. **Windows 支援脆弱**：需要手動下載 iii-engine binary 或 Docker Desktop，無 scoop/winget 整合。

### 7.2 潛在優勢

1. **零外部資料庫**：不需要 PostgreSQL/Qdrant/Redis，降低基礎設施複雜度
2. **Hook 自動擷取**：12 個生命週期 hook 實現完全無侵入式記憶擷取
3. **混合搜尋 RRF 融合**：三流檢索 + RRF 在理論上優於任何單一策略
4. **多 Agent 協調**：Leases + Signals + Mesh 是調研方案中最成熟的多 Agent 方案
5. **隱私過濾**：自動移除 API keys/secrets，其他方案均缺乏此功能
6. **Hermes 官方整合**：已內建 `integrations/hermes/` 目錄，6-hook 記憶提供者整合

---

## 8. N7 四維評估

### 8.1 品質 (Quality) — 4/5

**優勢**：800 測試、LongMemEval 基準測試、SHA-256 去重、隱私過濾、稽核軌跡
**缺陷**：DESIGN.md 內容錯誤暴露文件品質控管不足；跨基準比較方法學有瑕疵；iii-engine 版本鎖定問題

### 8.2 原創性 (Originality) — 4.5/5

**優勢**：4-tier 記憶固化模型（Working→Episodic→Semantic→Procedural）獨特且具理論基礎；Ebbinghaus 衰減曲線應用於 AI 記憶屬首創；RRF 三流融合搜尋；Hook 自動擷取模式
**缺陷**：自述為「延伸 Karpathy LLM Wiki 模式」，部分概念非原創

### 8.3 工藝 (Craftsmanship) — 3.5/5

**優勢**：TypeScript 為主 + Rust 引擎的效能取向設計；完整的可觀測性堆疊 (OTEL)；31 個版本迭代
**缺陷**：DESIGN.md 嚴重文件錯誤；51 個 MCP 工具的命名高度冗餘 (memory_* 前綴佔全部)；對 Python 生態的侵入式跨語言依賴

### 8.4 功能性 (Functionality) — 4.5/5

**優勢**：最完整的 MCP 記憶工具集 (51 工具)；跨 Agent 相容 (8+ agent)；多 Agent 協調原語 (leases/signals/mesh)；即時檢視器 + Session Replay
**缺陷**：Windows 安裝體驗差；核心壓縮功能預設 OFF 且需額外 LLM 費用

### 四維均分：**4.125 / 5**

---

## 9. 六大方案更新比較矩陣

| 維度 | Mem0 | memU | MemPalace | Letta | Karpathy Wiki | **agentmemory** |
|------|------|------|-----------|-------|---------------|-----------------|
| **記憶模型** | Graph Memory (Neo4j) | Flat Markdown Wiki | Obsidian Vault | Memory Blocks + Archival | 三層：Raw→Wiki→Schema | **四階固化 + Ebbinghaus 衰減** |
| **持久化** | PostgreSQL + Qdrant | `.claude/` Markdown | Obsidian Vault | SQLModel + pg_vector | 純 Markdown + Git | **iii-engine KV (Rust binary)** |
| **搜尋** | 向量 + 圖混合 | BM25 全文 | Obsidian 原生 | SQL + 向量 | index.md + qmd | **BM25 + Vector + Graph (RRF)** |
| **Agent 整合** | REST API / SDK | Claude Code Slash Cmd | MCP Server | Python SDK + MCP | Idea File | **MCP (51 tools) + REST (107 ep) + Hooks (12)** |
| **多 Agent** | ✅ user/agent/session | ❌ 單 Agent | ❌ 單用戶 | ✅ Supervisor/Worker | ❌ 無 | **✅ Leases + Signals + Mesh** |
| **矛盾偵測** | ❌ | ❌ | ❌ | ❌ | 概念 (Lint) | **✅ 內建（Jaccard-based supersession）** |
| **記憶衰減** | ❌ | ❌ | ❌ | ❌ | ❌ | **✅ Ebbinghaus + tiered** |
| **隱私過濾** | ❌ | ❌ | ❌ | ❌ | ❌ | **✅ 自動移除 secrets** |
| **成熟度** | 高（商業產品） | 低（個人專案） | 中 | 高（Y Combinator） | N/A（設計模式） | **中高（31 releases, 4.9K stars）** |
| **外部依賴** | PostgreSQL+Qdrant | 無 | Obsidian | PostgreSQL+pg_vector | 無 | **iii-engine (Rust binary)** |
| **N7 評分** | 3.875 | 4.125 | 3.75 | 4.0 | 4.125 | **4.125** |

---

## 10. 對 N6 設計的啟示

| # | 啟示 | 可行性 | 說明 |
|---|------|--------|------|
| 1 | **4-Tier 記憶固化模型** | 高 | Working→Episodic→Semantic→Procedural 分層與 N6 Event Sourcing 設計高度吻合 |
| 2 | **Ebbinghaus 記憶衰減** | 高 | 可直接移植至 N6，解決記憶膨脹問題 |
| 3 | **RRF 三流融合搜尋** | 中 | BM25+Vector+Graph 的 RRF 融合是目前最佳實踐，但需 embedding infrastructure |
| 4 | **Hook 自動擷取** | 高 | Hermes 已有 hook 系統，可直接對接 agentmemory 的 12 hook 模式 |
| 5 | **隱私過濾管線** | 高 | 在 N7 安全體系下，Pre-store 隱私過濾為必備功能 |
| 6 | **直接整合 vs 概念移植** | 待決策 | agentmemory 已有 `integrations/hermes/` 整合，可作為 N6 的快速啟動方案；或僅移植核心概念至 Python 原生實作 |

### 關鍵決策點

> **路徑 A — 直接整合 agentmemory**：
> - 優勢：快速啟動、完整的 MCP 工具集、已有 Hermes 整合
> - 風險：iii-engine 黑箱依賴、TypeScript/Rust 跨語言維護、Windows 安裝障礙
>
> **路徑 B — 概念移植至 Python 原生實作**：
> - 優勢：完全掌控、與 Hermes Python 生態一致、無外部依賴
> - 風險：開發時間長、需自行實作 4-tier consolidation + RRF + Graph
>
> **路徑 C — 混合方案**：
> - 以 agentmemory 作為 MCP 外掛快速驗證 → 確認需求後逐步替換為 Python 原生實作

---

## 11. 結論

agentmemory 是目前調研的 6 個方案中**功能最完整**的記憶層實作，在多 Agent 協調、搜尋策略、記憶固化模型三個面向均為領先。其 Hermes 官方整合降低了採用門檻。

然而，其核心依賴 iii-engine (Rust binary) 構成了**不可控的單點故障**。DESIGN.md 的嚴重文件錯誤、跨基準比較的方法學瑕疵，以及 51 個 MCP 工具的過度工程化傾向，均為值得警惕的信號。

**建議**：將 agentmemory 列為 N6 架構設計的**重要參考**，但**不建議直接採用為核心依賴**。其 4-tier consolidation model 和 Ebbinghaus decay 的概念設計值得移植至 Python 原生實作。若需快速原型驗證，可透過 MCP 外掛方式進行短期試用。

---

> **信心標注**：中（README + COMPARISON.md 為主要資料來源，未實際執行基準測試驗證）
> **反面論證已提出**：§7 技術批評 7 項疑慮
> **LOW_CONFIDENCE 項目**：矛盾偵測的實作深度（僅有 Jaccard-based supersession 描述，無程式碼驗證）
