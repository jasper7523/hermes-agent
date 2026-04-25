import os
import sys
import time
import json
import asyncio
import subprocess
from pathlib import Path

# Try to import watchdog and google.genai
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    from google import genai
    from google.genai import types
except ImportError:
    print("請先安裝依賴：pip install watchdog google-genai")
    sys.exit(1)

# Configurations
AGENT_HUB_DIR = Path(r"d:\Agent_Hub")
AUTO_MEMORY_DIR = AGENT_HUB_DIR / ".agent_memory" / "auto_memory"
COUNCIL_RECORDS_DIR = AGENT_HUB_DIR / ".agent_memory" / "council_records"

# Load Gemini API Key (Attempt to read from config or env)
sys.path.append(str(AGENT_HUB_DIR))
try:
    from config.settings import settings
    GEMINI_API_KEY = settings.GEMINI_API_KEY
except:
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

if not GEMINI_API_KEY:
    print("無法取得 GEMINI_API_KEY。請設定環境變數或確保 config/settings.py 正確配置。")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

def show_toast(title, message):
    """Shows a Windows Toast Notification using PowerShell"""
    ps_script = f"""
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    $template = [Windows.UI.Notifications.ToastTemplateType]::ToastText02
    $xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent($template)
    $xml.GetElementsByTagName("text")[0].AppendChild($xml.CreateTextNode("{title}")) | Out-Null
    $xml.GetElementsByTagName("text")[1].AppendChild($xml.CreateTextNode("{message}")) | Out-Null
    $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("AgentHub").Show($toast)
    """
    subprocess.run(["powershell", "-Command", ps_script], capture_output=True)

async def get_agent_opinion(agent_name, role_prompt, issue_content):
    print(f"[{agent_name}] 正在進行平行審查...")
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"【提案內容】\n{issue_content}\n\n請根據你的角色給出技術審查意見 (同意/不同意，及理由)。",
            config=types.GenerateContentConfig(
                system_instruction=role_prompt,
                temperature=0.2,
            )
        )
        return f"=== {agent_name} 審查意見 ===\n{response.text}\n"
    except Exception as e:
        return f"=== {agent_name} 審查失敗 ===\n{str(e)}\n"

async def process_council_proposal(file_path):
    print(f"\n⚡ 偵測到新提案：{file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"讀取檔案失敗：{e}")
        return

    # 定義 Agent 身分
    n5_prompt = "你是 N5 (Book Writer Agent)。你的目標是最大化寫作產出效率，排除一切阻礙進度的技術或流程問題。偏好能快速解決問題的彈性方案 (GSD精神)。對於任何會阻礙你交付作品的基礎設施限制，你傾向於繞過或找尋替代方案。"
    n7_prompt = "你是 N7 (Hermes Watchdog Agent)。你的目標是守護系統基礎設施、沙箱隔離與架構整潔。你極度厭惡技術債與破壞系統核心的越權行為。偏好防禦性編程與正規修復。任何私自寫入系統底層或繞過標準流程的行為都必須被導正。"
    n8_prompt = "你是 N8 (Academic Oracle Agent)。你的目標是確保資料溯源的精準度與完整性。偏好能保留完整 URL 與 metadata 的無損檢索方案。如果某個腳本有助於抓取完整且精確的參考文獻，你會支持。"
    n1_prompt = "你是 N1 (Agent Hub Coordinator)。身為最高指揮官的代理人與評議會主席，你需要綜合考量 N5、N7、N8 的意見。你必須堅守『修復基建優先法則』，但也要給予適度的實戰彈性。請給出明確的『最終裁決 (Final Ruling)』(同意提案/否決提案/修改後同意) 並解釋原因。你的回答應該要具備高階主管的果斷與威嚴。"

    # 平行審查
    print("啟動 N5, N7, N8 平行審查...")
    results = await asyncio.gather(
        get_agent_opinion("N5", n5_prompt, content),
        get_agent_opinion("N7", n7_prompt, content),
        get_agent_opinion("N8", n8_prompt, content)
    )
    
    combined_reviews = "\n".join(results)
    print("平行審查完成，提交主席 N1 裁決...")

    # N1 主席裁決
    try:
        n1_response = client.models.generate_content(
            model='gemini-2.5-pro', # N1 uses pro for better reasoning
            contents=f"【原始提案】\n{content}\n\n【合議庭審查結果】\n{combined_reviews}\n\n請根據合議庭結果給出主席最終裁決。",
            config=types.GenerateContentConfig(
                system_instruction=n1_prompt,
                temperature=0.2,
            )
        )
        final_ruling = n1_response.text
    except Exception as e:
        print(f"N1 裁決失敗：{e}")
        return

    # 生成稽核紀錄
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    record_filename = f"{timestamp}_N1_Ruling.md"
    record_path = COUNCIL_RECORDS_DIR / record_filename
    
    full_report = f"# Agent Council Arbitration Record\n\n## 1. Original Proposal\n\n{content}\n\n## 2. Council Reviews\n\n{combined_reviews}\n\n## 3. Chairman (N1) Final Ruling\n\n{final_ruling}\n"
    
    with open(record_path, "w", encoding="utf-8") as f:
        f.write(full_report)
    
    print(f"✅ 裁決已寫入：{record_path}")
    
    # 彈出通知
    show_toast("Agent 評議會", f"N1 已完成裁決！紀錄：{record_filename}")
    
    # 刪除或搬移原始提案檔 (避免重複觸發)
    archive_dir = AUTO_MEMORY_DIR / "archive"
    archive_dir.mkdir(exist_ok=True)
    os.rename(file_path, archive_dir / Path(file_path).name)

class CouncilHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and "[COUNCIL_PROPOSAL]" in os.path.basename(event.src_path):
            # 延遲避免檔案未寫入完成
            time.sleep(1.5)
            asyncio.run(process_council_proposal(event.src_path))

def main():
    print(f"==================================================")
    print(f" 🛡️ Ouroboros Event Bus (Agent Council) 啟動中...")
    print(f" 📂 監聽目錄：{AUTO_MEMORY_DIR}")
    print(f"==================================================")
    
    # Ensure dirs exist
    AUTO_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    COUNCIL_RECORDS_DIR.mkdir(parents=True, exist_ok=True)
    
    event_handler = CouncilHandler()
    observer = Observer()
    observer.schedule(event_handler, str(AUTO_MEMORY_DIR), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
