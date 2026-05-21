---
description: N7 記憶腳本開發守則
paths:
  - "memory/scripts/**/*.py"
  - "memory/session_state.db"
harness_version: 2.2.0
---
# N7 記憶腳本開發守則

1. **session_state.db** 僅可透過 `agent_session_db.py` 中的函式存取。
2. **禁止**直接執行 SQL 或使用 `sqlite3` 模組繞過 ORM。
3. **encoding**：所有腳本必須使用 `sys.stdout.reconfigure(encoding='utf-8')`。
4. **CLI 參數**：連字號格式（`--next-steps`），非底線（`--next_steps`）。
5. **錯誤處理**：DB 連線失敗時必須 Fail Loudly，禁止靜默吞掉例外。
