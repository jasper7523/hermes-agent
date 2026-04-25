import sys
import asyncio
from pathlib import Path

AGENT_HUB_DIR = Path(r"d:\Agent_Hub")
sys.path.append(str(AGENT_HUB_DIR))
import tools.agent_event_bus as aeb

if __name__ == '__main__':
    test_file = r'd:\Agent_Hub\.agent_memory\auto_memory\COUNCIL_PROPOSAL_test.md'
    asyncio.run(aeb.process_council_proposal(test_file))
