import json
from pathlib import Path

def main():
    config_path = Path(r"C:\Users\promy\.gemini\config\mcp_config.json")
    if not config_path.exists():
        print(f"ERROR: Configuration file not found at {config_path}")
        return

    print(f"Reading configuration from {config_path}...")
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    modified = False

    for name, srv in data.get("mcpServers", {}).items():
        command = srv.get("command", "")
        # 如果是 python.exe 啟動的 MCP 伺服器
        if "python.exe" in command.lower():
            args = srv.get("args", [])
            new_args = list(args)
            
            # 確保有 "-u" 參數且位於腳本前面
            # 確保有 "-X" "utf8" 參數且位於最前面
            # 移除已有的 "-X", "utf8", "-u" 以免重複或順序錯誤
            temp_args = []
            script_path = None
            
            # 簡單解析：找出第一個不是以 '-' 開頭的參數，這通常是 Python 腳本路徑
            script_idx = -1
            for i, arg in enumerate(args):
                if not arg.startswith("-"):
                    script_idx = i
                    break
            
            if script_idx != -1:
                script_path = args[script_idx]
                other_args = args[script_idx+1:]
                
                # 重新組合：["-X", "utf8", "-u", script_path, ...其他參數]
                srv["args"] = ["-X", "utf8", "-u", script_path] + other_args
                
                if srv["args"] != args:
                    print(f"Patching args for {name}:")
                    print(f"  Old: {args}")
                    print(f"  New: {srv['args']}")
                    modified = True
            else:
                # 如果沒有找到腳本路徑（可能只是模組執行之類的），就直接把 -X utf8 -u 加在最前面
                # 但需要防重複
                if "-X" not in new_args:
                    new_args = ["-X", "utf8"] + new_args
                if "-u" not in new_args:
                    # 插入在 -X utf8 之後
                    idx = new_args.index("utf8") + 1 if "utf8" in new_args else 0
                    new_args.insert(idx, "-u")
                
                if new_args != args:
                    srv["args"] = new_args
                    print(f"Patching args for {name} (no script fallback):")
                    print(f"  Old: {args}")
                    print(f"  New: {srv['args']}")
                    modified = True

    if modified:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("SUCCESS: Config updated with UTF-8 and Unbuffered flags.")
    else:
        print("NO_CHANGE: All Python MCP configurations are already patched.")

if __name__ == "__main__":
    main()
