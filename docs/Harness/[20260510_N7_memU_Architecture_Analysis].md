# memU 架構分析報告

> **文件類型**: Clean Room 技術研究報告  
> **分析者**: N7 (Hermes Agent — Evaluator)  
> **日期**: 2026-05-10  
> **來源**: [NevaMind-AI/memU](https://github.com/NevaMind-AI/memU) (GitHub 開源版)  
> **分析對象**: `service.py`, `memorize.py`, `retrieve.py`, `pipeline.py`, `models.py`, `settings.py`, README  
> **目的**: 為 N6 Mem_Agent 架構設計提供乾淨室基準參照

---

## 1. 系統定位與設計哲學

### 1.1 核心身份

memU 自我定位為**面向 24/7 主動式代理的記憶框架**，強調「記憶即檔案系統」隱喻。其設計哲學與前兩份分析對象形成三角對比：

| 面向 | memU | Mem0 (對照) | claude-mem (對照) |
|---|---|---|---|
| **架構模式** | Workflow Pipeline（可插拔步驟） | 函式庫/SDK（嵌入式） | Daemon Agent（獨立程序） |
| **核心隱喻** | 記憶即檔案系統 | 通用記憶層 | 3-Layer 漸進式揭露 |
| **記憶提取** | 多模態 Ingest → LLM Extract → Category | `memory.add()` 單次呼叫 | 對話 Hook（自動） |
| **儲存後端** | In-Memory / Pluggable DB + LocalFS | 向量資料庫 + SQLite | Markdown + 日誌 |
| **關鍵差異化** | 主動式意圖預測 + 成本優化 | 三訊號融合檢索 | 零設定 Hook |

### 1.2 設計哲學核心

memU 採用**「記憶即檔案系統 (Memory as File System)」**隱喻：

| 檔案系統概念 | memU 對應 |
|---|---|
| 📁 資料夾 | 🏷️ Categories（自動組織的主題） |
| 📄 檔案 | 🧠 Memory Items（提取的事實/偏好/技能） |
| 🔗 符號連結 | 🔄 Cross-references（`[ref:xxx]` 標記） |
| 📂 掛載點 | 📥 Resources（對話/文件/影像/音訊） |

此隱喻帶來兩個核心承諾：
1. **可導航性**: 記憶可像目錄一樣從粗到細瀏覽（Category → Items）
2. **可移植性**: 記憶可匯出、備份、轉移——如同檔案

> **與 Mem0 的根本差異**: Mem0 將記憶視為「事實陳述的平坦集合」；memU 將記憶視為「層次化的知識樹」。

---

## 2. 記憶類型分層架構

### 2.1 MemoryType 列舉

`models.py` 定義了 6 種記憶類型：

```python
MemoryType = Literal["profile", "event", "knowledge", "behavior", "skill", "tool"]
```

| 類型 | 說明 | 對應 Mem0 |
|---|---|---|
| `profile` | 使用者個人資料、偏好 | Factual Memory |
| `event` | 時間錨定事件 | Episodic Memory |
| `knowledge` | 領域知識、事實 | Semantic Memory |
| `behavior` | 行為模式、習慣 | 無直接對應 |
| `skill` | 學習到的技能 | 無直接對應 |
| `tool` | 工具呼叫歷史與效能 | Procedural Memory |

### 2.2 ToolCallResult（工具記憶）

memU 對工具記憶有專門的資料模型：

```python
class ToolCallResult(BaseModel):
    tool_name: str
    input: dict | str
    output: str
    success: bool
    time_cost: float      # 執行耗時（秒）
    token_cost: int       # Token 消耗
    score: float          # 品質分數 0.0-1.0
    call_hash: str        # 輸入+輸出 MD5（去重用）
```

> **N6 設計啟示**: 此模型直接對應我們 N3/N7 的工具呼叫追蹤需求。`score` 和 `time_cost` 欄位可用於 Agent 效能優化。

### 2.3 三層實體模型

```
Resource (掛載點)
  └── MemoryItem (記憶條目)
        └── CategoryItem (分類關聯)
              └── MemoryCategory (主題分類)
```

每個實體都繼承 `BaseRecord`，具備 `id`（UUID）、`created_at`、`updated_at` 欄位。

---

## 3. Memorize Pipeline（核心寫入引擎）

### 3.1 七步工作流

`_build_memorize_workflow()` 定義了 **7 個 WorkflowStep**：

```
Step 1: ingest_resource    (IO)
  ↓   fetch resource → local_path + raw_text
Step 2: preprocess_multimodal  (LLM)
  ↓   模態分發 → 預處理文本 + caption
Step 3: extract_items      (LLM)
  ↓   結構化記憶提取 → XML 解析
Step 4: dedupe_merge       (CPU)
  ↓   去重/合併（目前為 placeholder）
Step 5: categorize_items   (DB+Vector)
  ↓   嵌入 + 持久化 + 分類關聯
Step 6: persist_index      (DB+LLM)
  ↓   更新分類摘要 + 項目引用
Step 7: build_response     (CPU)
  ↓   組裝回傳結構
```

### 3.2 關鍵設計特點

#### (a) 多模態原生支援

memU 在 Step 2 原生支援 5 種模態：

| 模態 | 處理方式 |
|---|---|
| `conversation` | 索引標記 + 分段摘要 |
| `document` | LLM 壓縮 + caption |
| `image` | Vision API 分析 |
| `video` | FFmpeg 中間幀提取 → Vision |
| `audio` | 語音轉文字 → 文字流程 |

> **vs Mem0**: Mem0 僅處理文字訊息。memU 的多模態是原生設計而非後期擴充。

#### (b) XML 結構化提取

Step 3 使用 XML 格式（非 JSON）進行 LLM 提取，每個記憶類型有獨立的提示模板：

```xml
<profile>
  <memory>
    <content>使用者偏好深色模式</content>
    <categories>
      <category>preferences</category>
    </categories>
  </memory>
</profile>
```

提取使用 `defusedxml` 解析，防範 XML 注入攻擊。

#### (c) 內容雜湊去重

```python
def compute_content_hash(summary: str, memory_type: str) -> str:
    normalized = " ".join(summary.lower().split())
    content = f"{memory_type}:{normalized}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]
```

- 使用 SHA-256（比 Mem0 的 MD5 更安全）
- 正規化空白字元
- 支援 `enable_item_reinforcement` 模式：重複內容不建立新條目，而是增加 `reinforcement_count`

#### (d) 分類摘要的增量更新

Step 6 使用 LLM 增量更新分類摘要，支援 `[ref:xxx]` 項目引用：

```python
# 為每個新記憶生成短 ID
def _build_item_ref_id(self, item_id: str) -> str:
    return item_id.replace("-", "")[:6]

# 帶引用的摘要提示格式
"- [a1b2c3] 使用者偏好深色模式"
```

引用被持久化到 `MemoryItem.extra["ref_id"]`，供檢索時精確定位。

---

## 4. Retrieve Pipeline（核心檢索引擎）

### 4.1 雙模式檢索

memU 提供 **RAG** 和 **LLM** 兩種檢索模式，由 `retrieve_config.method` 控制：

```
RAG 模式: 向量搜尋 + cosine 排序（快速、低成本）
LLM 模式: LLM 語義排序（精確、高成本）
```

### 4.2 三層漸進揭露（與 claude-mem 對齊）

兩種模式都遵循相同的三層檢索架構：

```
Tier 1: Categories (粗粒度主題)
  ↓ sufficiency_check → 足夠? → 返回
  ↓ 不足 → query rewrite
Tier 2: Items (細粒度記憶條目)
  ↓ sufficiency_check → 足夠? → 返回
  ↓ 不足 → query rewrite
Tier 3: Resources (原始資源)
  ↓ 返回完整結果
```

### 4.3 充分性檢查（Sufficiency Check）

每層檢索後，使用 LLM 判斷已取回的內容是否足夠回答查詢：

```python
async def _decide_if_retrieval_needed(self, query, context_queries, retrieved_content):
    # 返回 (needs_more: bool, rewritten_query: str)
    # 決策: RETRIEVE 或 NO_RETRIEVE
    # 附帶: 重寫後的查詢（用於下一層）
```

**設計亮點**：
- **查詢重寫 (Query Rewrite)**: 每層不足時，LLM 重寫查詢聚焦於缺失資訊
- **漸進式上下文**: 每層的 `retrieved_content` 包含前面所有層的結果
- **Route Intention**: 可在第一步就判斷是否需要記憶檢索（跳過閒聊）

### 4.4 RAG 模式的向量搜尋

```python
# 分類層: 對分類摘要做 embedding 搜尋
summary_embeddings = await client.embed(summary_texts)
hits = cosine_topk(query_vec, corpus, k=top_k)

# 項目層: 支援混合排序
store.memory_item_repo.vector_search_items(
    qvec, top_k,
    ranking=config.item.ranking,           # 排序策略
    recency_decay_days=config.item.recency_decay_days  # 時效衰減
)
```

> **vs Mem0**: memU 的 RAG 模式支援 `recency_decay_days` 時效衰減，這是 Mem0 缺少的「記憶遺忘」機制。

### 4.5 LLM 模式的引用追蹤

LLM 模式新增了 `use_category_references` 功能：

```python
if use_refs and category_hits:
    for cat in category_hits:
        ref_ids.extend(extract_references(cat.get("summary", "")))
    items_pool = store.memory_item_repo.list_items_by_ref_ids(ref_ids)
```

分類摘要中的 `[ref:xxx]` 引用直接定位到具體記憶條目，避免全量搜尋。

---

## 5. Workflow Pipeline 架構

### 5.1 PipelineManager

memU 的核心創新在於其**可插拔的工作流管線引擎**：

```python
class PipelineManager:
    def register(name, steps, initial_state_keys)  # 註冊管線
    def build(name) -> list[WorkflowStep]           # 建構步驟
    def config_step(name, step_id, configs)          # 動態配置
    def insert_after/before(name, target, new_step)  # 動態插入
    def replace_step(name, target, new_step)         # 替換步驟
    def remove_step(name, target)                    # 移除步驟
```

### 5.2 WorkflowStep 定義

```python
@dataclass
class WorkflowStep:
    step_id: str              # 唯一標識
    role: str                 # 職責角色
    handler: Callable         # 處理函式
    requires: set[str]        # 需要的 state keys
    produces: set[str]        # 產出的 state keys
    capabilities: set[str]    # 需要的能力（llm, vector, db, io, vision）
    config: dict              # 步驟配置（含 LLM profile）
```

### 5.3 靜態驗證

`_validate_steps()` 在註冊時進行**靜態依賴圖驗證**：

1. **步驟 ID 唯一性**: 禁止重複 `step_id`
2. **能力檢查**: 步驟要求的 capabilities 必須在可用集合內
3. **LLM Profile 檢查**: 引用的 profile 必須已註冊
4. **依賴鏈驗證**: 每步的 `requires` 必須由前序步驟的 `produces` 或初始 state 提供

### 5.4 版本追蹤

```python
@dataclass
class PipelineRevision:
    name: str
    revision: int
    steps: list[WorkflowStep]
    created_at: float
```

每次管線修改都產生新的 `PipelineRevision`，支援審計追蹤。

> **N6 設計啟示**: 此管線架構是三個框架中最成熟的。靜態依賴驗證和版本追蹤直接對應 N9 Entropy Guardian 的審計需求。

---

## 6. 攔截器系統 (Interceptor System)

### 6.1 LLM 攔截器

```python
service.intercept_before_llm_call(fn, name, priority, where)
service.intercept_after_llm_call(fn, name, priority, where)
service.intercept_on_error_llm_call(fn, name, priority, where)
```

- **優先級排序**: `priority` 控制執行順序
- **條件過濾**: `where` 可按 profile/operation 過濾
- **LLMCallMetadata**: 每次呼叫攜帶 `profile`, `operation`, `step_id`, `trace_id`, `tags`

### 6.2 Workflow 攔截器

```python
service.intercept_before_workflow_step(fn, name)
service.intercept_after_workflow_step(fn, name)
service.intercept_on_error_workflow_step(fn, name)
```

> **N6 設計啟示**: 攔截器模式直接可用於 N9 的遙測接入。在每個 workflow step 的 before/after 注入遙測邏輯，無需修改業務代碼。

---

## 7. 儲存架構

### 7.1 可插拔資料庫

```python
database = build_database(config=database_config, user_model=user_model)
```

支援配置驅動的後端切換，透過 `DatabaseConfig` 分離 metadata store 和 vector index：

```python
class DatabaseConfig:
    metadata_store: MetadataStoreConfig    # 記憶/分類/關聯
    vector_index: VectorIndexConfig | None  # 向量索引（可選）
```

### 7.2 User Scope（多租戶）

```python
def build_scoped_models(user_model):
    # 動態建立帶有 user scope 的 Pydantic 模型
    resource_model = merge_scope_model(user_model, Resource)
    memory_item_model = merge_scope_model(user_model, MemoryItem)
    # ...
```

所有 CRUD 操作透過 `user_data` 參數實現租戶隔離。

### 7.3 LocalFS Blob 儲存

```python
self.fs = LocalFS(blob_config.resources_dir)
local_path, raw_text = await self.fs.fetch(resource_url, modality)
```

資源檔案（圖片/影片/音訊）下載到本地檔案系統，與記憶元資料分離。

---

## 8. N7 四維評估

### 8.1 評分矩陣

| 維度 | 分數 | 分析 |
|---|---|---|
| **品質 (Quality)** | 4.0/5 | Workflow Pipeline 的靜態依賴驗證設計嚴謹。SHA-256 去重優於 Mem0 的 MD5。XML 解析使用 `defusedxml` 防注入。扣分點：`dedupe_merge` 步驟仍為 placeholder，去重邏輯不完整。 |
| **原創性 (Originality)** | 4.5/5 | 「記憶即檔案系統」隱喻在同類框架中獨樹一幟。可插拔管線 + 攔截器 + 版本追蹤的組合設計具高度創新性。`[ref:xxx]` 引用系統將分類摘要與具體記憶精確連結，解決了「摘要失真」問題。 |
| **工藝 (Craftsmanship)** | 4.0/5 | 程式碼透過 Mixin 模式（MemorizeMixin / RetrieveMixin / CRUDMixin）實現關注點分離，遠優於 Mem0 的 3000 行 God Object。Pipeline 版本追蹤支援審計。扣分點：Mixin 間的 TYPE_CHECKING 依賴宣告繁瑣，增加維護成本。 |
| **功能性 (Functionality)** | 4.0/5 | 多模態原生支援（文字/圖片/影片/音訊/文件）。雙模式檢索（RAG/LLM）。動態管線修改。時效衰減（`recency_decay_days`）。扣分點：缺少 Entity Store（Mem0 的強項），跨記憶關聯僅靠 Category 間接實現。 |

**四維平均**: 4.125 / 5

### 8.2 必要缺陷指摘（反討好校準）

1. **dedupe_merge Placeholder**: Step 4 的去重邏輯為空殼（`state["resource_plans"] = state.get("resource_plans", [])`）。在高頻寫入場景下，相似但不完全相同的記憶會大量堆積。

2. **缺少 Entity Store**: 與 Mem0 的 Entity Linking 相比，memU 僅靠 Category 分類實現跨記憶關聯。缺少命名實體級別的關聯追蹤（例如：「Jasper」出現在多條記憶中時，無法自動建立實體關聯圖）。

3. **In-Memory 預設瓶頸**: `database/inmemory/` 預設將所有記憶載入記憶體。雖然支援可插拔後端，但官方示例未展示大規模儲存場景的最佳實踐。

4. **Reinforcement 語義模糊**: `enable_item_reinforcement` 將重複內容計數+1 而非建立新條目，但「語義相近但不完全相同」的情境未處理——SHA-256 hash 要求完全匹配。

---

## 9. 對 N6 設計的關鍵啟示

### 9.1 可採用的設計模式

| 模式 | memU 實作 | N6 適用場景 |
|---|---|---|
| **Workflow Pipeline** | 7 步可插拔管線 + 靜態驗證 | N6 的記憶寫入/檢索管線核心架構 |
| **Interceptor System** | before/after/on_error 三重攔截 | N9 遙測接入點 |
| **Pipeline Versioning** | PipelineRevision 追蹤 | N7 審計與回溯 |
| **Memory as FS** | Category/Item 層次化結構 | N6 的記憶導航模型 |
| **[ref:xxx] 引用** | 摘要到條目的精確連結 | N6 的漸進揭露精確定位 |
| **Recency Decay** | `recency_decay_days` 時效衰減 | N6 的記憶遺忘機制 |
| **Multi-Modal Ingest** | 5 種模態原生支援 | N6 對多模態工作區的支援 |

### 9.2 需調整的設計

| memU 設計 | 問題 | N6 改良方向 |
|---|---|---|
| In-Memory 預設 | 不可擴展 | SQLite FTS 作為預設後端 |
| 無 Entity Store | 跨記憶關聯弱 | 輕量 Entity Index（借鑑 Mem0） |
| dedupe_merge 空殼 | 去重不完整 | 實作語義去重（embedding 相似度門檻） |
| Mixin 模式 | TYPE_CHECKING 繁瑣 | 考慮 Composition over Inheritance |
| XML 提取格式 | 解析成本高 | JSON 結構化輸出（與 Mem0 對齊） |

### 9.3 三框架綜合對照

| 面向 | claude-mem | Mem0 | memU | N6 綜合策略 |
|---|---|---|---|---|
| **架構** | Daemon Agent | 嵌入式 SDK | Workflow Pipeline | Daemon + Pipeline |
| **擷取觸發** | 自動 Hook | 手動 API | 手動 API + 主動式 | Hook + 手動雙模式 |
| **儲存** | Markdown | 向量 DB | In-Memory/Pluggable | 雙寫（MD + SQLite） |
| **檢索** | 3-Layer 漸進 | 三訊號融合 | 3-Layer + 充分性檢查 | 3-Layer + BM25 + 充分性 |
| **實體關聯** | 無 | Entity Store | Category 間接 | 輕量 Entity Index |
| **多模態** | 無 | 無 | 5 種原生支援 | 文字為主 + 多模態擴充 |
| **管線可擴展** | 固定 Hook | 固定流水線 | 動態插拔 + 版本追蹤 | 動態管線 + N9 審計 |
| **遺忘機制** | 無 | 無 | recency_decay | TTL + 重要度衰減 |
| **Token 效率** | 高（漸進揭露） | 低（長提示） | 中（充分性檢查） | 漸進揭露 + 充分性 |

---

## 10. 結論與建議

memU 在三個框架中展現了**最成熟的工程架構**——其可插拔 Workflow Pipeline、攔截器系統、版本追蹤構成了完整的「記憶作業系統」骨架。「記憶即檔案系統」隱喻為 N6 提供了清晰的使用者心智模型。

**然而**，memU 在「智慧檢索」維度弱於 Mem0（缺少 Entity Store 和三訊號融合），在「零設定易用性」維度弱於 claude-mem（缺少 Daemon Hook）。

**建議 N6 設計採取的混合策略**：

1. **骨架**: memU 的 Workflow Pipeline + Interceptor 架構（最大可擴展性）
2. **觸發**: claude-mem 的 Daemon Hook（零設定自動擷取）
3. **提取**: Mem0 的精細提取提示（但縮短至 ≤200 行）+ memU 的多模態分發
4. **檢索**: memU 的 3-Layer + 充分性檢查 + Mem0 的 BM25 融合
5. **儲存**: 雙寫（Markdown for 人類 + SQLite FTS for 機器）
6. **關聯**: Mem0 的輕量 Entity Index + memU 的 `[ref:xxx]` 引用
7. **衰減**: memU 的 `recency_decay` + TTL + 重要度加權
8. **審計**: memU 的 Pipeline Versioning + Interceptor → N9 遙測

> **信心程度**: 高（基於直接原始碼分析與 README 交叉驗證）

---

*本報告基於 memU 開源版原始碼（`main` branch, 2026-05）進行乾淨室分析。*  
*分析過程嚴格遵循 N7 Evaluator Protocol，不受 N1 既有設計文件影響。*
