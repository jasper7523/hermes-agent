import json
import signal
import sys

<<<<<<< HEAD
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from tui_gateway.server import handle_request, resolve_skin, write_json
=======
from tui_gateway.server import dispatch, resolve_skin, write_json
>>>>>>> ce089169d578b96c82641f17186ba63c288b22d8

if hasattr(signal, "SIGPIPE"):
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
signal.signal(signal.SIGINT, signal.SIG_IGN)


def main():
    if not write_json({
        "jsonrpc": "2.0",
        "method": "event",
        "params": {"type": "gateway.ready", "payload": {"skin": resolve_skin()}},
    }):
        sys.exit(0)

    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            if not write_json({"jsonrpc": "2.0", "error": {"code": -32700, "message": "parse error"}, "id": None}):
                sys.exit(0)
            continue

        resp = dispatch(req)
        if resp is not None:
            if not write_json(resp):
                sys.exit(0)


if __name__ == "__main__":
    main()
