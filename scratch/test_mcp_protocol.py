import subprocess
import json
import time

def test_mcp():
    cmd = [r"D:\hermes-agent\venv\Scripts\python.exe", r"d:\Agent_Hub\tools\hello_mcp.py"]
    print(f"Executing: {' '.join(cmd)}")
    
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        bufsize=0
    )
    
    # 1. Handshake: list_tools
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    print("Sending list_tools request...")
    proc.stdin.write(json.dumps(req) + "\n")
    proc.stdin.flush()
    
    time.sleep(1)
    
    # Read response
    line = proc.stdout.readline()
    print(f"Received: {line}")
    
    if not line:
        print("ERROR: No response from MCP server. Check stderr.")
        print(f"STDERR: {proc.stderr.read()}")
        return

    # 2. Call tool
    call_req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "say_hello",
            "arguments": {"text": "Integration Test"}
        }
    }
    print("Sending call_tool request...")
    proc.stdin.write(json.dumps(call_req) + "\n")
    proc.stdin.flush()
    
    time.sleep(1)
    line = proc.stdout.readline()
    print(f"Received: {line}")
    
    proc.terminate()

if __name__ == "__main__":
    test_mcp()
