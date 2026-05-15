---
name: hermes-session
description: 手動管理 N7 Session Memory（載入 / 存檔 / 搜尋）
---

# /hermes-session — Session Memory 管理

> 連接 `hermes-agent.md` SMPP 協定，提供手動操作介面。

## 使用方式

使用者輸入 `/hermes-session` 加上子命令：

| 子命令 | 說明 |
|--------|------|
| `/hermes-session load` | 載入最近 3 筆 session |
| `/hermes-session save` | 立即觸發 session_save（不等 StepGate 計數器） |
| `/hermes-session search <關鍵字>` | 用 FTS5 搜尋歷史 session |
| `/hermes-session stats` | 顯示 session 統計 |

---

## Step 1: 解析子命令

從使用者的輸入中判斷子命令。若未指定，預設為 `load`。

---

## Step 2: 執行對應操作

### 2a. load

// turbo
```bash
python d:\hermes-agent\memory\scripts\session_load.py --agent N7 --limit 3
```

將輸出視為上次工作的延續脈絡。

### 2b. save

詢問使用者提供以下資訊（或從當前對話上下文自動歸納）：
- **summary**: 本次工作摘要
- **decisions**: 關鍵決策
- **next-steps**: 後續待辦
- **tags**: 標籤

然後執行：
```bash
python d:\hermes-agent\memory\scripts\session_save.py --agent N7 --summary "<摘要>" --decisions "<決策>" --next-steps "<待辦>" --tags "<標籤>" --steps <當前StepGate計數>
```

### 2c. search

// turbo
```bash
python -c "import sys; sys.path.insert(0, 'd:/hermes-agent/memory/scripts'); from agent_session_db import *; conn=init_db(get_db_path()); [print(f'[{r[\"created_at\"][:16]}] {r[\"summary\"]}') for r in search_sessions(conn, '<使用者提供的關鍵字>', 'N7')]; conn.close()"
```

### 2d. stats

// turbo
```bash
python -c "import sys; sys.path.insert(0, 'd:/hermes-agent/memory/scripts'); from agent_session_db import *; conn=init_db(get_db_path()); s=get_session_stats(conn, 'N7'); print(f'Total sessions: {s[\"total\"]}'); print(f'Latest: {s[\"latest\"]}'); print(f'Total StepGate steps: {s[\"total_steps\"]}'); conn.close()"
```

---

## Step 3: 回報結果

將操作結果以結構化格式回報給使用者。
