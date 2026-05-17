"""Fix encoding + replace paths in N6 plan files."""
import pathlib

OLD = "d:\\\\hermes-agent"  # escaped backslash as in markdown
NEW = "D:\\\\Agent_Hub\\\\agents\\\\Mem_Agent"

for name in [
    "2026-05-16-n6-memory-broker.md",
    "2026-05-16-n6-memory-broker-zh.md",
]:
    p = pathlib.Path(r"d:\hermes-agent\docs\superpowers\plans") / name
    
    # Try multiple encodings
    text = None
    for enc in ["utf-8", "utf-8-sig", "utf-16", "utf-16-le", "cp950", "latin-1"]:
        try:
            text = p.read_text(encoding=enc)
            print(f"{name}: read with {enc}")
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    if text is None:
        print(f"{name}: FAILED to read with any encoding")
        continue
    
    count = text.count(OLD)
    print(f"  Found {count} occurrences of escaped path")
    
    # Also check unescaped
    old_unesc = "d:\\hermes-agent"
    count2 = text.count(old_unesc)
    print(f"  Found {count2} occurrences of unescaped path")
    
    if count > 0:
        text = text.replace(OLD, NEW)
    if count2 > 0:
        new_unesc = "D:\\Agent_Hub\\agents\\Mem_Agent"
        text = text.replace(old_unesc, new_unesc)
    
    p.write_text(text, encoding="utf-8")
    
    # Verify
    text2 = p.read_text(encoding="utf-8")
    r1 = text2.count(OLD)
    r2 = text2.count(old_unesc)
    n1 = text2.count("Mem_Agent")
    print(f"  After: {r1} escaped old, {r2} unescaped old, {n1} Mem_Agent refs")
