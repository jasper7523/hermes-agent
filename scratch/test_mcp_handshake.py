"""
MCP Handshake Simulator v2 — 使用 line-delimited JSON (MCP SDK 1.27.0 實際使用的協議)
"""
import subprocess
import json
import sys
import threading
import time


def read_line_response(stdout, label, timeout=15):
    """從 stdout 讀取一行 JSON"""
    result = {"ok": False, "data": None, "error": None}

    def _read():
        try:
            line = stdout.readline()
            if not line:
                result["error"] = "EOF (empty read)"
                return
            decoded = line.decode("utf-8", errors="replace").strip()
            if not decoded:
                result["error"] = "Empty line"
                return
            result["data"] = json.loads(decoded)
            result["ok"] = True
        except Exception as e:
            result["error"] = str(e)

    t = threading.Thread(target=_read, daemon=True)
    t.start()
    t.join(timeout=timeout)
    if t.is_alive():
        result["error"] = f"TIMEOUT ({timeout}s)"
    return result


def send_line(stdin, request):
    """Send JSON-RPC as single line"""
    msg = json.dumps(request, ensure_ascii=False) + "\n"
    stdin.write(msg.encode("utf-8"))
    stdin.flush()


def test_server(name, script_path):
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"Script:  {script_path}")
    print(f"{'='*60}")

    proc = subprocess.Popen(
        [
            r"D:\Agent_Hub\tools\venv_mcp\Scripts\python.exe",
            "-X", "utf8", "-u",
            script_path,
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
    )

    # Capture stderr in background
    stderr_lines = []
    def _read_stderr():
        try:
            for line in proc.stderr:
                stderr_lines.append(line.decode("utf-8", errors="replace").strip())
        except:
            pass
    stderr_thread = threading.Thread(target=_read_stderr, daemon=True)
    stderr_thread.start()

    time.sleep(1.0)  # Let server initialize

    # Check if process already died
    if proc.poll() is not None:
        stderr_thread.join(timeout=2)
        print(f"  !! Server CRASHED on startup! exit code: {proc.returncode}")
        print(f"  !! stderr:")
        for line in stderr_lines:
            print(f"       {line}")
        return

    print(f"  Server PID: {proc.pid} (alive)")

    # Step 1: initialize
    print("\n  [1] Sending initialize...")
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-diag", "version": "1.0"},
        },
    }
    try:
        send_line(proc.stdin, init_req)
    except Exception as e:
        print(f"  !! Failed to send initialize: {e}")
        proc.terminate()
        return

    resp1 = read_line_response(proc.stdout, "initialize", timeout=10)
    if not resp1["ok"]:
        print(f"  !! initialize FAILED: {resp1['error']}")
        stderr_thread.join(timeout=2)
        print(f"  !! stderr:")
        for line in stderr_lines:
            print(f"       {line}")
        proc.terminate()
        return
    print(f"  << initialize OK")
    server_info = resp1["data"].get("result", {}).get("serverInfo", {})
    print(f"     serverInfo: {json.dumps(server_info, ensure_ascii=False)}")

    # Step 1.5: Send initialized notification
    initialized_notif = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
    }
    send_line(proc.stdin, initialized_notif)
    print("  [1.5] Sent initialized notification")

    time.sleep(0.3)

    # Step 2: tools/list
    print("\n  [2] Sending tools/list...")
    list_req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {},
    }
    send_line(proc.stdin, list_req)

    resp2 = read_line_response(proc.stdout, "tools/list", timeout=10)
    if not resp2["ok"]:
        print(f"  !! tools/list FAILED: {resp2['error']}")
        stderr_thread.join(timeout=2)
        print(f"  !! stderr:")
        for line in stderr_lines:
            print(f"       {line}")
        proc.terminate()
        return
    print(f"  << tools/list OK")
    tools = resp2["data"].get("result", {}).get("tools", [])
    print(f"     Found {len(tools)} tools:")
    for tool in tools:
        desc_preview = tool.get("description", "")[:80]
        print(f"       - {tool['name']}: {desc_preview}")

    # Step 3: Call ping (or say_hello for hello server)
    tool_name = "ping" if "gatekeeper" in name.lower() else "say_hello"
    tool_args = {} if tool_name == "ping" else {"text": "test"}
    print(f"\n  [3] Calling {tool_name}...")
    call_req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": tool_args,
        },
    }
    send_line(proc.stdin, call_req)

    resp3 = read_line_response(proc.stdout, tool_name, timeout=10)
    if not resp3["ok"]:
        print(f"  !! {tool_name} FAILED: {resp3['error']}")
        stderr_thread.join(timeout=2)
        print(f"  !! stderr:")
        for line in stderr_lines:
            print(f"       {line}")
    else:
        print(f"  << {tool_name} OK")
        content = resp3["data"].get("result", {}).get("content", [])
        for c in content:
            print(f"     Response: {c.get('text', '')}")

    # Cleanup
    proc.terminate()
    proc.wait(timeout=5)
    stderr_thread.join(timeout=2)
    if stderr_lines:
        print(f"\n  [stderr output]:")
        for line in stderr_lines:
            print(f"    {line}")
    print(f"\n  Exit code: {proc.returncode}")
    print(f"  === RESULT: {'ALL PASS' if resp3.get('ok') else 'FAILED'} ===")


if __name__ == "__main__":
    test_server("hello (CONTROL GROUP)", r"D:\Agent_Hub\tools\hello_mcp.py")
    test_server("literature-gatekeeper (TEST)", r"D:\Agent_Hub\mcp\literature_gate_mcp.py")
    test_server("draft-quality-gatekeeper (TEST)", r"D:\Agent_Hub\mcp\draft_quality_gate_mcp.py")
    print("\n\n=== DIFFERENTIAL DIAGNOSIS COMPLETE ===")
