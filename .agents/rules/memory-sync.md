---
description: N7 Memory Script Development Rules
paths:
  - "memory/scripts/**/*.py"
  - "memory/session_state.db"
harness_version: 2.2.1
---
# N7 Memory Script Development Rules

1. **session_state.db**: MUST only be accessed through functions in `agent_session_db.py`.
2. **No raw SQL**: DO NOT directly execute SQL or use the `sqlite3` module to bypass the ORM.
3. **Encoding**: All scripts MUST use `sys.stdout.reconfigure(encoding='utf-8')`.
4. **CLI arguments**: Use hyphen format (`--next-steps`), NOT underscore (`--next_steps`).
5. **Error handling**: WHEN DB connection fails, THEN Fail Loudly. DO NOT silently swallow exceptions.
