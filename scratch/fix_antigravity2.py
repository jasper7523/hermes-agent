import sqlite3
import shutil
import os
import subprocess
import time
import sys

print("=" * 60)
print("  Antigravity 2 對話歷史修復腳本")
print("=" * 60)

old_db = r"C:\Users\promy\AppData\Roaming\Antigravity\User\globalStorage\state.vscdb"
backup_db = r"C:\Users\promy\AppData\Roaming\Antigravity\User\globalStorage\state.vscdb.pre_fix_backup"

# Step 0: Check if Antigravity 2 is running
print("\n[Step 0] 檢查 Antigravity 2 是否在執行...")
result = subprocess.run(
    ["powershell", "-Command", "Get-Process 'Antigravity' -ErrorAction SilentlyContinue | Select-Object -First 1"],
    capture_output=True, text=True
)
if "Antigravity" in result.stdout:
    print("  ⚠️  Antigravity 2 仍在執行！正在關閉...")
    subprocess.run(
        ["powershell", "-Command", "Get-Process 'Antigravity' | Stop-Process -Force"],
        capture_output=True
    )
    time.sleep(3)
    print("  ✅ 已關閉 Antigravity 2")
else:
    print("  ✅ Antigravity 2 未在執行")

# Step 1: Backup
print("\n[Step 1] 備份 state.vscdb...")
if not os.path.exists(backup_db):
    shutil.copy2(old_db, backup_db)
    print(f"  ✅ 已備份至: {backup_db}")
else:
    print(f"  ℹ️  備份已存在，跳過")

# Step 2: Check if trajectorySummaries already exists
print("\n[Step 2] 檢查 trajectorySummaries...")
conn = sqlite3.connect(old_db)
c = conn.cursor()
c.execute("SELECT length(value) FROM ItemTable WHERE key='antigravityUnifiedStateSync.trajectorySummaries'")
row = c.fetchone()

if row:
    print(f"  ✅ trajectorySummaries 已存在 ({row[0]} bytes)")
    print("  ℹ️  state.vscdb 中已有對話索引，無需注入")
else:
    print("  ⚠️  trajectorySummaries 不存在！嘗試從 Antigravity IDE 複製...")
    ide_db = r"C:\Users\promy\AppData\Roaming\Antigravity IDE\User\globalStorage\state.vscdb"
    if os.path.exists(ide_db):
        ide_conn = sqlite3.connect(ide_db)
        ide_c = ide_conn.cursor()
        ide_c.execute("SELECT value FROM ItemTable WHERE key='antigravityUnifiedStateSync.trajectorySummaries'")
        ide_row = ide_c.fetchone()
        if ide_row:
            c.execute("INSERT OR REPLACE INTO ItemTable (key, value) VALUES (?, ?)",
                      ("antigravityUnifiedStateSync.trajectorySummaries", ide_row[0]))
            conn.commit()
            print(f"  ✅ 已從 IDE 注入 trajectorySummaries ({len(ide_row[0])} bytes)")
        ide_conn.close()

# Step 3: Also copy agyhub_summaries_proto.pb from IDE
print("\n[Step 3] 複製 agyhub_summaries_proto.pb 索引...")
src_pb = r"C:\Users\promy\.gemini\antigravity-ide\agyhub_summaries_proto.pb"
dst_pb = r"C:\Users\promy\.gemini\antigravity\agyhub_summaries_proto.pb"
dst_pb_bak = r"C:\Users\promy\.gemini\antigravity\agyhub_summaries_proto.pb.bak"

if os.path.exists(src_pb):
    src_size = os.path.getsize(src_pb)
    dst_size = os.path.getsize(dst_pb) if os.path.exists(dst_pb) else 0
    
    if src_size > dst_size:
        # Backup current
        if os.path.exists(dst_pb):
            shutil.copy2(dst_pb, dst_pb_bak)
        # Copy from IDE
        shutil.copy2(src_pb, dst_pb)
        print(f"  ✅ 已複製 ({src_size} bytes 覆蓋 {dst_size} bytes)")
    else:
        print(f"  ℹ️  目標已較大或相同 (src={src_size}, dst={dst_size})，跳過")
else:
    print(f"  ⚠️  來源不存在: {src_pb}")

conn.close()

print("\n" + "=" * 60)
print("  ✅ 修復完成！請重新啟動 Antigravity 2")
print("=" * 60)
input("\n按 Enter 關閉此視窗...")
