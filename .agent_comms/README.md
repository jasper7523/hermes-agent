# N7 Agent Mailbox

# .agent_comms/ — Agent Communication Mailbox
# Part of Jasper Strategic Hub (Harness v2.2) Three-Panel Communication Architecture

## Directory Structure
- `inbox/`  : Incoming task envelopes from other Agents (JSON)
- `outbox/` : Completed results awaiting relay to Event Bus (JSON)
- `archive/`: Historical envelopes for audit trail

## Protocol
- Messages use the Envelope JSON Schema defined in agent_communication_protocol.md
- Files are written atomically (write to .tmp then rename)
- inbox/ messages are claimed by setting status: "processing"
- Completed results go to outbox/ for N6 Event Bus to harvest

## Security
- This directory is agent-local; cross-agent writes go through N6 Event Bus only
- Per Harness §3 Permission Pipeline: no direct file modification across agents
