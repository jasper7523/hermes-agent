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

    # 修改 draft-quality-gatekeeper 的 args
    if "draft-quality-gatekeeper" in data.get("mcpServers", {}):
        srv = data["mcpServers"]["draft-quality-gatekeeper"]
        args = srv.get("args", [])
        if args and args[0] != "-u":
            srv["args"] = ["-u"] + args
            print("Patched draft-quality-gatekeeper args with '-u'")
            modified = True
        else:
            print("draft-quality-gatekeeper already patched or empty args")
    else:
        print("draft-quality-gatekeeper not found in mcpServers")

    # 修改 literature-gatekeeper 的 args
    if "literature-gatekeeper" in data.get("mcpServers", {}):
        srv = data["mcpServers"]["literature-gatekeeper"]
        args = srv.get("args", [])
        if args and args[0] != "-u":
            srv["args"] = ["-u"] + args
            print("Patched literature-gatekeeper args with '-u'")
            modified = True
        else:
            print("literature-gatekeeper already patched or empty args")
    else:
        print("literature-gatekeeper not found in mcpServers")

    if modified:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("SUCCESS: Config updated.")
    else:
        print("NO_CHANGE: Configuration is already up to date.")

if __name__ == "__main__":
    main()
