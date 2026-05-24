---
description: N7 Gateway Platform Safety Rules
paths:
  - "gateway/**"
  - "gateway/platforms/**"
harness_version: 2.2.1
---
# N7 Gateway Platform Safety Rules

1. **Token Lock**: Platform adapters MUST call `acquire_scoped_lock()` on `connect()` and `release_scoped_lock()` on `disconnect()`.
2. **Prompt Caching**: DO NOT alter toolsets or rebuild system prompts mid-conversation.
3. **Background Notifications**: Follow the `display.background_process_notifications` config value.
4. **Profile Safety**: Use `get_hermes_home()` to resolve paths. DO NOT hardcode `~/.hermes`.
5. **Schema Isolation**: Tool schema descriptions MUST NOT hardcode tool names from other toolsets.
