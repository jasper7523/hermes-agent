---
description: N7 Gateway 平台安全守則
paths:
  - "gateway/**"
  - "gateway/platforms/**"
harness_version: 2.2.0
---
# N7 Gateway 平台安全守則

1. **Token Lock**：平台適配器必須在 `connect()` 時呼叫 `acquire_scoped_lock()`，`disconnect()` 時呼叫 `release_scoped_lock()`。
2. **Prompt Caching**：嚴禁在對話中途改變 toolsets 或重建 system prompts。
3. **背景通知**：遵守 `display.background_process_notifications` 設定值。
4. **Profile 安全**：使用 `get_hermes_home()` 取得路徑，嚴禁寫死 `~/.hermes`。
5. **Schema 隔離**：Tool schema descriptions 禁止寫死跨 toolset 的工具名稱。
