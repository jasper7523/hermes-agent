# N6 Phase 2 — Task 14: Web UI (FastAPI + 靜態前端)

> **For agentic workers:** Use superpowers:subagent-driven-development to implement.

**Goal:** 提供 localhost Web 介面，可瀏覽、搜尋、管理 N6 記憶與巡檢歷史。

**Architecture:** FastAPI 後端 + vanilla HTML/JS/CSS 靜態前端。localhost:6060 綁定，admin 操作需確認。

**Tech Stack:** FastAPI, uvicorn, vanilla HTML/JS/CSS

**依賴：** `store.py`, `markdown_sync.py` (Task 12), `inspector.py` (Task 13), `config.py`

---

## 檔案結構

```
src/n6_memory_broker/
├── web/
│   ├── __init__.py
│   ├── app.py             # FastAPI 路由
│   └── static/
│       ├── index.html      # SPA 入口
│       ├── app.js          # 前端邏輯
│       └── style.css       # 樣式

tests/n6/
├── test_web_api.py         # API 測試
```

---

## Step 1：撰寫 API 測試

```python
# tests/n6/test_web_api.py
"""Test Web API endpoints."""
import pytest
from fastapi.testclient import TestClient
from n6_memory_broker.web.app import create_app
from n6_memory_broker.store import insert_memory
from n6_memory_broker.models import MemoryEntry


@pytest.fixture
def client(tmp_db, tmp_markdown_root):
    app = create_app(tmp_db, tmp_markdown_root)
    return TestClient(app)


def test_get_memories_empty(client):
    resp = client.get("/api/memories")
    assert resp.status_code == 200
    data = resp.json()
    assert data["memories"] == []
    assert data["total"] == 0


def test_get_memories_with_data(client, tmp_db):
    insert_memory(tmp_db, MemoryEntry(agent_id="N5", content="Web test"))
    resp = client.get("/api/memories")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_get_stats(client, tmp_db):
    insert_memory(tmp_db, MemoryEntry(agent_id="N5", content="Stat test"))
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_memories"] >= 1


def test_get_namespaces(client, tmp_db):
    insert_memory(tmp_db, MemoryEntry(agent_id="N5", content="A", namespace="dev"))
    insert_memory(tmp_db, MemoryEntry(agent_id="N5", content="B", namespace="ops"))
    resp = client.get("/api/namespaces")
    assert resp.status_code == 200
    ns = resp.json()["namespaces"]
    assert "dev" in ns
    assert "ops" in ns


def test_search_memories(client, tmp_db):
    insert_memory(tmp_db, MemoryEntry(agent_id="N5", content="Unique search term xyz"))
    resp = client.get("/api/memories?q=xyz")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1
```

- [ ] **Step 2：執行測試確認失敗**

- [ ] **Step 3：實作 web/app.py**

```python
# src/n6_memory_broker/web/__init__.py
"""N6 Web UI package."""

# src/n6_memory_broker/web/app.py
"""FastAPI application for N6 Memory Broker Web UI."""
import sqlite3
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


def create_app(
    conn: sqlite3.Connection,
    md_root: Path | None = None,
) -> FastAPI:
    app = FastAPI(title="N6 Memory Broker", version="2.0")

    static_dir = Path(__file__).parent / "static"

    @app.get("/")
    async def index():
        return FileResponse(static_dir / "index.html")

    @app.get("/api/memories")
    async def list_memories(
        q: str = Query(None),
        namespace: str = Query(None),
        agent_id: str = Query(None),
        limit: int = Query(50, le=200),
        offset: int = Query(0),
    ):
        if q:
            rows = conn.execute(
                """SELECT m.* FROM memories m
                   JOIN memories_fts f ON m.id = f.rowid
                   WHERE memories_fts MATCH ?
                   ORDER BY rank LIMIT ? OFFSET ?""",
                (q, limit, offset),
            ).fetchall()
            total_row = conn.execute(
                """SELECT COUNT(*) as cnt FROM memories m
                   JOIN memories_fts f ON m.id = f.rowid
                   WHERE memories_fts MATCH ?""", (q,)
            ).fetchone()
        else:
            wheres, params = [], []
            if namespace:
                wheres.append("namespace = ?")
                params.append(namespace)
            if agent_id:
                wheres.append("agent_id = ?")
                params.append(agent_id)
            where_clause = f"WHERE {' AND '.join(wheres)}" if wheres else ""
            rows = conn.execute(
                f"SELECT * FROM memories {where_clause} ORDER BY id DESC LIMIT ? OFFSET ?",
                params + [limit, offset],
            ).fetchall()
            total_row = conn.execute(
                f"SELECT COUNT(*) as cnt FROM memories {where_clause}", params
            ).fetchone()

        return {
            "memories": [dict(r) for r in rows],
            "total": total_row["cnt"] if total_row else 0,
        }

    @app.get("/api/memories/{memory_id}")
    async def get_memory(memory_id: int):
        row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
        if not row:
            return {"error": "Not found"}, 404
        return dict(row)

    @app.get("/api/stats")
    async def stats():
        total = conn.execute("SELECT COUNT(*) as cnt FROM memories").fetchone()
        tiers = conn.execute(
            "SELECT memory_tier, COUNT(*) as cnt FROM memories GROUP BY memory_tier"
        ).fetchall()
        agents = conn.execute(
            "SELECT agent_id, COUNT(*) as cnt FROM memories GROUP BY agent_id"
        ).fetchall()
        return {
            "total_memories": total["cnt"] if total else 0,
            "by_tier": {r["memory_tier"]: r["cnt"] for r in tiers},
            "by_agent": {r["agent_id"]: r["cnt"] for r in agents},
        }

    @app.get("/api/namespaces")
    async def namespaces():
        rows = conn.execute(
            "SELECT DISTINCT namespace FROM memories ORDER BY namespace"
        ).fetchall()
        return {"namespaces": [r["namespace"] for r in rows]}

    # Mount static files last
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    return app
```

- [ ] **Step 4：建立靜態前端檔案**

> 前端 HTML/JS/CSS 由 subagent 使用 web_application_development 規範產生，
> 需包含：搜尋列、namespace 側邊欄、統計儀表板、記憶列表。
> 此處僅提供 index.html 骨架供 API 測試通過。

```html
<!-- src/n6_memory_broker/web/static/index.html -->
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>N6 Memory Broker</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <div id="app">
        <h1>N6 Memory Broker</h1>
        <div id="search-bar"><input type="text" id="q" placeholder="Search..."></div>
        <div id="stats"></div>
        <div id="memories"></div>
    </div>
    <script src="/static/app.js"></script>
</body>
</html>
```

- [ ] **Step 5：執行測試確認通過**

執行：`cd D:\Agent_Hub\agents\Mem_Agent && python -m pytest tests/n6/test_web_api.py -v`

- [ ] **Step 6：提交**

```bash
git add src/n6_memory_broker/web/ tests/n6/test_web_api.py
git commit -m "feat(n6): web UI — FastAPI backend + static frontend skeleton"
```

---

## PyYAML + FastAPI 依賴更新

在所有 Task 完成後，需更新 `pyproject.toml`：

```toml
# 新增 dependencies
dependencies = [
    "mcp[cli]>=1.0",
    "pydantic>=2.0",
    "google-genai>=1.0",
    "pyyaml>=6.0",
    "fastapi>=0.100",
    "uvicorn>=0.30",
]
```

執行：`cd D:\Agent_Hub\agents\Mem_Agent && pip install -e ".[dev]"`
