# Mem0 架構分析報告

> **文件類型**: Clean Room 技術研究報告  
> **分析者**: N7 (Hermes Agent — Evaluator)  
> **日期**: 2026-05-10  
> **來源**: [mem0ai/mem0](https://github.com/mem0ai/mem0) (GitHub 開源版)  
> **分析對象**: `mem0/memory/main.py`, `mem0/configs/prompts.py`, `mem0/memory/utils.py`, 官方文件  
> **目的**: 為 N6 Mem_Agent 架構設計提供乾淨室基準參照

---

## 1. 系統定位與設計哲學

### 1.1 核心身份

Mem0 自我定位為**通用記憶層 (Universal Memory Layer)**，為 AI Agent 提供跨對話的持久化記憶能力。其設計哲學與 claude-mem 截然不同：

| 面向 | Mem0 | claude-mem (對照) |
|---|---|---|
| **架構模式** | 函式庫/SDK（嵌入式） | Daemon Agent（獨立程序） |
| **記憶提取時機** | `memory.add()` 主動呼叫 | 對話生命週期 Hook（自動） |
| **儲存後端** | 向量資料庫（Qdrant 等）+ SQLite | Markdown 檔案 + 日誌 |
| **記憶管理策略** | ADD-only（V3）/ CRUD（V2） | 3-Layer 漸進式揭露 |
| **實體關聯** | Entity Store + Graph（選配） | 無 |

### 1.2 設計哲學核心

Mem0 採用**「寧多勿缺」(Extract Everything)** 的激進策略。其 `ADDITIVE_EXTRACTION_PROMPT` 明確指出：

> *"When in doubt, extract. A slightly redundant memory is far less costly than a missing one. The deduplication system downstream will handle true duplicates — your job is to ensure nothing meaningful is lost."*

此策略將記憶品質控管委託給下游的 Hash 去重與向量搜尋排序，而非在提取階段就做嚴格的門控——與 claude-mem 傾向在 Hook 層做「是否值得記憶」的初篩形成鮮明對比。

---

## 2. 記憶類型分層架構

### 2.1 四層記憶模型

Mem0 官方文件定義了四種記憶層級，並以 `user_id` / `run_id` / `agent_id` 三組鍵來區隔作用域：

```
┌─────────────────────────────────────────┐
│  Layer 4: Organizational Memory         │
│  (共享知識：FAQ、產品目錄、政策)          │
│  Scope: 跨所有 agent / user             │
├─────────────────────────────────────────┤
│  Layer 3: User Memory (長期)            │
│  偏好、帳戶狀態、法遵細節               │
│  Scope: user_id                         │
├─────────────────────────────────────────┤
│  Layer 2: Session Memory (短期)         │
│  多步驟任務狀態、除錯脈絡               │
│  Scope: run_id                          │
├─────────────────────────────────────────┤
│  Layer 1: Conversation Memory (瞬時)    │
│  工具呼叫、思維鏈（CoT）                │
│  Scope: 當前對話回合                     │
└─────────────────────────────────────────┘
```

### 2.2 短期 vs 長期記憶

| 短期記憶類型 | 說明 |
|---|---|
| Conversation History | 最近的對話回合，維持連貫性 |
| Working Memory | 臨時狀態（工具輸出、中間計算） |
| Attention Context | 即時焦點（Agent 當前處理的事項） |

| 長期記憶類型 | 說明 |
|---|---|
| Factual Memory | 使用者偏好、帳戶細節、領域事實 |
| Episodic Memory | 過去互動的摘要、已完成任務 |
| Semantic Memory | 概念間關係（供推理用） |

### 2.3 Procedural Memory（程序性記憶）

Mem0 額外支援一種特殊記憶類型 `MemoryType.PROCEDURAL`，用 `PROCEDURAL_MEMORY_SYSTEM_PROMPT` 來總結 Agent 的執行歷史（N 步動作序列）。此類記憶要求：

- **逐字保存 (Verbatim Preservation)**: Agent 每一步的輸出必須原樣記錄
- **結構化步驟**: 每步包含 Agent Action → Action Result → Embedded Metadata（Key Findings / Errors / Context）
- **進度追蹤**: Global Metadata 包含任務目標 + 完成百分比

> **N6 設計啟示**: 此模式直接對應我們 Agent Hub 中 N3/N4 的工作日誌需求。但我們的場景更偏重「決策記憶」而非「動作日誌」。

---

## 3. V3 Phased Batch Pipeline（核心引擎剖析）

### 3.1 流水線總覽

`_add_to_vector_store()` 方法實作了一條 **8 階段批次處理流水線**：

```
Phase 0: Context Gathering
    ↓
Phase 1: Existing Memory Retrieval
    ↓
Phase 2: LLM Extraction (單次呼叫)
    ↓
Phase 3: Batch Embedding
    ↓
Phase 4-5: CPU Processing + Hash Dedup
    ↓
Phase 6: Batch Persist (Vector Store)
    ↓
Phase 7: Batch Entity Linking
    ↓
Phase 8: Save Messages + Return
```

### 3.2 各階段深度分析

#### Phase 0: Context Gathering
```python
session_scope = _build_session_scope(filters)
last_messages = self.db.get_last_messages(session_scope, limit=10)
parsed_messages = parse_messages(messages)
```
- 從 SQLite 取最近 10 條歷史訊息
- 組合成 `"role: content\n"` 格式的純文字

#### Phase 1: Existing Memory Retrieval
```python
query_embedding = self.embedding_model.embed(parsed_messages, "search")
existing_results = self.vector_store.search(
    query=parsed_messages, vectors=query_embedding, top_k=10, filters=search_filters
)
```
- **反幻覺設計**: 將 UUID 映射為整數索引 `{str(idx): mem.id}`，防止 LLM 在輸出中幻覺出不存在的 UUID
- 最多取 10 條相關記憶作為去重參照

#### Phase 2: LLM Extraction（核心）
```python
system_prompt = ADDITIVE_EXTRACTION_PROMPT  # ~870 行的超長提示
user_prompt = generate_additive_extraction_prompt(
    existing_memories=existing_memories,
    new_messages=parsed_messages,
    last_k_messages=last_messages,
    custom_instructions=custom_instr,
)
response = self.llm.generate_response(
    messages=[...],
    response_format={"type": "json_object"},
)
```

**關鍵發現 — ADDITIVE_EXTRACTION_PROMPT 的設計特點**：

1. **僅 ADD 操作**: V3 版本放棄了 V2 的 CRUD（ADD/UPDATE/DELETE/NONE）語義，改為純 ADD 模式。所有新資訊都作為獨立記憶條目新增，不修改現有記憶。

2. **雙來源提取**: 同時從 user 和 assistant 訊息中提取，但有嚴格邊界：
   - User 訊息：個人事實、偏好、計劃
   - Assistant 訊息：推薦、方案、研究成果（*但不提取附和/重述*）

3. **時間錨定 (Temporal Grounding)**: 使用 `Observation Date`（對話發生日期）而非 `Current Date`（系統日期）解析相對時間參照（「昨天」→ 觀察日前一天）

4. **反抽象化 (Anti-Generalization)**: 嚴禁將具體細節泛化：
   - ❌ "User has a dog"
   - ✅ "User has a dog named Poppy and their morning walks together are the highlight of their day"

5. **附帶事實提取**: 要求提取問句中的附帶個人事實（incidental facts），例如「我花園種了櫻桃番茄，有什麼適合的伴生植物嗎？」→ 提取「使用者在花園種櫻桃番茄」

6. **Memory Linking**: 新記憶可透過 `linked_memory_ids` 欄位連結到已有記憶的 UUID，建立關聯圖

#### Phase 3: Batch Embedding
```python
mem_embeddings_list = self.embedding_model.embed_batch(mem_texts, "add")
```
- 批次嵌入所有提取的記憶文本
- 有逐一 fallback 機制

#### Phase 4-5: Hash Dedup
```python
mem_hash = hashlib.md5(text.encode()).hexdigest()
if mem_hash in existing_hashes or mem_hash in seen_hashes:
    continue  # 跳過重複
```
- MD5 Hash 去重（同時對比既有記憶與當前批次內）
- BM25 Lemmatization 預處理

#### Phase 6: Batch Persist
```python
self.vector_store.insert(vectors=all_vectors, ids=all_ids, payloads=all_payloads)
self.db.batch_add_history(history_records)  # SQLite 歷史記錄
```
- 批次寫入向量儲存 + SQLite 歷史
- 所有事件標記為 `"ADD"`

#### Phase 7: Entity Linking
```python
all_entities = extract_entities_batch(all_texts)
# 7a: Global dedup
# 7b: Batch embed entities
# 7c: Batch search for existing entities (similarity >= 0.95)
# 7d: Separate into inserts vs updates
# 7e: Batch insert new entities
```

**實體連結流程**：
1. 批次提取所有記憶中的命名實體
2. 全域去重（跨記憶條目的相同實體合併）
3. 搜尋 Entity Store 中的現有實體（門檻 ≥ 0.95 表示同一實體）
4. 已存在：更新 `linked_memory_ids` 清單
5. 新實體：批次插入 Entity Store

#### Phase 8: Save & Return
- 將原始訊息存入 SQLite 的 session 歷史
- 返回 `[{id, memory, event: "ADD"}]`

---

## 4. 三訊號混合檢索引擎

### 4.1 搜尋管線

`_search_vector_store()` 實作了一個 **語義 + 關鍵詞 + 實體** 三路融合的檢索系統：

```
Query
  ├── Semantic Search (向量相似度)     ──→ semantic_results
  ├── BM25 Keyword Search (詞彙匹配)   ──→ bm25_scores
  └── Entity Boost (實體命中加成)       ──→ entity_boosts
                                            ↓
                                    score_and_rank()
                                            ↓
                                    Ranked Results
```

### 4.2 搜尋參數

| 參數 | 預設值 | 說明 |
|---|---|---|
| `top_k` | 20 | 最大返回數 |
| `threshold` | 0.1 | 最低分數門檻 |
| `rerank` | False | 是否啟用 Reranker |
| `internal_limit` | max(top_k * 4, 60) | 內部過度取樣數量 |

### 4.3 實體加成 (Entity Boost)

```python
def _compute_entity_boosts(self, query_entities, filters):
    # 最多 8 個去重實體
    # 每個實體搜尋 Entity Store (top_k=500)
    # similarity >= 0.5 才啟用
    # Spread-attenuated boost: 連結太多記憶的實體會被衰減
    num_linked = max(len(linked_memory_ids), 1)
    memory_count_weight = 1.0 / (1.0 + 0.001 * ((num_linked - 1) ** 2))
    boost = similarity * ENTITY_BOOST_WEIGHT * memory_count_weight
```

**設計亮點**：
- **擴散衰減 (Spread Attenuation)**: 一個實體連結到越多記憶，每條記憶收到的加成越少。這防止高頻實體（如使用者名字）對所有記憶都給予等量加成。
- `ENTITY_BOOST_WEIGHT` 控制實體訊號的全域權重

### 4.4 進階篩選器

支援豐富的 metadata 過濾運算子：
- 精確匹配: `{"key": "value"}`
- 比較: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`
- 集合: `in`, `nin`
- 文字: `contains`, `icontains`
- 萬用: `{"key": "*"}`
- 邏輯: `AND`, `OR`, `NOT`

---

## 5. Prompt 工程深度剖析

### 5.1 提取提示分類

Mem0 有 **4 套不同的提取提示**，適用於不同場景：

| 提示名稱 | 角色 | V2/V3 | 輸出格式 |
|---|---|---|---|
| `FACT_RETRIEVAL_PROMPT` | 通用事實提取 | V2（Legacy） | `{"facts": [...]}` |
| `USER_MEMORY_EXTRACTION_PROMPT` | User 訊息專用 | V2 | `{"facts": [...]}` |
| `AGENT_MEMORY_EXTRACTION_PROMPT` | Agent 訊息專用 | V2 | `{"facts": [...]}` |
| `ADDITIVE_EXTRACTION_PROMPT` | 統一 ADD-only | V3（主力） | `{"memory": [{id, text, attributed_to, linked_memory_ids}]}` |

### 5.2 V2 → V3 的演進

V2 使用 `DEFAULT_UPDATE_MEMORY_PROMPT` 實作 CRUD 語義：
- LLM 需要決定 ADD / UPDATE / DELETE / NONE
- 返回帶有 `event` 和 `old_memory` 的完整記憶陣列

V3 簡化為純 ADD：
- LLM 只需提取新事實
- 去重交給 Hash + 向量搜尋
- 大幅降低 LLM 決策負擔（減少幻覺風險）

### 5.3 提取品質控管機制

`ADDITIVE_EXTRACTION_PROMPT` 內建了多層品質閘門：

1. **Exhaustive Extraction Checklist（完整性自檢）**:
   - 每個不同主題/話題轉換是否都有提取？
   - 對話中間和結尾的訊息是否都檢查了？
   - 10+ 條訊息的對話應提取 5-15 條記憶
   - 每條使用者訊息中的每個事實是否都有對應提取？

2. **No Echo Extraction（反回聲）**: 禁止從 assistant 的重述中重複提取

3. **No Within-Response Duplication（批次內去重）**: 同一回應中語義等價的記憶只保留資訊量更大的

4. **No Detail Contamination（反污染）**: 禁止將 Existing Memories 的細節混入新提取

### 5.4 多語言支援

`use_input_language=True` 時：
- 自動偵測輸入語言並以相同語言記錄
- 保留原始文字/字母系統
- CJK 語言需維持原始敬語程度
- 日語需明確補全省略主語

---

## 6. 儲存架構

### 6.1 雙儲存設計

```
┌──────────────────┐     ┌─────────────────┐
│  Vector Store    │     │  SQLite          │
│  (Qdrant 等)     │     │  (SQLiteManager) │
├──────────────────┤     ├─────────────────┤
│ ● 記憶向量+payload│     │ ● 歷史記錄       │
│ ● 實體向量+連結   │     │ ● 訊息儲存       │
│ ● 搜尋/排序       │     │ ● 事件日誌       │
└──────────────────┘     └─────────────────┘
```

### 6.2 Payload 結構

每條記憶在向量儲存中的 payload：
```json
{
  "data": "記憶文本",
  "hash": "MD5 hash",
  "text_lemmatized": "BM25 用的詞形還原文本",
  "created_at": "ISO 8601",
  "updated_at": "ISO 8601",
  "attributed_to": "user | assistant",
  "user_id": "...",
  "agent_id": "...",
  "run_id": "..."
}
```

### 6.3 History Event 結構

```json
{
  "memory_id": "UUID",
  "old_memory": null,
  "new_memory": "記憶文本",
  "event": "ADD | UPDATE | DELETE",
  "created_at": "ISO 8601",
  "is_deleted": 0
}
```

---

## 7. N7 四維評估

### 7.1 評分矩陣

| 維度 | 分數 | 分析 |
|---|---|---|
| **品質 (Quality)** | 4.5/5 | V3 Pipeline 的 Phase 設計嚴謹，fallback 機制完善（batch → single）。Hash 去重 + 反幻覺 UUID 映射顯示高度防禦性設計。扣分點：MD5 用於 hash 去重，在理論上存在碰撞風險（雖然實務影響極低）。 |
| **原創性 (Originality)** | 4.0/5 | 三訊號混合檢索（Semantic + BM25 + Entity Boost）的融合設計具創新性。Spread Attenuation 衰減機制是精巧的工程決策。但「ADD-only」的設計簡化了問題空間，可能在需要記憶演進（如偏好改變）的場景中表現不佳。 |
| **工藝 (Craftsmanship)** | 3.5/5 | `ADDITIVE_EXTRACTION_PROMPT` 長達 ~870 行，文件化極為詳盡但有 Token 浪費風險。程式碼組織清晰，但 `main.py` 單檔超過 3000 行，存在 God Object 反模式。Entity linking 邏輯嵌入 add 方法而非獨立模組。 |
| **功能性 (Functionality)** | 4.5/5 | 完整的 CRUD + Search + History + Entity Linking。Procedural Memory 支援 Agent 工作日誌。多語言提取。進階 metadata 過濾。唯一缺憾是缺少原生的「記憶衰減/遺忘」機制。 |

**四維平均**: 4.125 / 5

### 7.2 必要缺陷指摘（反討好校準）

1. **Token 效率問題**: `ADDITIVE_EXTRACTION_PROMPT` 佔用大量 input token（~870 行提示文本），每次 `add()` 呼叫都會消耗。在高頻場景下，這構成顯著的成本與延遲負擔。

2. **記憶膨脹風險**: ADD-only 策略意味著記憶資料庫只增不減。缺少原生的 TTL、衰減或容量管理機制，長期運行可能導致檢索效率下降和 Token 預算超支。

3. **Entity Extraction 的黑盒風險**: `extract_entities_batch()` 的實作細節未在核心程式碼中公開，依賴外部模組。實體品質直接影響 Entity Boost 的可靠性。

4. **單執行緒瓶頸**: `_add_to_vector_store()` 是同步管線，雖有 async 版本但 entity linking 階段仍為同步批次處理，在大量記憶場景下可能成為瓶頸。

---

## 8. 對 N6 設計的關鍵啟示

### 8.1 可採用的設計模式

| 模式 | Mem0 實作 | N6 適用場景 |
|---|---|---|
| **Phased Batch Pipeline** | 8 階段分離 | N6 的記憶寫入管線可參考此分階設計 |
| **Anti-Hallucination UUID Mapping** | UUID → int 映射 | 任何需要 LLM 參照現有 ID 的場景 |
| **Hash Dedup** | MD5 去重 | N6 的記憶去重層 |
| **Entity Linking** | 獨立 Entity Store | N6 跨 Agent 記憶關聯 |
| **Spread Attenuation** | 實體加成衰減 | N6 檢索排序 |
| **Temporal Grounding** | Observation Date 錨定 | N6 時間參照解析 |

### 8.2 需調整的設計

| Mem0 設計 | 問題 | N6 改良方向 |
|---|---|---|
| 870 行提取提示 | Token 浪費 | 分層式提取（輕量初篩 + 深度提取） |
| ADD-only（V3） | 無法處理偏好演進 | 保留 UPDATE/MERGE 語義但限制 DELETE |
| 向量資料庫中心 | 可觀測性低 | 雙寫策略：Markdown + Vector Store |
| 嵌入式 SDK | 與 Agent 耦合 | Daemon 模式（借鑑 claude-mem） |
| 無記憶衰減 | 資料庫膨脹 | 引入 TTL + 重要度加權衰減 |
| main.py 3000+ 行 | God Object | 按職責拆分模組 |

### 8.3 與 claude-mem 的互補分析

| 面向 | claude-mem 優勢 | Mem0 優勢 | N6 綜合策略 |
|---|---|---|---|
| **擷取觸發** | 自動 Hook（零設定） | 精確 API 呼叫 | Hook + 手動雙模式 |
| **儲存格式** | Markdown（人類可讀） | 向量（機器優化） | 雙寫（Markdown + SQLite FTS） |
| **檢索層** | 3-Layer 漸進揭露 | 三訊號融合搜尋 | 3-Layer 結構 + 語義排序 |
| **實體關聯** | 無 | Entity Store | 輕量級實體索引 |
| **Token 效率** | 高（漸進揭露） | 低（長提示） | 漸進揭露為主 |
| **可觀測性** | 高（Git 追蹤） | 低（向量黑盒） | Markdown + 審計日誌 |

---

## 9. 技術債與風險標註

| 風險 | 嚴重度 | 說明 |
|---|---|---|
| 提示注入 (Prompt Injection) | 🔴 HIGH | 使用者訊息直接注入 LLM 提取提示，可能被惡意訊息操控提取結果 |
| 記憶膨脹 (Memory Bloat) | 🟡 MEDIUM | ADD-only 無容量管理，長期累積可能影響檢索品質 |
| 嵌入模型漂移 | 🟡 MEDIUM | 更換嵌入模型後，舊向量與新向量不相容 |
| LLM 提取一致性 | 🟡 MEDIUM | 不同 LLM 對同一對話可能提取不同數量/品質的記憶 |
| Entity Store 孤兒 | 🟢 LOW | 記憶刪除後，Entity Store 中的 linked_memory_ids 可能指向已刪除的記憶 |

---

## 10. 結論與建議

Mem0 提供了一個**工業級的記憶管理參考實作**，其 V3 Phased Batch Pipeline 和三訊號混合檢索引擎展現了成熟的工程設計。然而，其「嵌入式 SDK」定位和「ADD-only」策略與我們 N6 的「Daemon Agent」定位存在根本差異。

**建議 N6 設計採取的混合策略**：

1. **擷取**: claude-mem 的 Daemon Hook 模式（自動擷取）+ Mem0 的精細提取提示（但縮短至 ≤200 行）
2. **儲存**: 雙寫策略（Markdown for 人類 + SQLite FTS for 機器）——不引入額外向量資料庫依賴
3. **檢索**: claude-mem 的 3-Layer 漸進揭露 + Mem0 的 BM25 融合排序
4. **實體**: 輕量級 Entity Index（基於 SQLite FTS），不引入獨立 Entity Store
5. **衰減**: 新增 TTL + 重要度加權的衰減機制（Mem0 缺少此功能）

> **信心程度**: 高（基於直接原始碼分析與官方文件交叉驗證）

---

*本報告基於 Mem0 開源版原始碼（`main` branch, 2026-05）進行乾淨室分析。*  
*分析過程嚴格遵循 N7 Evaluator Protocol，不受 N1 既有設計文件影響。*
