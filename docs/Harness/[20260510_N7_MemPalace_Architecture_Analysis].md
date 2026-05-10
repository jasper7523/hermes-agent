# MemPalace 架構分析報告

> **文件類型**: Clean Room 技術研究報告  
> **分析者**: N7 (Hermes Agent — Evaluator)  
> **日期**: 2026-05-10  
> **來源**: [MemPalace/mempalace](https://github.com/mempalace/mempalace) (GitHub 開源版)  
> **分析對象**: `palace.py`, `backends/base.py`, `knowledge_graph.py`, 官方文件  
> **目的**: 為 N6 Mem_Agent 架構設計提供乾淨室基準參照（第四份）

---

## 1. 系統定位與設計哲學

### 1.1 核心身份

MemPalace 自我定位為**「最佳基準的開源 AI 記憶系統」**，強調 Local-first、零 API 呼叫、逐字儲存（Verbatim Storage）。其設計靈感來自古希臘演說家的**記憶宮殿術 (Method of Loci)**——將記憶放置在想像建築物的房間中。

| 面向 | MemPalace | Mem0 | memU | claude-mem |
|---|---|---|---|---|
| **架構模式** | CLI + MCP Server | 嵌入式 SDK | Workflow Pipeline | Daemon Agent |
| **核心隱喻** | 記憶宮殿（Wing/Room/Drawer） | 通用記憶層 | 記憶即檔案系統 | 3-Layer 漸進揭露 |
| **記憶策略** | **逐字儲存（不摘要）** | LLM 提取事實 | LLM 提取+分類 | Hook 自動提取 |
| **LLM 依賴** | 零（核心路徑） | 重度（提取+搜尋） | 重度 | 中度 |
| **儲存後端** | ChromaDB（可插拔） | 向量 DB + SQLite | In-Memory/Pluggable | Markdown |
| **知識圖譜** | ✅ 時態三元組 SQLite | Entity Store（選配） | ❌ | ❌ |

### 1.2 設計哲學核心

MemPalace 採用**「逐字保真 (Verbatim Fidelity)」**策略——與 Mem0/memU 的「LLM 提取摘要」路線截然相反：

> *「MemPalace stores your conversation history as verbatim text and retrieves it with semantic search. It does not summarize, extract, or paraphrase.」*

**核心信念**：摘要會丟失資訊；逐字儲存 + 結構化索引 + 語義搜尋 = 更高的召回率。

此信念獲得基準數據支持：LongMemEval R@5 = **96.6%**（無 LLM），Hybrid v4 = **98.4%**。

> **反面論證（MW4）**：逐字儲存的 Token 成本在長期運行場景中顯著高於摘要式系統。96.6% 的基準表現可能部分歸因於 LongMemEval 任務本身偏好逐字匹配——在需要推論或跨文件綜合的場景中，摘要式系統可能表現更好。信心程度：中。

---

## 2. 記憶宮殿層次結構

### 2.1 五層空間隱喻

```
Palace (宮殿 = 一個專案/工作區)
├── Wing (翼 = 人物/專案/主題)
│   ├── Room (房間 = 具體主題，如 auth-migration)
│   │   └── Drawer (抽屜 = 逐字文本塊，主要檢索層)
│   └── Hall (大廳 = 概念分類)
│       ├── hall_facts      → 已鎖定的決策
│       ├── hall_events     → 會議/里程碑/除錯
│       ├── hall_discoveries → 突破/新洞察
│       ├── hall_preferences → 習慣/偏好
│       └── hall_advice     → 建議/解法
└── Tunnel (隧道 = Wing 間的跨域連結)
```

### 2.2 Closet 索引層

Closet 是 Drawer 之上的**摘要指標層**，格式為 `topic|entities|→drawer_ids`：

```python
CLOSET_CHAR_LIMIT = 1500   # 每個 closet 最多 ~1500 字元
CLOSET_EXTRACT_WINDOW = 5000  # 掃描前 5000 字元提取實體/主題
```

提取邏輯（純規則、無 LLM）：
1. **實體提取**: i18n 正規表達式找出專有名詞（≥2 次出現），支援多語言
2. **主題提取**: 動作動詞模式（built/fixed/wrote/…）+ 章節標題
3. **引用提取**: 雙引號內的文本片段（15-150 字元）

> **vs memU**: memU 用 LLM 做分類摘要；MemPalace 用純規則提取。成本為零但精度較低。

### 2.3 Tunnel 跨域連結

相同 Room 名稱出現在不同 Wing 時，系統自動建立 Tunnel 連結：

```
wing_kai/auth-migration → "Kai debugged OAuth token refresh"
wing_driftwood/auth-migration → "team decided to migrate to Clerk"
wing_priya/auth-migration → "Priya approved Clerk over Auth0"
```

MCP 工具 `mempalace_traverse` 和 `mempalace_find_tunnels` 支援圖遍歷。

---

## 3. 可插拔後端架構（RFC 001）

### 3.1 BaseBackend / BaseCollection ABC

MemPalace 定義了嚴格的**後端合約 (Backend Contract)**：

```python
class BaseCollection(ABC):
    def add(*, documents, ids, metadatas, embeddings) -> None
    def upsert(*, documents, ids, metadatas, embeddings) -> None
    def query(*, query_texts, query_embeddings, n_results, where) -> QueryResult
    def get(*, ids, where, limit, offset) -> GetResult
    def delete(*, ids, where) -> None
    def count() -> int
    # 可選: update(), estimated_count(), close(), health()

class BaseBackend(ABC):
    name: ClassVar[str]
    spec_version: ClassVar[str] = "1.0"
    capabilities: ClassVar[frozenset[str]]
    def get_collection(*, palace: PalaceRef, collection_name, create) -> BaseCollection
    def close_palace(palace: PalaceRef) -> None
    def health(palace: PalaceRef) -> HealthStatus
```

### 3.2 設計亮點

| 特點 | 說明 |
|---|---|
| **PalaceRef 抽象** | `id` + `local_path` + `namespace` 三元組，支援本地/雲端/多租戶 |
| **HealthStatus** | 每個後端/集合都有健康狀態檢查 |
| **Typed Results** | `QueryResult`/`GetResult` 取代 dict，帶 `_DictCompatMixin` 過渡層 |
| **UnsupportedFilterError** | 禁止靜默丟棄未知過濾運算子（spec §1.4） |
| **EmbedderIdentityMismatch** | 偵測嵌入模型更換後的向量不相容 |
| **kwargs-only** | 所有方法強制 keyword-only 參數 |

> **vs Mem0/memU**: MemPalace 的後端抽象是四個框架中**最正式的工程規格**（有 RFC 編號、spec 版本號、capabilities 聲明）。Mem0 直接耦合 Qdrant；memU 有可插拔設計但無正式 spec。

---

## 4. 時態知識圖譜

### 4.1 架構

MemPalace 的知識圖譜採用 **SQLite 儲存的時態三元組 (Temporal Triples)**：

```sql
entities (id, name, type, properties, created_at)
triples  (id, subject, predicate, object,
          valid_from, valid_to, confidence,
          source_closet, source_file, source_drawer_id)
```

### 4.2 核心操作

| 操作 | 方法 | 說明 |
|---|---|---|
| 新增事實 | `add_triple("Max", "child_of", "Alice", valid_from="2015-04")` | 自動建立不存在的實體 |
| 失效標記 | `invalidate("Max", "has_issue", "injury", ended="2026-02")` | 設定 `valid_to`，不刪除 |
| 時間查詢 | `query_entity("Max", as_of="2026-01-15")` | 只返回該時點有效的事實 |
| 關係查詢 | `query_relationship("works_on")` | 按謂語查所有三元組 |
| 時間線 | `timeline("Max")` | 按 `valid_from` 排序的事實列表 |

### 4.3 關鍵設計特點

1. **時態有效性窗口**: `valid_from` → `valid_to` 實現「事實何時為真」的時間推理
2. **軟失效 (Soft Invalidation)**: `invalidate()` 不刪除記錄，而是設定結束日期——支援歷史回溯
3. **來源追溯 (Provenance)**: 每個三元組追蹤 `source_closet` + `source_drawer_id`，可回溯到原始逐字記憶
4. **去重**: 相同 subject/predicate/object 且 `valid_to IS NULL` 的三元組不重複插入
5. **線程安全**: `threading.Lock` 保護所有讀寫操作
6. **WAL 模式**: SQLite 使用 WAL journal mode 提升並發性能

> **vs Mem0**: Mem0 的 Entity Store 只追蹤「實體連結到哪些記憶」，無時態維度。MemPalace 的時態三元組是四個框架中**唯一具備時間推理能力**的知識圖譜。

---

## 5. Mining 引擎（寫入管線）

### 5.1 雙重 Mining 模式

```bash
mempalace mine ~/projects/myapp                     # 專案檔案模式
mempalace mine ~/.claude/projects/ --mode convos     # 對話記錄模式
```

| 模式 | 觸發 | 去重策略 |
|---|---|---|
| 專案模式 | `check_mtime=True` | 檔案修改時間比對 |
| 對話模式 | `check_mtime=False` | 版本號 (`NORMALIZE_VERSION`) 比對 |

### 5.2 寫入流程

```
Source File
  ↓
mine_palace_lock() — 非阻塞鎖（每 palace 一把）
  ↓
file_already_mined() — 版本+mtime 檢查
  ↓
mine_lock() — 檔案級鎖（防止交錯 delete+insert）
  ↓
process_file()
  ├── 拆分為 Drawers（逐字文本塊）
  ├── 嵌入向量
  └── upsert 到 ChromaDB
  ↓
build_closet_lines() — 規則式主題/實體提取
  ↓
purge_file_closets() + upsert_closet_lines()
```

### 5.3 並發安全

MemPalace 實作了**兩層鎖機制**：

1. **Palace 級鎖** (`mine_palace_lock`): 非阻塞，防止多個 `mempalace mine` 同時操作同一 palace（會腐蝕 HNSW 圖）
2. **檔案級鎖** (`mine_lock`): 阻塞式，防止同一檔案的 delete+insert 交錯

跨平台支援：Windows 用 `msvcrt.locking`，Unix 用 `fcntl.flock`。

> **N6 設計啟示**: 此雙層鎖模式直接對應我們 Daemon 模式的並發寫入需求。

---

## 6. Auto-save Hooks

MemPalace 提供兩個 Claude Code Hooks：
1. **定期儲存**: 週期性將對話內容 mine 進 palace
2. **壓縮前儲存**: 在上下文壓縮觸發前搶救完整對話

`mempalace sweep <dir>` 命令實現逐訊息粒度的儲存（每條 user/assistant 訊息一個 Drawer），具備冪等性和斷點續傳。

---

## 7. N7 四維評估

### 7.1 評分矩陣

| 維度 | 分數 | 分析 |
|---|---|---|
| **品質 (Quality)** | 4.5/5 | RFC 001 後端合約設計嚴謹；雙層鎖機制完善；`EmbedderIdentityMismatch` 防護嵌入模型更換風險。Benchmark 可重現性高。扣分：Closet 實體提取為硬編碼正規表達式，無法處理複雜命名實體。 |
| **原創性 (Originality)** | 4.5/5 | 「逐字儲存 + 結構化索引」的反直覺策略在同類框架中獨樹一幟。時態知識圖譜（`valid_from`/`valid_to`）是四框架中唯一具備時間推理的設計。「記憶宮殿」隱喻（Wing/Room/Hall/Tunnel）比 memU 的檔案系統更貼近人類空間認知。 |
| **工藝 (Craftsmanship)** | 4.0/5 | 程式碼模組化清晰（palace/backend/kg 分離）；RFC 編號系統體現工程紀律。扣分：`palace.py` 混合了業務邏輯（closet building）和基礎設施（鎖機制），違反 SRP。`_DictCompatMixin` 過渡層增加認知負擔。 |
| **功能性 (Functionality)** | 4.0/5 | 29 個 MCP 工具覆蓋完整操作面；知識圖譜 CRUD + 時間查詢；跨平台鎖。扣分：核心路徑不使用 LLM，意味著「理解」能力弱——使用者必須知道要搜什麼詞才能找到記憶，缺乏 Mem0/memU 的意圖推理。 |

**四維平均**: 4.25 / 5

### 7.2 必要缺陷指摘（反討好校準）

1. **逐字儲存的 Token 爆炸**: 長期運行的 24/7 Agent 場景中，逐字儲存會導致向量資料庫膨脹。MemPalace 無原生的衰減/遺忘/壓縮機制。

2. **Closet 提取的規則脆弱性**: 實體提取依賴正規表達式（專有名詞 ≥2 次出現），無法處理：代詞指代（「他說」→ 誰？）、非拉丁語系的複雜命名實體、語義等價但文字不同的主題。

3. **無意圖推理**: 核心路徑不使用 LLM，無法像 memU 的 Sufficiency Check 那樣判斷「已取回的內容是否足夠回答問題」。搜尋品質完全依賴嵌入模型的語義理解和使用者的查詢品質。

4. **知識圖譜與主記憶分離**: KG 使用獨立 SQLite，Drawers 在 ChromaDB，兩者透過 `source_closet` / `source_drawer_id` 弱連結。缺乏統一的查詢介面——使用者需分別搜尋向量庫和圖譜。

---

## 8. 對 N6 設計的關鍵啟示

### 8.1 可採用的設計模式

| 模式 | MemPalace 實作 | N6 適用場景 |
|---|---|---|
| **時態知識圖譜** | `valid_from`/`valid_to` 三元組 | N6 的事實時效管理（偏好演進/決策撤回） |
| **RFC 後端合約** | BaseBackend/BaseCollection ABC | N6 儲存後端的正式介面定義 |
| **雙層鎖機制** | Palace 級 + 檔案級非阻塞鎖 | N6 Daemon 並發寫入防護 |
| **來源追溯** | `source_closet` → `source_drawer_id` | N6 記憶的可審計性（N9 需求） |
| **Hook 自動儲存** | Claude Code 定期/壓縮前 Hook | N6 的 Daemon Hook 觸發點設計 |
| **EmbedderIdentityMismatch** | 嵌入模型更換偵測 | N6 的模型漂移防護 |

### 8.2 需調整的設計

| MemPalace 設計 | 問題 | N6 改良方向 |
|---|---|---|
| 逐字儲存 | Token 爆炸 | 雙軌：逐字存檔 + LLM 摘要索引 |
| 規則式實體提取 | 精度不足 | LLM 輕量提取（借鑑 Mem0） |
| 無意圖推理 | 被動搜尋 | 充分性檢查（借鑑 memU） |
| KG 獨立分離 | 查詢割裂 | 統一查詢路由器 |
| 無記憶衰減 | 資料庫膨脹 | TTL + 重要度加權衰減 |

### 8.3 四框架最終綜合對照

| 面向 | claude-mem | Mem0 | memU | MemPalace | **N6 綜合策略** |
|---|---|---|---|---|---|
| **觸發** | 自動 Hook | 手動 API | 手動+主動 | CLI+Hook | **Hook+手動雙模式** |
| **儲存內容** | 摘要 | LLM 提取事實 | LLM 提取+分類 | 逐字文本 | **雙軌（摘要+逐字）** |
| **檢索** | 3-Layer 漸進 | 三訊號融合 | 3-Layer+充分性 | 語義+Hybrid | **3-Layer+BM25+充分性** |
| **知識圖譜** | ❌ | Entity Store | ❌ | 時態三元組 | **時態 Entity Index** |
| **LLM 依賴** | 中 | 重 | 重 | 零/可選 | **分層（輕量初篩+深度提取）** |
| **可插拔性** | 低 | 低 | 高（Pipeline） | 高（RFC ABC） | **Pipeline+RFC 合約** |
| **並發安全** | 無 | 無 | 無 | 雙層鎖 | **雙層鎖** |
| **時間推理** | ❌ | ❌ | recency_decay | valid_from/to | **時態有效性窗口** |
| **Benchmark** | 無 | 無 | 無 | 96.6% R@5 | **可重現基準測試** |

---

## 9. 結論與建議

MemPalace 在四個框架中展現了**最強的工程紀律**（RFC 系統、後端合約、雙層鎖、可重現 Benchmark）和**最獨特的設計哲學**（逐字保真 vs LLM 摘要）。其時態知識圖譜是唯一具備「事實何時為真」推理能力的實作。

**然而**，逐字儲存策略在 24/7 長時運行場景中面臨 Token 成本爆炸風險，且缺乏 LLM 驅動的意圖推理——這在「主動式記憶代理」定位中是致命短板。

**建議 N6 設計新增的借鑑**：

1. **時態知識圖譜**: 採用 MemPalace 的 `valid_from`/`valid_to` 三元組模式（SQLite 儲存），取代 Mem0 的無時態 Entity Store
2. **RFC 後端合約**: 採用 MemPalace 的 `BaseBackend`/`BaseCollection` ABC 作為 N6 儲存介面設計參考
3. **雙層鎖**: 採用 Palace 級 + 檔案級鎖模式保護 Daemon 並發寫入
4. **嵌入模型漂移防護**: 採用 `EmbedderIdentityMismatchError` 機制
5. **雙軌儲存**: 結合 MemPalace 的逐字保真（審計/回溯用）+ Mem0/memU 的 LLM 摘要（檢索/Token 優化用）

> **信心程度**: 高（基於直接原始碼分析、官方文件與 Benchmark 文件交叉驗證）

---

*本報告基於 MemPalace 開源版原始碼（v3.3.4, 2026-05）進行乾淨室分析。*  
*分析過程嚴格遵循 N7 Evaluator Protocol，不受 N1 既有設計文件影響。*
