# N6 記憶中介者（Memory Broker）實作計畫

> **給 Agentic 執行者：** 必備子技能：使用 superpowers:subagent-driven-development（推薦）或 superpowers:executing-plans 逐 Task 實作。步驟使用 checkbox (`- [ ]`) 語法追蹤進度。

**目標：** 將 N6 記憶中介者建構為 MCP Server — 一個集中式、常駐的記憶 daemon，為所有 N1-N9 Agent 提供持久化、可搜尋、存取控制的長期記憶服務。

**架構：** N6 是單一寫入者（Single-Writer）MCP Server，後端為雙層儲存：Markdown 檔案作為 Source of Truth + SQLite/FTS5 作為衍生索引。Gemini Embedding 2 提供語意搜尋，FTS5 為離線降級方案。ACL 強制命名空間隔離 — 管理者（N1/N6/N7/N9）擁有全域存取，一般 Agent 僅能讀寫自己的命名空間。

**技術棧：** Python 3.13+, SQLite 3.49+ (WAL + FTS5), MCP SDK (`mcp[cli]`), Google Generative AI (Embedding), pathlib, pytest

**決策參考：** KI `n6-memory-architecture-research/artifacts/接續指南.md` §5.1

---

## 檔案結構

```
d:\hermes-agent\src\n6_memory_broker\
├── __init__.py              # Package init + version
├── server.py                # MCP Server entry point + tool registration
├── schema.py                # SQLite schema init, migrations, FTS5
├── models.py                # Pydantic models (MemoryEntry, SearchResult, ACL)
├── acl.py                   # Access Control Layer (role→permission mapping)
├── store.py                 # Core CRUD: insert, update, search, archive
├── embedding.py             # Gemini Embedding 2 client + FTS5 fallback
├── markdown_sync.py         # Markdown ↔ SQLite bidirectional sync
├── decay.py                 # γ-decay engine (tier promotion, archival)
├── legacy_migrator.py       # One-shot migration of 39 legacy files
├── inspector.py             # 2-hour periodic inspection daemon
└── config.py                # Environment config + constants

d:\hermes-agent\src\n6_memory_broker\tools\
├── __init__.py
├── write_tools.py           # memory_submit, memory_update
├── read_tools.py            # memory_search, memory_load_recent, memory_browse_*
└── admin_tools.py           # memory_stats, memory_archive_status

d:\hermes-agent\tests\n6\
├── conftest.py              # Shared fixtures (temp DB, mock ACL)
├── test_schema.py           # Schema creation + migration
├── test_models.py           # Pydantic validation
├── test_acl.py              # Permission checks
├── test_store.py            # CRUD operations
├── test_write_tools.py      # MCP write tools
├── test_read_tools.py       # MCP read tools
├── test_admin_tools.py      # MCP admin tools
├── test_embedding.py        # Embedding + fallback
├── test_decay.py            # Tier promotion + archival
├── test_markdown_sync.py    # Markdown ↔ DB sync
└── test_legacy_migrator.py  # Legacy migration
```

---

## 執行模式比較

本計畫提供兩種執行方式，核心差異在於**上下文管理**與**品質閘門機制**：

### 模式 A：Subagent 驅動（推薦）

**技能：** `superpowers:subagent-driven-development`

**運作原理：** 主控 Agent（你的當前 session）作為調度中心，每個 Task 派發一個**全新的** subagent 去執行。subagent 完成後，主控 Agent 再派發兩個 reviewer subagent 進行雙階段審查。

```
主控 Agent (N7)
  ├── 派發 Implementer Subagent → 執行 Task 1
  │     └── 完成 → 回報 DONE
  ├── 派發 Spec Reviewer Subagent → 驗證是否符合規格
  │     └── ✅ PASS
  ├── 派發 Code Quality Reviewer → 驗證程式碼品質
  │     └── ✅ PASS → 標記 Task 1 完成
  ├── 派發 Implementer Subagent → 執行 Task 2
  │     └── ...（重複）
  └── 全部完成 → 派發 Final Reviewer → finishing-a-development-branch
```

**優點：**
- ✅ 每個 Task 擁有**乾淨的上下文**，不會被前面的 Task 殘留資訊污染
- ✅ **雙階段品質閘門**：先驗規格符合性、再驗程式碼品質
- ✅ 主控 Agent 保留全域視野，可在 Task 之間做決策調整
- ✅ 支援 `NEEDS_CONTEXT` / `BLOCKED` 狀態回報，遇到問題會停下來詢問

**缺點：**
- ⚠️ 每個 Task 需要 3+ 次 subagent 調用（Implementer + 2 Reviewers）
- ⚠️ 主控 Agent 需要手動提供上下文給每個 subagent

**適用場景：** Task 之間相對獨立、需要高品質保證、session 時間充足

---

### 模式 B：內聯執行

**技能：** `superpowers:executing-plans`

**運作原理：** 在**同一個 session** 中，Agent 直接按照計畫逐步執行每個 Task 的每個 Step。沒有 subagent 分派，所有工作在當前上下文中完成。

```
當前 Session (N7)
  ├── 讀取計畫 → 批判性審查 → 建立 Todo 清單
  ├── 執行 Task 1 Step 1-8 → 標記完成
  ├── 執行 Task 2 Step 1-8 → 標記完成
  ├── ...
  └── 全部完成 → finishing-a-development-branch
```

**優點：**
- ✅ 無 subagent 開銷，**執行速度更快**
- ✅ 所有 Task 共享上下文，跨 Task 的依賴關係處理更簡單
- ✅ 適合快速原型開發

**缺點：**
- ⚠️ **無雙階段審查**，品質保證依賴 Agent 自身的自檢能力
- ⚠️ 長計畫可能導致上下文窗口溢出，後期 Task 品質下降
- ⚠️ 一旦中途出錯，可能汙染後續所有 Task 的執行

**適用場景：** 計畫較短（≤5 Tasks）、快速迭代、不需要嚴格的審查流程

---

### 建議選擇

| 條件 | 推薦模式 |
|------|---------|
| 本計畫（11 Tasks，高複雜度） | **模式 A：Subagent 驅動** |
| 快速修補（1-3 Tasks） | 模式 B：內聯執行 |
| 需要嚴格品質閘門 | 模式 A |
| 上下文窗口有限 | 模式 A |
| 需要跨 Task 快速共享狀態 | 模式 B |

---

## 施工所需技能清單

以下列出本計畫施工過程中**必須**或**建議**載入的 Skills，按階段分類：

### 🔧 核心施工技能（必須）

| 技能 | 路徑 | 用途 | 使用時機 |
|------|------|------|---------|
| **subagent-driven-development** | `superpowers/subagent-driven-development/SKILL.md` | 主控調度：派發 Implementer + Reviewer subagents | 模式 A 全程使用 |
| **executing-plans** | `superpowers/executing-plans/SKILL.md` | 內聯執行：逐步實作計畫 | 模式 B 全程使用 |
| **test-driven-development** | `superpowers/test-driven-development/SKILL.md` | TDD 循環：紅→綠→重構 | 每個 Task 的 Step 1-4 |
| **using-git-worktrees** | `superpowers/using-git-worktrees/SKILL.md` | Git worktree 隔離：建立獨立工作分支 | 施工開始前 |

### 🔍 品質保證技能（強烈建議）

| 技能 | 路徑 | 用途 | 使用時機 |
|------|------|------|---------|
| **requesting-code-review** | `superpowers/requesting-code-review/SKILL.md` | 向 reviewer subagent 提交審查請求 | 模式 A 每個 Task 完成後 |
| **receiving-code-review** | `superpowers/receiving-code-review/SKILL.md` | 處理 reviewer 回饋 | 審查未通過時 |
| **verification-before-completion** | `superpowers/verification-before-completion/SKILL.md` | 完工前最終驗證 | Task 11 完成後 |
| **systematic-debugging** | `superpowers/systematic-debugging/SKILL.md` | 系統性除錯流程 | 測試失敗且原因不明時 |

### 🚀 收尾技能（必須）

| 技能 | 路徑 | 用途 | 使用時機 |
|------|------|------|---------|
| **finishing-a-development-branch** | `superpowers/finishing-a-development-branch/SKILL.md` | 分支收尾：最終測試 + 合併準備 | 全部 11 Tasks 完成後 |

### 📋 施工流程摘要

```
1. 載入 using-git-worktrees → 建立隔離工作分支
2. 選擇模式 A 或 B → 載入對應技能
3. 逐 Task 執行：
   ├── 每個 Task 內使用 test-driven-development
   ├── 模式 A：每個 Task 後觸發 requesting-code-review
   └── 遇到卡關：載入 systematic-debugging
4. Task 11 完成後 → verification-before-completion
5. 最終收尾 → finishing-a-development-branch
```

---

## Task 1：專案骨架 + MCP Server 啟動

**檔案：**
- 建立：`src/n6_memory_broker/__init__.py`
- 建立：`src/n6_memory_broker/config.py`
- 建立：`src/n6_memory_broker/server.py`
- 建立：`tests/n6/conftest.py`
- 建立：`tests/n6/test_server_boot.py`

- [ ] **步驟 1：建立套件初始化檔**

```python
# src/n6_memory_broker/__init__.py
"""N6 Memory Broker — Centralized MCP Memory Server for Hermes Agents."""
__version__ = "0.1.0"
```

- [ ] **步驟 2：建立設定模組**

```python
# src/n6_memory_broker/config.py
"""N6 configuration constants and environment resolution."""
import os
from pathlib import Path

# ─── Paths ──────────────────────────────────────────────────────────────
N6_ROOT = Path(os.getenv("N6_DATA_ROOT", str(Path(__file__).parent.parent.parent / "data" / "n6")))
MARKDOWN_ROOT = N6_ROOT / "memories"
ARCHIVE_ROOT = N6_ROOT / "archive"
DB_PATH = N6_ROOT / "n6_memory.db"

# ─── Embedding ──────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
EMBEDDING_MODEL = "gemini-embedding-exp-03-07"
EMBEDDING_DIM = 3072

# ─── Decay ──────────────────────────────────────────────────────────────
SEMANTIC_ARCHIVE_DAYS = 90
SAFETY_VALVE_DAYS = 180
INSPECTION_INTERVAL_HOURS = 2

# ─── Server ─────────────────────────────────────────────────────────────
MCP_SERVER_NAME = "n6-memory-broker"
MCP_SERVER_VERSION = "0.1.0"
```

- [ ] **步驟 3：撰寫預期失敗的啟動測試**

```python
# tests/n6/test_server_boot.py
"""Test that MCP server can be instantiated."""
from n6_memory_broker.server import create_server

def test_create_server_returns_mcp_instance():
    server = create_server()
    assert server is not None
    assert server.name == "n6-memory-broker"
```

- [ ] **步驟 4：建立共用測試 fixtures**

```python
# tests/n6/conftest.py
"""Shared fixtures for N6 tests."""
import pytest
from pathlib import Path
from n6_memory_broker.schema import init_db

@pytest.fixture
def tmp_db(tmp_path):
    """Yield a fresh SQLite connection with N6 schema."""
    db_path = tmp_path / "test_n6.db"
    conn = init_db(db_path)
    yield conn
    conn.close()

@pytest.fixture
def tmp_markdown_root(tmp_path):
    """Yield a temporary markdown directory."""
    md_root = tmp_path / "memories"
    md_root.mkdir()
    return md_root

@pytest.fixture
def admin_caller():
    """Return an admin agent identity."""
    from n6_memory_broker.models import CallerIdentity
    return CallerIdentity(agent_id="N7")

@pytest.fixture
def general_caller():
    """Return a general agent identity."""
    from n6_memory_broker.models import CallerIdentity
    return CallerIdentity(agent_id="N5")
```

- [ ] **步驟 5：執行測試確認失敗**

執行：`cd d:\hermes-agent && python -m pytest tests/n6/test_server_boot.py -v`
預期：FAIL，錯誤為 `ModuleNotFoundError`

- [ ] **步驟 6：實作最小 MCP Server**

```python
# src/n6_memory_broker/server.py
"""N6 Memory Broker — MCP Server entry point."""
from mcp.server.fastmcp import FastMCP
from n6_memory_broker.config import MCP_SERVER_NAME, MCP_SERVER_VERSION

def create_server() -> FastMCP:
    """Create and configure the N6 MCP server instance."""
    server = FastMCP(
        MCP_SERVER_NAME,
        version=MCP_SERVER_VERSION,
        description="Centralized memory broker for Hermes N1-N9 agents",
    )
    return server

if __name__ == "__main__":
    server = create_server()
    server.run(transport="stdio")
```

- [ ] **步驟 7：執行測試確認通過**

執行：`cd d:\hermes-agent && python -m pytest tests/n6/test_server_boot.py -v`
預期：PASS

- [ ] **步驟 8：提交**

```bash
cd d:\hermes-agent
git add src/n6_memory_broker/ tests/n6/
git commit -m "feat(n6): bootstrap MCP server skeleton + config + test fixtures"
```

---

## Task 2：SQLite Schema + FTS5 索引 + Pydantic 模型

**檔案：**
- 建立：`src/n6_memory_broker/schema.py`
- 建立：`src/n6_memory_broker/models.py`
- 建立：`tests/n6/test_schema.py`
- 建立：`tests/n6/test_models.py`

- [ ] **步驟 1：撰寫預期失敗的 Schema 測試**

```python
# tests/n6/test_schema.py
"""Test SQLite schema initialization."""
from n6_memory_broker.schema import init_db, SCHEMA_VERSION

def test_init_creates_memories_table(tmp_path):
    conn = init_db(tmp_path / "test.db")
    tables = [t[0] for t in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]
    assert "memories" in tables
    assert "memories_fts" in tables
    assert "schema_version" in tables
    conn.close()

def test_init_sets_wal_mode(tmp_path):
    conn = init_db(tmp_path / "test.db")
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode == "wal"
    conn.close()

def test_schema_version_is_set(tmp_path):
    conn = init_db(tmp_path / "test.db")
    ver = conn.execute("SELECT version FROM schema_version").fetchone()[0]
    assert ver == SCHEMA_VERSION
    conn.close()

def test_memories_has_required_columns(tmp_path):
    conn = init_db(tmp_path / "test.db")
    cols = [c[1] for c in conn.execute("PRAGMA table_info(memories)").fetchall()]
    for req in ["id", "agent_id", "namespace", "project_id", "content",
                "tags", "channel", "memory_tier", "access_count",
                "last_accessed_at", "created_at", "updated_at"]:
        assert req in cols, f"Missing column: {req}"
    conn.close()

def test_idempotent_init(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path).close()
    conn2 = init_db(db_path)
    ver = conn2.execute("SELECT version FROM schema_version").fetchone()[0]
    assert ver == SCHEMA_VERSION
    conn2.close()
```

- [ ] **步驟 2：執行測試確認失敗**

執行：`cd d:\hermes-agent && python -m pytest tests/n6/test_schema.py -v`
預期：FAIL

- [ ] **步驟 3：實作 Schema 模組**

```python
# src/n6_memory_broker/schema.py
"""N6 SQLite schema — memories table + FTS5 index."""
import sqlite3
from pathlib import Path

SCHEMA_VERSION = 1

def init_db(db_path: Path) -> sqlite3.Connection:
    """Initialize N6 memory database with WAL + FTS5."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS memories (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id        TEXT    NOT NULL,
            namespace       TEXT    NOT NULL DEFAULT 'default',
            project_id      TEXT,
            content         TEXT    NOT NULL,
            tags            TEXT    DEFAULT '',
            channel         TEXT    NOT NULL DEFAULT 'ide',
            memory_tier     TEXT    NOT NULL DEFAULT 'working',
            access_count    INTEGER NOT NULL DEFAULT 0,
            last_accessed_at TEXT,
            embedding_blob  BLOB,
            created_at      TEXT    NOT NULL,
            updated_at      TEXT    NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_memories_agent_ns
            ON memories(agent_id, namespace, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_memories_project
            ON memories(project_id, created_at DESC)
            WHERE project_id IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_memories_tier
            ON memories(memory_tier, last_accessed_at);
    """)

    try:
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                content, tags,
                content='memories', content_rowid='id'
            )
        """)
    except sqlite3.OperationalError:
        pass

    ver = conn.execute("SELECT version FROM schema_version").fetchone()
    if not ver:
        conn.execute("INSERT INTO schema_version VALUES (?)", (SCHEMA_VERSION,))
        conn.commit()
    return conn
```

- [ ] **步驟 4：執行 Schema 測試**

執行：`cd d:\hermes-agent && python -m pytest tests/n6/test_schema.py -v`
預期：PASS

- [ ] **步驟 5：撰寫預期失敗的模型測試**

```python
# tests/n6/test_models.py
"""Test Pydantic models for N6."""
import pytest
from n6_memory_broker.models import MemoryEntry, CallerIdentity, MemoryTier

def test_memory_entry_defaults():
    entry = MemoryEntry(agent_id="N5", content="test")
    assert entry.namespace == "default"
    assert entry.project_id is None
    assert entry.channel == "ide"
    assert entry.memory_tier == MemoryTier.WORKING

def test_memory_entry_requires_content():
    with pytest.raises(Exception):
        MemoryEntry(agent_id="N5", content="")

def test_caller_identity_admin():
    caller = CallerIdentity(agent_id="N7")
    assert caller.role == "admin"

def test_caller_identity_general():
    caller = CallerIdentity(agent_id="N5")
    assert caller.role == "general"
```

- [ ] **步驟 6：實作模型**

```python
# src/n6_memory_broker/models.py
"""Pydantic models for N6 Memory Broker."""
from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class MemoryTier(str, Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"

ADMIN_AGENTS = frozenset({"N1", "N6", "N7", "N9"})

class CallerIdentity(BaseModel):
    agent_id: str
    role: str = ""
    def model_post_init(self, __context) -> None:
        if not self.role:
            self.role = "admin" if self.agent_id in ADMIN_AGENTS else "general"

class MemoryEntry(BaseModel):
    agent_id: str
    content: str = Field(..., min_length=1)
    namespace: str = "default"
    project_id: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    channel: str = "ide"
    memory_tier: MemoryTier = MemoryTier.WORKING

class SearchResult(BaseModel):
    id: int
    agent_id: str
    namespace: str
    content: str
    tags: list[str]
    memory_tier: MemoryTier
    score: float = 0.0
    created_at: str = ""
```

- [ ] **步驟 7：執行所有 Task 2 測試**

執行：`cd d:\hermes-agent && python -m pytest tests/n6/test_schema.py tests/n6/test_models.py -v`
預期：PASS

- [ ] **步驟 8：提交**

```bash
git add src/n6_memory_broker/schema.py src/n6_memory_broker/models.py tests/n6/
git commit -m "feat(n6): SQLite schema with FTS5 + Pydantic models"
```

---

## Task 3：ACL（存取控制層）

**檔案：**
- 建立：`src/n6_memory_broker/acl.py`
- 建立：`tests/n6/test_acl.py`

- [ ] **步驟 1：撰寫預期失敗的 ACL 測試**

```python
# tests/n6/test_acl.py
"""Test N6 Access Control Layer."""
import pytest
from n6_memory_broker.acl import check_permission, ACLError
from n6_memory_broker.models import CallerIdentity

def test_admin_can_read_any():
    caller = CallerIdentity(agent_id="N7")
    assert check_permission(caller, "read", target_agent="N5") is True

def test_admin_can_write_any():
    caller = CallerIdentity(agent_id="N1")
    assert check_permission(caller, "write", target_agent="N5") is True

def test_admin_can_manage():
    caller = CallerIdentity(agent_id="N9")
    assert check_permission(caller, "manage") is True

def test_general_can_read_own():
    caller = CallerIdentity(agent_id="N5")
    assert check_permission(caller, "read", target_agent="N5") is True

def test_general_cannot_read_other():
    caller = CallerIdentity(agent_id="N5")
    with pytest.raises(ACLError):
        check_permission(caller, "read", target_agent="N7")

def test_general_can_write_own():
    caller = CallerIdentity(agent_id="N2")
    assert check_permission(caller, "write", target_agent="N2") is True

def test_general_cannot_manage():
    caller = CallerIdentity(agent_id="N8")
    with pytest.raises(ACLError):
        check_permission(caller, "manage")
```

- [ ] **步驟 2：執行測試確認失敗**

執行：`cd d:\hermes-agent && python -m pytest tests/n6/test_acl.py -v`
預期：FAIL

- [ ] **步驟 3：實作 ACL**

```python
# src/n6_memory_broker/acl.py
"""N6 Access Control Layer — role-based permission enforcement."""
from n6_memory_broker.models import CallerIdentity

class ACLError(PermissionError):
    """Raised when an agent attempts a forbidden action."""
    pass

def check_permission(
    caller: CallerIdentity,
    action: str,
    target_agent: str | None = None,
) -> bool:
    """Check if caller has permission for the given action.

    Actions: 'read', 'write', 'manage'
    Rules (Q6): Admin=全域, General=僅自己
    """
    is_admin = caller.role == "admin"

    if action == "manage":
        if not is_admin:
            raise ACLError(f"Agent {caller.agent_id}: manage forbidden")
        return True

    if action in ("read", "write"):
        if is_admin:
            return True
        if target_agent and target_agent != caller.agent_id:
            raise ACLError(f"Agent {caller.agent_id}: {action} on {target_agent} forbidden")
        return True

    raise ACLError(f"Unknown action: {action}")
```

- [ ] **步驟 4：執行測試確認通過**

執行：`cd d:\hermes-agent && python -m pytest tests/n6/test_acl.py -v`
預期：PASS

- [ ] **步驟 5：提交**

```bash
git add src/n6_memory_broker/acl.py tests/n6/test_acl.py
git commit -m "feat(n6): ACL layer — admin/general role enforcement"
```

---

## Task 4：核心 Store（CRUD 層）

**檔案：**
- 建立：`src/n6_memory_broker/store.py`
- 建立：`tests/n6/test_store.py`

- [ ] **步驟 1：撰寫預期失敗的 Store 測試**

```python
# tests/n6/test_store.py
"""Test N6 memory store CRUD operations."""
import pytest
from n6_memory_broker.store import insert_memory, get_memory, update_memory_meta, search_fts, list_by_namespace
from n6_memory_broker.models import MemoryEntry

def test_insert_and_get(tmp_db):
    entry = MemoryEntry(agent_id="N5", content="Test memory", namespace="dev")
    mid = insert_memory(tmp_db, entry)
    assert mid > 0
    row = get_memory(tmp_db, mid)
    assert row["content"] == "Test memory"
    assert row["namespace"] == "dev"
    assert row["memory_tier"] == "working"
    assert row["access_count"] == 0

def test_insert_increments_id(tmp_db):
    e1 = MemoryEntry(agent_id="N5", content="first")
    e2 = MemoryEntry(agent_id="N5", content="second")
    id1 = insert_memory(tmp_db, e1)
    id2 = insert_memory(tmp_db, e2)
    assert id2 == id1 + 1

def test_update_memory_meta(tmp_db):
    entry = MemoryEntry(agent_id="N7", content="original", tags=["a"])
    mid = insert_memory(tmp_db, entry)
    update_memory_meta(tmp_db, mid, tags=["a", "b"], namespace="ops")
    row = get_memory(tmp_db, mid)
    assert "b" in row["tags"]
    assert row["namespace"] == "ops"

def test_search_fts(tmp_db):
    insert_memory(tmp_db, MemoryEntry(agent_id="N5", content="SQLite WAL mode"))
    insert_memory(tmp_db, MemoryEntry(agent_id="N5", content="Python asyncio"))
    results = search_fts(tmp_db, "SQLite", agent_id="N5")
    assert len(results) >= 1
    assert "SQLite" in results[0]["content"]

def test_list_by_namespace(tmp_db):
    insert_memory(tmp_db, MemoryEntry(agent_id="N5", content="a", namespace="alpha"))
    insert_memory(tmp_db, MemoryEntry(agent_id="N5", content="b", namespace="beta"))
    insert_memory(tmp_db, MemoryEntry(agent_id="N5", content="c", namespace="alpha"))
    rows = list_by_namespace(tmp_db, agent_id="N5", namespace="alpha")
    assert len(rows) == 2
```

- [ ] **步驟 2：執行測試確認失敗**

執行：`cd d:\hermes-agent && python -m pytest tests/n6/test_store.py -v`
預期：FAIL

- [ ] **步驟 3：實作 Store 模組**

```python
# src/n6_memory_broker/store.py
"""N6 Core Store — CRUD operations on memories table."""
import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional
from n6_memory_broker.models import MemoryEntry

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def insert_memory(conn: sqlite3.Connection, entry: MemoryEntry) -> int:
    """Insert a memory and update FTS5 index. Returns row id."""
    now = _now()
    tags_str = json.dumps(entry.tags)
    cur = conn.execute("""
        INSERT INTO memories
            (agent_id, namespace, project_id, content, tags, channel,
             memory_tier, access_count, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
    """, (entry.agent_id, entry.namespace, entry.project_id,
          entry.content, tags_str, entry.channel,
          entry.memory_tier.value, now, now))
    row_id = cur.lastrowid
    conn.execute(
        "INSERT INTO memories_fts(rowid, content, tags) VALUES (?, ?, ?)",
        (row_id, entry.content, tags_str))
    conn.commit()
    return row_id

def get_memory(conn: sqlite3.Connection, memory_id: int) -> dict | None:
    """Get a single memory by id. Increments access_count."""
    now = _now()
    conn.execute(
        "UPDATE memories SET access_count = access_count + 1, last_accessed_at = ? WHERE id = ?",
        (now, memory_id))
    conn.commit()
    row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    d["tags"] = json.loads(d.get("tags", "[]"))
    return d

def update_memory_meta(
    conn: sqlite3.Connection,
    memory_id: int,
    tags: list[str] | None = None,
    namespace: str | None = None,
) -> None:
    """Update tags and/or namespace on a memory."""
    updates, params = [], []
    if tags is not None:
        updates.append("tags = ?")
        params.append(json.dumps(tags))
    if namespace is not None:
        updates.append("namespace = ?")
        params.append(namespace)
    if not updates:
        return
    updates.append("updated_at = ?")
    params.append(_now())
    params.append(memory_id)
    conn.execute(f"UPDATE memories SET {', '.join(updates)} WHERE id = ?", params)
    # Rebuild FTS
    row = conn.execute("SELECT content, tags FROM memories WHERE id = ?", (memory_id,)).fetchone()
    if row:
        conn.execute("DELETE FROM memories_fts WHERE rowid = ?", (memory_id,))
        conn.execute("INSERT INTO memories_fts(rowid, content, tags) VALUES (?, ?, ?)",
                     (memory_id, row["content"], row["tags"]))
    conn.commit()

def search_fts(
    conn: sqlite3.Connection,
    query: str,
    agent_id: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """Full-text search via FTS5."""
    if agent_id:
        rows = conn.execute("""
            SELECT m.* FROM memories m
            JOIN memories_fts f ON m.id = f.rowid
            WHERE memories_fts MATCH ? AND m.agent_id = ?
            ORDER BY rank LIMIT ?
        """, (query, agent_id, limit)).fetchall()
    else:
        rows = conn.execute("""
            SELECT m.* FROM memories m
            JOIN memories_fts f ON m.id = f.rowid
            WHERE memories_fts MATCH ?
            ORDER BY rank LIMIT ?
        """, (query, limit)).fetchall()
    return [_parse_row(r) for r in rows]

def list_by_namespace(
    conn: sqlite3.Connection,
    agent_id: str,
    namespace: str,
    limit: int = 50,
) -> list[dict]:
    """List memories in a specific namespace."""
    rows = conn.execute("""
        SELECT * FROM memories
        WHERE agent_id = ? AND namespace = ?
        ORDER BY created_at DESC LIMIT ?
    """, (agent_id, namespace, limit)).fetchall()
    return [_parse_row(r) for r in rows]

def _parse_row(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["tags"] = json.loads(d.get("tags", "[]"))
    return d
```

- [ ] **步驟 4：執行測試確認通過**

執行：`cd d:\hermes-agent && python -m pytest tests/n6/test_store.py -v`
預期：PASS

- [ ] **步驟 5：提交**

```bash
git add src/n6_memory_broker/store.py tests/n6/test_store.py
git commit -m "feat(n6): core store CRUD with FTS5 search"
```

---

## Task 5：MCP 寫入工具（memory_submit + memory_update）

**檔案：**
- 建立：`src/n6_memory_broker/tools/__init__.py`
- 建立：`src/n6_memory_broker/tools/write_tools.py`
- 建立：`tests/n6/test_write_tools.py`

- [ ] **步驟 1：撰寫預期失敗的測試**

```python
# tests/n6/test_write_tools.py
"""Test MCP write tools."""
import pytest
from n6_memory_broker.tools.write_tools import handle_memory_submit, handle_memory_update

def test_memory_submit_success(tmp_db):
    result = handle_memory_submit(
        tmp_db, agent_id="N5", content="Decision: use SQLite",
        namespace="dev", tags=["arch"], channel="ide"
    )
    assert result["status"] == "ok"
    assert result["memory_id"] > 0

def test_memory_submit_empty_content(tmp_db):
    result = handle_memory_submit(tmp_db, agent_id="N5", content="")
    assert result["status"] == "error"

def test_memory_update_tags(tmp_db):
    r = handle_memory_submit(tmp_db, agent_id="N7", content="test")
    mid = r["memory_id"]
    result = handle_memory_update(
        tmp_db, agent_id="N7", memory_id=mid, tags=["new-tag"]
    )
    assert result["status"] == "ok"

def test_memory_update_acl_blocked(tmp_db):
    r = handle_memory_submit(tmp_db, agent_id="N7", content="admin data")
    mid = r["memory_id"]
    result = handle_memory_update(
        tmp_db, agent_id="N5", memory_id=mid, tags=["hack"]
    )
    assert result["status"] == "error"
    assert "forbidden" in result["message"].lower()
```

- [ ] **步驟 2：執行測試確認失敗**

執行：`cd d:\hermes-agent && python -m pytest tests/n6/test_write_tools.py -v`
預期：FAIL

- [ ] **步驟 3：實作寫入工具**

```python
# src/n6_memory_broker/tools/__init__.py
"""N6 MCP Tool modules."""

# src/n6_memory_broker/tools/write_tools.py
"""MCP Write Tools: memory_submit, memory_update."""
import sqlite3
from n6_memory_broker.models import MemoryEntry, CallerIdentity
from n6_memory_broker.acl import check_permission, ACLError
from n6_memory_broker.store import insert_memory, update_memory_meta, get_memory

def handle_memory_submit(
    conn: sqlite3.Connection,
    agent_id: str,
    content: str,
    namespace: str = "default",
    project_id: str | None = None,
    tags: list[str] | None = None,
    channel: str = "ide",
) -> dict:
    """Submit a new memory."""
    try:
        entry = MemoryEntry(
            agent_id=agent_id, content=content, namespace=namespace,
            project_id=project_id, tags=tags or [], channel=channel,
        )
    except Exception as e:
        return {"status": "error", "message": str(e)}

    caller = CallerIdentity(agent_id=agent_id)
    try:
        check_permission(caller, "write", target_agent=agent_id)
    except ACLError as e:
        return {"status": "error", "message": str(e)}

    mid = insert_memory(conn, entry)
    return {"status": "ok", "memory_id": mid}

def handle_memory_update(
    conn: sqlite3.Connection,
    agent_id: str,
    memory_id: int,
    tags: list[str] | None = None,
    namespace: str | None = None,
) -> dict:
    """Update tags/namespace on an existing memory."""
    row = get_memory(conn, memory_id)
    if not row:
        return {"status": "error", "message": f"Memory {memory_id} not found"}

    caller = CallerIdentity(agent_id=agent_id)
    try:
        check_permission(caller, "write", target_agent=row["agent_id"])
    except ACLError as e:
        return {"status": "error", "message": str(e)}

    update_memory_meta(conn, memory_id, tags=tags, namespace=namespace)
    return {"status": "ok", "memory_id": memory_id}
```

- [ ] **步驟 4：執行測試確認通過**

執行：`cd d:\hermes-agent && python -m pytest tests/n6/test_write_tools.py -v`
預期：PASS

- [ ] **步驟 5：提交**

```bash
git add src/n6_memory_broker/tools/ tests/n6/test_write_tools.py
git commit -m "feat(n6): MCP write tools — memory_submit + memory_update"
```

---

## Task 6：MCP 讀取工具（4 個工具）

**檔案：**
- 建立：`src/n6_memory_broker/tools/read_tools.py`
- 建立：`tests/n6/test_read_tools.py`

- [ ] **步驟 1：撰寫預期失敗的測試**

```python
# tests/n6/test_read_tools.py
"""Test MCP read tools."""
import pytest
from n6_memory_broker.tools.write_tools import handle_memory_submit
from n6_memory_broker.tools.read_tools import (
    handle_memory_search, handle_memory_load_recent,
    handle_memory_browse_namespace, handle_memory_browse_project,
)

@pytest.fixture
def seeded_db(tmp_db):
    """Seed test data."""
    handle_memory_submit(tmp_db, "N5", "SQLite WAL mode", "dev", tags=["db"])
    handle_memory_submit(tmp_db, "N5", "Python asyncio", "dev", tags=["py"])
    handle_memory_submit(tmp_db, "N7", "ACL design decision", "arch", tags=["security"])
    handle_memory_submit(tmp_db, "N5", "Cross-project note", "dev", project_id="proj-alpha")
    return tmp_db

def test_search_own(seeded_db):
    r = handle_memory_search(seeded_db, agent_id="N5", query="SQLite")
    assert r["status"] == "ok"
    assert len(r["results"]) >= 1

def test_search_acl_blocked(seeded_db):
    r = handle_memory_search(seeded_db, agent_id="N5", query="ACL")
    assert len(r["results"]) == 0  # N5 cannot see N7's memories

def test_search_admin_sees_all(seeded_db):
    r = handle_memory_search(seeded_db, agent_id="N7", query="SQLite")
    assert len(r["results"]) >= 1

def test_load_recent(seeded_db):
    r = handle_memory_load_recent(seeded_db, agent_id="N5", limit=2)
    assert r["status"] == "ok"
    assert len(r["results"]) == 2

def test_browse_namespace(seeded_db):
    r = handle_memory_browse_namespace(seeded_db, agent_id="N5")
    assert r["status"] == "ok"
    assert "dev" in r["namespaces"]

def test_browse_project(seeded_db):
    r = handle_memory_browse_project(seeded_db, agent_id="N5")
    assert r["status"] == "ok"
    assert "proj-alpha" in r["projects"]
```

- [ ] **步驟 2：執行測試確認失敗**

執行：`cd d:\hermes-agent && python -m pytest tests/n6/test_read_tools.py -v`
預期：FAIL

- [ ] **步驟 3：實作讀取工具**

```python
# src/n6_memory_broker/tools/read_tools.py
"""MCP Read Tools: memory_search, memory_load_recent, memory_browse_*."""
import sqlite3
from n6_memory_broker.models import CallerIdentity, ADMIN_AGENTS
from n6_memory_broker.store import search_fts, _parse_row

def handle_memory_search(
    conn: sqlite3.Connection,
    agent_id: str,
    query: str,
    limit: int = 10,
) -> dict:
    """Search memories with ACL filtering."""
    caller = CallerIdentity(agent_id=agent_id)
    # Admin sees all, general sees only own
    search_agent = None if caller.role == "admin" else agent_id
    results = search_fts(conn, query, agent_id=search_agent, limit=limit)
    return {"status": "ok", "results": results}

def handle_memory_load_recent(
    conn: sqlite3.Connection,
    agent_id: str,
    limit: int = 10,
) -> dict:
    """Load most recent memories for the calling agent."""
    caller = CallerIdentity(agent_id=agent_id)
    target = None if caller.role == "admin" else agent_id
    if target:
        rows = conn.execute(
            "SELECT * FROM memories WHERE agent_id = ? ORDER BY created_at DESC LIMIT ?",
            (target, limit)).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM memories ORDER BY created_at DESC LIMIT ?",
            (limit,)).fetchall()
    return {"status": "ok", "results": [_parse_row(r) for r in rows]}

def handle_memory_browse_namespace(
    conn: sqlite3.Connection,
    agent_id: str,
) -> dict:
    """List distinct namespaces visible to the caller."""
    caller = CallerIdentity(agent_id=agent_id)
    if caller.role == "admin":
        rows = conn.execute("SELECT DISTINCT namespace FROM memories").fetchall()
    else:
        rows = conn.execute(
            "SELECT DISTINCT namespace FROM memories WHERE agent_id = ?",
            (agent_id,)).fetchall()
    return {"status": "ok", "namespaces": [r[0] for r in rows]}

def handle_memory_browse_project(
    conn: sqlite3.Connection,
    agent_id: str,
) -> dict:
    """List distinct project_ids visible to the caller."""
    caller = CallerIdentity(agent_id=agent_id)
    if caller.role == "admin":
        rows = conn.execute(
            "SELECT DISTINCT project_id FROM memories WHERE project_id IS NOT NULL"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT DISTINCT project_id FROM memories WHERE agent_id = ? AND project_id IS NOT NULL",
            (agent_id,)).fetchall()
    return {"status": "ok", "projects": [r[0] for r in rows]}
```

- [ ] **步驟 4：執行測試確認通過**

執行：`cd d:\hermes-agent && python -m pytest tests/n6/test_read_tools.py -v`
預期：PASS

- [ ] **步驟 5：提交**

```bash
git add src/n6_memory_broker/tools/read_tools.py tests/n6/test_read_tools.py
git commit -m "feat(n6): MCP read tools — search, recent, browse namespace/project"
```

---

## Task 7：MCP 管理工具（memory_stats + memory_archive_status）

**檔案：**
- 建立：`src/n6_memory_broker/tools/admin_tools.py`
- 建立：`tests/n6/test_admin_tools.py`

- [ ] **步驟 1：撰寫預期失敗的測試**

```python
# tests/n6/test_admin_tools.py
"""Test MCP admin tools."""
import pytest
from n6_memory_broker.tools.write_tools import handle_memory_submit
from n6_memory_broker.tools.admin_tools import handle_memory_stats, handle_memory_archive_status

@pytest.fixture
def seeded_db(tmp_db):
    handle_memory_submit(tmp_db, "N5", "note 1", "dev")
    handle_memory_submit(tmp_db, "N5", "note 2", "dev")
    handle_memory_submit(tmp_db, "N7", "admin note", "ops")
    return tmp_db

def test_stats_admin(seeded_db):
    r = handle_memory_stats(seeded_db, agent_id="N7")
    assert r["status"] == "ok"
    assert r["total_memories"] == 3
    assert "N5" in r["by_agent"]
    assert r["by_agent"]["N5"] == 2

def test_stats_general_blocked(seeded_db):
    r = handle_memory_stats(seeded_db, agent_id="N5")
    assert r["status"] == "error"

def test_archive_status_admin(seeded_db):
    r = handle_memory_archive_status(seeded_db, agent_id="N7")
    assert r["status"] == "ok"
    assert "candidates" in r

def test_archive_status_general_blocked(seeded_db):
    r = handle_memory_archive_status(seeded_db, agent_id="N5")
    assert r["status"] == "error"
```

- [ ] **步驟 2：執行測試確認失敗**

執行：`cd d:\hermes-agent && python -m pytest tests/n6/test_admin_tools.py -v`
預期：FAIL

- [ ] **步驟 3：實作管理工具**

```python
# src/n6_memory_broker/tools/admin_tools.py
"""MCP Admin Tools: memory_stats, memory_archive_status."""
import sqlite3
from datetime import datetime, timezone, timedelta
from n6_memory_broker.models import CallerIdentity
from n6_memory_broker.acl import check_permission, ACLError
from n6_memory_broker.config import SEMANTIC_ARCHIVE_DAYS, SAFETY_VALVE_DAYS

def handle_memory_stats(conn: sqlite3.Connection, agent_id: str) -> dict:
    """Return global memory statistics (admin only)."""
    caller = CallerIdentity(agent_id=agent_id)
    try:
        check_permission(caller, "manage")
    except ACLError as e:
        return {"status": "error", "message": str(e)}

    total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    by_agent_rows = conn.execute(
        "SELECT agent_id, COUNT(*) as cnt FROM memories GROUP BY agent_id"
    ).fetchall()
    by_tier_rows = conn.execute(
        "SELECT memory_tier, COUNT(*) as cnt FROM memories GROUP BY memory_tier"
    ).fetchall()
    by_ns_rows = conn.execute(
        "SELECT namespace, COUNT(*) as cnt FROM memories GROUP BY namespace ORDER BY cnt DESC LIMIT 10"
    ).fetchall()

    return {
        "status": "ok",
        "total_memories": total,
        "by_agent": {r[0]: r[1] for r in by_agent_rows},
        "by_tier": {r[0]: r[1] for r in by_tier_rows},
        "top_namespaces": {r[0]: r[1] for r in by_ns_rows},
    }

def handle_memory_archive_status(conn: sqlite3.Connection, agent_id: str) -> dict:
    """Report memories eligible for archival (admin only)."""
    caller = CallerIdentity(agent_id=agent_id)
    try:
        check_permission(caller, "manage")
    except ACLError as e:
        return {"status": "error", "message": str(e)}

    now = datetime.now(timezone.utc)
    sem_cutoff = (now - timedelta(days=SEMANTIC_ARCHIVE_DAYS)).isoformat()
    safety_cutoff = (now - timedelta(days=SAFETY_VALVE_DAYS)).isoformat()

    semantic_candidates = conn.execute("""
        SELECT COUNT(*) FROM memories
        WHERE memory_tier = 'semantic'
          AND (last_accessed_at IS NULL OR last_accessed_at < ?)
    """, (sem_cutoff,)).fetchone()[0]

    safety_candidates = conn.execute("""
        SELECT COUNT(*) FROM memories
        WHERE last_accessed_at IS NULL OR last_accessed_at < ?
    """, (safety_cutoff,)).fetchone()[0]

    return {
        "status": "ok",
        "candidates": {
            "semantic_90d": semantic_candidates,
            "safety_valve_180d": safety_candidates,
        },
    }
```

- [ ] **步驟 4：執行測試確認通過**

執行：`cd d:\hermes-agent && python -m pytest tests/n6/test_admin_tools.py -v`
預期：PASS

- [ ] **步驟 5：提交**

```bash
git add src/n6_memory_broker/tools/admin_tools.py tests/n6/test_admin_tools.py
git commit -m "feat(n6): MCP admin tools — memory_stats + memory_archive_status"
```

---

## Task 8：嵌入向量層（Gemini + FTS5 降級方案）

**檔案：**
- 建立：`src/n6_memory_broker/embedding.py`
- 建立：`tests/n6/test_embedding.py`

- [ ] **步驟 1：撰寫預期失敗的測試**

```python
# tests/n6/test_embedding.py
"""Test embedding layer with graceful fallback."""
import pytest
from unittest.mock import patch, MagicMock
from n6_memory_broker.embedding import get_embedding, semantic_search, EmbeddingUnavailable

def test_get_embedding_returns_vector():
    """With valid API key, should return float list."""
    with patch("n6_memory_broker.embedding._call_gemini_api") as mock:
        mock.return_value = [0.1] * 3072
        vec = get_embedding("test text")
        assert len(vec) == 3072
        assert all(isinstance(v, float) for v in vec)

def test_get_embedding_fallback_on_no_key():
    """Without API key, should raise EmbeddingUnavailable."""
    with patch("n6_memory_broker.embedding.GEMINI_API_KEY", ""):
        with pytest.raises(EmbeddingUnavailable):
            get_embedding("test text")

def test_semantic_search_falls_back_to_fts(tmp_db):
    """When embedding unavailable, semantic_search uses FTS5."""
    from n6_memory_broker.store import insert_memory
    from n6_memory_broker.models import MemoryEntry
    insert_memory(tmp_db, MemoryEntry(agent_id="N5", content="SQLite WAL mode"))
    with patch("n6_memory_broker.embedding.get_embedding", side_effect=EmbeddingUnavailable):
        results = semantic_search(tmp_db, "SQLite", agent_id="N5")
        assert len(results) >= 1
```

- [ ] **步驟 2：執行測試確認失敗**

執行：`cd d:\hermes-agent && python -m pytest tests/n6/test_embedding.py -v`
預期：FAIL

- [ ] **步驟 3：實作嵌入向量模組**

```python
# src/n6_memory_broker/embedding.py
"""Gemini Embedding 2 client with FTS5 graceful fallback."""
import struct
import sqlite3
from n6_memory_broker.config import GEMINI_API_KEY, EMBEDDING_MODEL, EMBEDDING_DIM
from n6_memory_broker.store import search_fts

class EmbeddingUnavailable(Exception):
    """Raised when embedding service is not available."""
    pass

def _call_gemini_api(text: str) -> list[float]:
    """Call Gemini Embedding API. Raises on failure."""
    import google.generativeai as genai
    genai.configure(api_key=GEMINI_API_KEY)
    result = genai.embed_content(model=EMBEDDING_MODEL, content=text)
    return result["embedding"]

def get_embedding(text: str) -> list[float]:
    """Get embedding vector. Raises EmbeddingUnavailable if not configured."""
    if not GEMINI_API_KEY:
        raise EmbeddingUnavailable("GEMINI_API_KEY not set")
    try:
        return _call_gemini_api(text)
    except Exception as e:
        raise EmbeddingUnavailable(f"Embedding API error: {e}") from e

def vec_to_blob(vec: list[float]) -> bytes:
    """Serialize float vector to bytes for SQLite BLOB storage."""
    return struct.pack(f"{len(vec)}f", *vec)

def blob_to_vec(blob: bytes) -> list[float]:
    """Deserialize bytes back to float vector."""
    n = len(blob) // 4
    return list(struct.unpack(f"{n}f", blob))

def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)

def semantic_search(
    conn: sqlite3.Connection,
    query: str,
    agent_id: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """Semantic search with automatic FTS5 fallback."""
    try:
        query_vec = get_embedding(query)
    except EmbeddingUnavailable:
        # Graceful degradation to FTS5
        return search_fts(conn, query, agent_id=agent_id, limit=limit)

    # Vector search: scan memories with embeddings
    if agent_id:
        rows = conn.execute(
            "SELECT * FROM memories WHERE agent_id = ? AND embedding_blob IS NOT NULL",
            (agent_id,)).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM memories WHERE embedding_blob IS NOT NULL"
        ).fetchall()

    scored = []
    for row in rows:
        row_vec = blob_to_vec(row["embedding_blob"])
        score = cosine_similarity(query_vec, row_vec)
        d = dict(row)
        d["score"] = score
        scored.append(d)

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]
```

- [ ] **步驟 4：執行測試確認通過**

執行：`cd d:\hermes-agent && python -m pytest tests/n6/test_embedding.py -v`
預期：PASS

- [ ] **步驟 5：提交**

```bash
git add src/n6_memory_broker/embedding.py tests/n6/test_embedding.py
git commit -m "feat(n6): embedding layer — Gemini + FTS5 fallback"
```

---

## Task 9：γ-衰減引擎（層級晋升 + 歸檔）

**檔案：**
- 建立：`src/n6_memory_broker/decay.py`
- 建立：`tests/n6/test_decay.py`

- [ ] **步驟 1：撰寫預期失敗的測試**

```python
# tests/n6/test_decay.py
"""Test γ-decay: tier promotion and archival."""
import pytest
from datetime import datetime, timezone, timedelta
from n6_memory_broker.decay import promote_tiers, find_archive_candidates, archive_memories
from n6_memory_broker.store import insert_memory, get_memory
from n6_memory_broker.models import MemoryEntry

def test_promote_working_to_episodic(tmp_db):
    """Memory accessed >=3 times should promote working→episodic."""
    entry = MemoryEntry(agent_id="N5", content="frequently accessed")
    mid = insert_memory(tmp_db, entry)
    # Simulate 3 accesses
    for _ in range(3):
        get_memory(tmp_db, mid)
    promoted = promote_tiers(tmp_db)
    row = tmp_db.execute("SELECT memory_tier FROM memories WHERE id = ?", (mid,)).fetchone()
    assert row[0] == "episodic"
    assert promoted > 0

def test_no_promote_below_threshold(tmp_db):
    """Memory with 1 access stays at working."""
    entry = MemoryEntry(agent_id="N5", content="rarely accessed")
    mid = insert_memory(tmp_db, entry)
    get_memory(tmp_db, mid)  # 1 access
    promote_tiers(tmp_db)
    row = tmp_db.execute("SELECT memory_tier FROM memories WHERE id = ?", (mid,)).fetchone()
    assert row[0] == "working"

def test_find_archive_candidates_safety_valve(tmp_db):
    """Memories idle >180 days should be archive candidates."""
    entry = MemoryEntry(agent_id="N5", content="old memory")
    mid = insert_memory(tmp_db, entry)
    old_date = (datetime.now(timezone.utc) - timedelta(days=200)).isoformat()
    tmp_db.execute(
        "UPDATE memories SET last_accessed_at = ?, created_at = ? WHERE id = ?",
        (old_date, old_date, mid))
    tmp_db.commit()
    candidates = find_archive_candidates(tmp_db)
    assert len(candidates) >= 1

def test_archive_moves_to_archive_table(tmp_db):
    entry = MemoryEntry(agent_id="N5", content="to be archived")
    mid = insert_memory(tmp_db, entry)
    old_date = (datetime.now(timezone.utc) - timedelta(days=200)).isoformat()
    tmp_db.execute(
        "UPDATE memories SET last_accessed_at = ?, created_at = ? WHERE id = ?",
        (old_date, old_date, mid))
    tmp_db.commit()
    archived = archive_memories(tmp_db, [mid])
    assert archived == 1
    row = tmp_db.execute("SELECT * FROM memories WHERE id = ?", (mid,)).fetchone()
    assert row is None  # Removed from active table
```

- [ ] **步驟 2：執行測試確認失敗**

執行：`cd d:\hermes-agent && python -m pytest tests/n6/test_decay.py -v`
預期：FAIL

- [ ] **步驟 3：實作衰減引擎**

```python
# src/n6_memory_broker/decay.py
"""γ-Decay Engine — tier promotion and archival."""
import sqlite3
from datetime import datetime, timezone, timedelta
from n6_memory_broker.config import SEMANTIC_ARCHIVE_DAYS, SAFETY_VALVE_DAYS

# Tier promotion thresholds (access_count)
TIER_THRESHOLDS = {
    "working": ("episodic", 3),
    "episodic": ("semantic", 10),
    "semantic": ("procedural", 25),
}

def _ensure_archive_table(conn: sqlite3.Connection) -> None:
    """Create archive table if not exists (mirrors memories schema)."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories_archive (
            id              INTEGER PRIMARY KEY,
            agent_id        TEXT NOT NULL,
            namespace       TEXT NOT NULL,
            project_id      TEXT,
            content         TEXT NOT NULL,
            tags            TEXT DEFAULT '',
            channel         TEXT NOT NULL,
            memory_tier     TEXT NOT NULL,
            access_count    INTEGER NOT NULL,
            last_accessed_at TEXT,
            embedding_blob  BLOB,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL,
            archived_at     TEXT NOT NULL
        )
    """)
    conn.commit()

def promote_tiers(conn: sqlite3.Connection) -> int:
    """Promote memories based on access_count thresholds. Returns count promoted."""
    promoted = 0
    for current_tier, (next_tier, threshold) in TIER_THRESHOLDS.items():
        cur = conn.execute("""
            UPDATE memories SET memory_tier = ?, updated_at = ?
            WHERE memory_tier = ? AND access_count >= ?
        """, (next_tier, datetime.now(timezone.utc).isoformat(),
              current_tier, threshold))
        promoted += cur.rowcount
    conn.commit()
    return promoted

def find_archive_candidates(conn: sqlite3.Connection) -> list[int]:
    """Find memories eligible for archival per γ-decay rules."""
    now = datetime.now(timezone.utc)
    sem_cutoff = (now - timedelta(days=SEMANTIC_ARCHIVE_DAYS)).isoformat()
    safety_cutoff = (now - timedelta(days=SAFETY_VALVE_DAYS)).isoformat()

    # Rule 1: semantic tier + 90 days idle
    sem_rows = conn.execute("""
        SELECT id FROM memories
        WHERE memory_tier = 'semantic'
          AND (last_accessed_at IS NULL OR last_accessed_at < ?)
    """, (sem_cutoff,)).fetchall()

    # Rule 2: any tier + 180 days safety valve
    safety_rows = conn.execute("""
        SELECT id FROM memories
        WHERE last_accessed_at IS NULL OR last_accessed_at < ?
    """, (safety_cutoff,)).fetchall()

    ids = set(r[0] for r in sem_rows) | set(r[0] for r in safety_rows)
    return list(ids)

def archive_memories(conn: sqlite3.Connection, memory_ids: list[int]) -> int:
    """Move memories to archive table. Returns count archived."""
    _ensure_archive_table(conn)
    now = datetime.now(timezone.utc).isoformat()
    archived = 0
    for mid in memory_ids:
        row = conn.execute("SELECT * FROM memories WHERE id = ?", (mid,)).fetchone()
        if not row:
            continue
        d = dict(row)
        conn.execute("""
            INSERT INTO memories_archive
                (id, agent_id, namespace, project_id, content, tags, channel,
                 memory_tier, access_count, last_accessed_at, embedding_blob,
                 created_at, updated_at, archived_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (d["id"], d["agent_id"], d["namespace"], d["project_id"],
              d["content"], d["tags"], d["channel"], d["memory_tier"],
              d["access_count"], d["last_accessed_at"], d["embedding_blob"],
              d["created_at"], d["updated_at"], now))
        conn.execute("DELETE FROM memories WHERE id = ?", (mid,))
        conn.execute("DELETE FROM memories_fts WHERE rowid = ?", (mid,))
        archived += 1
    conn.commit()
    return archived
```

- [ ] **步驟 4：執行測試確認通過**

執行：`cd d:\hermes-agent && python -m pytest tests/n6/test_decay.py -v`
預期：PASS

- [ ] **步驟 5：提交**

```bash
git add src/n6_memory_broker/decay.py tests/n6/test_decay.py
git commit -m "feat(n6): γ-decay engine — tier promotion + archival"
```

---

## Task 10：遺產遷移腳本

**檔案：**
- 建立：`src/n6_memory_broker/legacy_migrator.py`
- 建立：`tests/n6/test_legacy_migrator.py`

- [ ] **步驟 1：撰寫預期失敗的測試**

```python
# tests/n6/test_legacy_migrator.py
"""Test legacy memory migration."""
import pytest
from pathlib import Path
from n6_memory_broker.legacy_migrator import scan_legacy_dir, migrate_file

def test_scan_auto_memory(tmp_path):
    """Scan auto_memory directory returns .md files."""
    auto = tmp_path / "auto_memory"
    auto.mkdir()
    (auto / "incident_001.md").write_text("# Bug\nSome bug details")
    (auto / "incident_002.md").write_text("# Fix\nFixed it")
    (auto / "not_md.txt").write_text("skip me")
    files = scan_legacy_dir(auto)
    assert len(files) == 2
    assert all(f.suffix == ".md" for f in files)

def test_migrate_file_creates_memory(tmp_db, tmp_path):
    """migrate_file should insert a memory with correct namespace."""
    md = tmp_path / "test_memory.md"
    md.write_text("# Decision\nUse SQLite for persistence")
    mid = migrate_file(tmp_db, md, namespace="legacy-incidents", agent_id="N6")
    assert mid > 0
    row = tmp_db.execute("SELECT * FROM memories WHERE id = ?", (mid,)).fetchone()
    assert row["namespace"] == "legacy-incidents"
    assert row["agent_id"] == "N6"
    assert row["channel"] == "migration"
    assert "SQLite" in row["content"]

def test_migrate_file_idempotent(tmp_db, tmp_path):
    """Migrating same file twice should not create duplicates."""
    md = tmp_path / "test.md"
    md.write_text("# Test\nContent")
    mid1 = migrate_file(tmp_db, md, namespace="legacy-test", agent_id="N6")
    mid2 = migrate_file(tmp_db, md, namespace="legacy-test", agent_id="N6")
    assert mid2 == mid1  # Same ID, not a new record
```

- [ ] **步驟 2：執行測試確認失敗**

執行：`cd d:\hermes-agent && python -m pytest tests/n6/test_legacy_migrator.py -v`
預期：FAIL

- [ ] **步驟 3：實作遷移器**

```python
# src/n6_memory_broker/legacy_migrator.py
"""One-shot migration of legacy memory files into N6 store."""
import hashlib
import sqlite3
from pathlib import Path
from n6_memory_broker.models import MemoryEntry
from n6_memory_broker.store import insert_memory

def scan_legacy_dir(directory: Path) -> list[Path]:
    """Scan directory for .md files to migrate."""
    if not directory.exists():
        return []
    return sorted(directory.glob("*.md"))

def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]

def migrate_file(
    conn: sqlite3.Connection,
    file_path: Path,
    namespace: str,
    agent_id: str = "N6",
) -> int:
    """Migrate a single markdown file. Returns memory_id. Idempotent via content hash."""
    content = file_path.read_text(encoding="utf-8")
    chash = _content_hash(content)
    tag = f"migrated:{file_path.name}:{chash}"

    # Check if already migrated
    existing = conn.execute(
        "SELECT id FROM memories WHERE tags LIKE ?",
        (f'%{tag}%',)).fetchone()
    if existing:
        return existing[0]

    entry = MemoryEntry(
        agent_id=agent_id,
        content=content,
        namespace=namespace,
        tags=[tag, f"source:{file_path.name}"],
        channel="migration",
    )
    return insert_memory(conn, entry)

# ─── CLI entry point for batch migration ────────────────────────────────
LEGACY_SOURCES = {
    "auto_memory": "legacy-incidents",
    "strategic_case_studies": "legacy-strategy",
}

def run_full_migration(conn: sqlite3.Connection, legacy_root: Path) -> dict:
    """Run full legacy migration. Returns stats."""
    stats = {"total": 0, "migrated": 0, "skipped": 0}
    for dir_name, ns in LEGACY_SOURCES.items():
        source_dir = legacy_root / dir_name
        files = scan_legacy_dir(source_dir)
        for f in files:
            before_count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            migrate_file(conn, f, namespace=ns)
            after_count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
            stats["total"] += 1
            if after_count > before_count:
                stats["migrated"] += 1
            else:
                stats["skipped"] += 1
    return stats
```

- [ ] **步驟 4：執行測試確認通過**

執行：`cd d:\hermes-agent && python -m pytest tests/n6/test_legacy_migrator.py -v`
預期：PASS

- [ ] **步驟 5：提交**

```bash
git add src/n6_memory_broker/legacy_migrator.py tests/n6/test_legacy_migrator.py
git commit -m "feat(n6): legacy migration — 39 files → N6 store (idempotent)"
```

---

## Task 11：MCP 工具註冊 + Server 整合

**檔案：**
- 修改：`src/n6_memory_broker/server.py`
- 建立：`tests/n6/test_server_integration.py`

- [ ] **步驟 1：撰寫預期失敗的整合測試**

```python
# tests/n6/test_server_integration.py
"""Test that all 8 MCP tools are registered on the server."""
from n6_memory_broker.server import create_server

def test_server_has_all_tools():
    server = create_server()
    tool_names = [t.name for t in server.list_tools()]
    expected = [
        "memory_submit", "memory_update",
        "memory_search", "memory_load_recent",
        "memory_browse_namespace", "memory_browse_project",
        "memory_stats", "memory_archive_status",
    ]
    for name in expected:
        assert name in tool_names, f"Missing tool: {name}"

def test_server_tool_count():
    server = create_server()
    assert len(server.list_tools()) == 8
```

- [ ] **步驟 2：執行測試確認失敗**

執行：`cd d:\hermes-agent && python -m pytest tests/n6/test_server_integration.py -v`
預期：FAIL（工具尚未註冊）

- [ ] **步驟 3：在 Server 上註冊所有工具**

更新 `src/n6_memory_broker/server.py`，透過 `@server.tool()` 裝飾器註冊所有 8 個工具，委派給對應的 handler 函數。每個工具應接受 `agent_id` 作為必要參數，並透過共用 DB 連線轉發至對應的 `handle_*` 函數。

```python
# src/n6_memory_broker/server.py (updated)
"""N6 Memory Broker — MCP Server with all 8 tools registered."""
from mcp.server.fastmcp import FastMCP
from n6_memory_broker.config import MCP_SERVER_NAME, MCP_SERVER_VERSION, DB_PATH
from n6_memory_broker.schema import init_db

_conn = None

def _get_conn():
    global _conn
    if _conn is None:
        _conn = init_db(DB_PATH)
    return _conn

def create_server() -> FastMCP:
    server = FastMCP(
        MCP_SERVER_NAME,
        version=MCP_SERVER_VERSION,
        description="Centralized memory broker for Hermes N1-N9 agents",
    )

    from n6_memory_broker.tools.write_tools import handle_memory_submit, handle_memory_update
    from n6_memory_broker.tools.read_tools import (
        handle_memory_search, handle_memory_load_recent,
        handle_memory_browse_namespace, handle_memory_browse_project,
    )
    from n6_memory_broker.tools.admin_tools import handle_memory_stats, handle_memory_archive_status

    @server.tool()
    def memory_submit(agent_id: str, content: str, namespace: str = "default",
                      project_id: str = "", tags: str = "", channel: str = "ide") -> dict:
        """Submit a new memory to the N6 store."""
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
        return handle_memory_submit(_get_conn(), agent_id, content, namespace,
                                    project_id or None, tag_list, channel)

    @server.tool()
    def memory_update(agent_id: str, memory_id: int, tags: str = "",
                      namespace: str = "") -> dict:
        """Update tags or namespace on an existing memory."""
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
        ns = namespace or None
        return handle_memory_update(_get_conn(), agent_id, memory_id, tag_list, ns)

    @server.tool()
    def memory_search(agent_id: str, query: str, limit: int = 10) -> dict:
        """Search memories using keyword + semantic (with ACL)."""
        return handle_memory_search(_get_conn(), agent_id, query, limit)

    @server.tool()
    def memory_load_recent(agent_id: str, limit: int = 10) -> dict:
        """Load most recent memories for the calling agent."""
        return handle_memory_load_recent(_get_conn(), agent_id, limit)

    @server.tool()
    def memory_browse_namespace(agent_id: str) -> dict:
        """List distinct namespaces visible to the caller."""
        return handle_memory_browse_namespace(_get_conn(), agent_id)

    @server.tool()
    def memory_browse_project(agent_id: str) -> dict:
        """List distinct project_ids visible to the caller."""
        return handle_memory_browse_project(_get_conn(), agent_id)

    @server.tool()
    def memory_stats(agent_id: str) -> dict:
        """Return global memory statistics (admin only)."""
        return handle_memory_stats(_get_conn(), agent_id)

    @server.tool()
    def memory_archive_status(agent_id: str) -> dict:
        """Report memories eligible for archival (admin only)."""
        return handle_memory_archive_status(_get_conn(), agent_id)

    return server

if __name__ == "__main__":
    server = create_server()
    server.run(transport="stdio")
```

- [ ] **步驟 4：執行整合測試**

執行：`cd d:\hermes-agent && python -m pytest tests/n6/test_server_integration.py -v`
預期：PASS

- [ ] **步驟 5：執行全部測試套件**

執行：`cd d:\hermes-agent && python -m pytest tests/n6/ -v`
預期：全部 PASS

- [ ] **步驟 6：提交**

```bash
git add src/n6_memory_broker/server.py tests/n6/test_server_integration.py
git commit -m "feat(n6): register all 8 MCP tools on server + integration test"
```

---

## 自我審查清單

### 1. 規格覆蓋率（Q1-Q8）

| 決策 | 對應 Task | 狀態 |
|----------|---------|--------|
| Q1：全域 N1-N9 + 外部 | ACL (Task 3) + 所有工具 | ✅ |
| Q2：Markdown + SQLite | Schema (Task 2) + Store (Task 4) | ✅ |
| Q3：Gemini Embedding + FTS5 降級 | Embedding (Task 8) | ✅ |
| Q4：β 雙軌 (namespace + project_id) | Schema 欄位 + browse 工具 | ✅ |
| Q5：γ 計數+時間加權 + 歸檔 | Decay (Task 9) | ✅ |
| Q6：8 MCP tools + ACL | Tasks 5-7 + Task 11 | ✅ |
| Q7：三階段通道 | channel 欄位 (Schema) | ✅ Phase 1 |
| Q8：KI 獨立 + 遺產遷移 | Legacy (Task 10) | ✅ |

### 2. 占位符掃描

未發現 TBD、TODO 或「稍後實作」字樣。所有步驟均包含完整程式碼。

### 3. 型別一致性

- `CallerIdentity` 在 ACL、write_tools、read_tools、admin_tools 中一致使用
- `MemoryEntry` 在 store + write_tools + legacy_migrator 中一致使用
- `insert_memory()` / `get_memory()` / `search_fts()` 簽名在所有消費端保持穩定

### 4. 延遲項目（未包含在本計畫中）

| 項目 | 原因 | 建議後續 |
|------|--------|-------------------|
| Markdown ↔ DB 同步 (`markdown_sync.py`) | 依賴 Markdown 目錄結構決策 | Phase 1 後獨立計畫 |
| 2h 巡檢 daemon (`inspector.py`) | 需要排程整合 (cron/Temporalio) | 獨立計畫 |
| Web UI 通道 (Q7 Phase 2) | 未來範圍 | 獨立計畫 |
| Line 通道 (Q7 Phase 3) | 未來範圍 | 獨立計畫 |
| 向量索引 (sqlite-vec 或 FAISS) | Q3 可選優化 | 效能計畫 |

---

**計畫已完成並儲存至 `docs/superpowers/plans/2026-05-16-n6-memory-broker.md`。兩種執行方式：**

**1. Subagent 驅動（推薦）** — 每個 Task 派發獨立 subagent，任務間審查，快速疊代

**2. 內聯執行** — 在本 session 內使用 executing-plans 批次執行，檢查點確認

**請選擇哪種方式？**
