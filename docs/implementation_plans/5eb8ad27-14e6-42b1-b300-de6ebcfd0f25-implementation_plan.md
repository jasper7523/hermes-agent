# N7 Watchdog Infrastructure Parse & Blueprint: Multi-Agent Dispatcher

這份草稿由 N7 背景監控程序產出，旨在實作【多重代理路由派發器】(YAML Parser & Router Dispatcher)。

## 🚨 User Review Required (Code Review)

指揮官，以下是我依據 `task-groups.yaml` 所產生的 Python 實作草稿。此程式碼具有高度的防禦性 (`try-catch`) 與完整的系統級 Logging 追蹤。這是一份「修補草稿」，**我無權直接寫入核心代碼**，請您進行 Code Review。若您批准，我將請 N1 發包給 N3 執行實體修改。

## Proposed Changes

我們預計將以下邏輯寫入 `src/core/router_dispatcher.py` 或是現有的 `adk_engine.py` 之中。

### [NEW] `router_dispatcher.py`

此模組實作了兩個主要核心：
1. **`TopologyManager`**: 負責載入 `task-groups.yaml`，若檔案遺失或格式錯誤會捕捉並發出 Critical Log 阻斷執行。
2. **`HermesDispatcher`**: 接收意圖字串，透過關鍵字進行推演。未來可輕易替換為呼叫 LLM API 進行 Classifier 的版本。

```python
import os
import yaml
import logging
from typing import Dict, Any, Optional

# N7 鐵律：完善的 Error Logging 追蹤
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - [Hub-Router] - %(levelname)s - %(message)s'
)

class TopologyManager:
    """負責讀取與解析多重代理人的 YAML 拓樸配置"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.topology: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """載入 task-groups.yaml，具備 N7 嚴格防禦性編程把關"""
        if not os.path.exists(self.config_path):
            logging.error(f"FATAL: 代理拓樸設定檔未找到：{self.config_path}")
            raise FileNotFoundError(f"Missing Topology Database at {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                # 重新塑印字典，以 ID 作為主鍵，例如 'N2': {name: 'Legal_Research_Agent'...}
                self.topology = {group['id']: group for group in data.get('task_groups', [])}
            
            logging.info(f"系統拓樸成功載入。共計掛載 {len(self.topology)} 個特種 Agent。")
        except yaml.YAMLError as e:
            # 針對 YAML 格式損毀的攔截
            logging.critical(f"YAML 語法損毀解析失敗 {self.config_path}: {e}")
            raise
        except Exception as e:
            # 最後一道防線捕捉未知錯誤
            logging.critical(f"拓樸檔載入發生預期外之致命錯誤: {e}")
            raise

class HermesDispatcher:
    """全域路由分發器 (Router)：解析意圖並呼叫對應 Agent"""
    
    def __init__(self, topology_manager: TopologyManager):
        self.topo = topology_manager

    def dispatch(self, user_intent: str) -> Optional[Dict[str, Any]]:
        """
        傳入使用者提示詞或意圖，回傳對應的 Agent 拓樸資料。
        TODO: 第一階段採用 Heuristics (關鍵字探索)，第二階段應升級為呼叫 Llama/Gemini 分類器。
        """
        intent_lower = user_intent.lower()
        
        try:
            agent_id = self._analyze_intent(intent_lower)
            
            if not agent_id:
                logging.warning(f"路由迷失 (Routing Failure): 無法指派明確 Agent => {user_intent[:20]}...")
                return None  # 觸發退場策略，交還 N1 前台作全域處理
            
            target_agent = self.topo.topology.get(agent_id)
            if not target_agent:
                logging.error(f"路由派發錯亂：解析器請求了 {agent_id}，但未見於目前的 task-groups.yaml 中！")
                return None
                
            logging.info(
                f"【路由成功】任務分派給 => [{agent_id}] {target_agent['name']} \n"
                f"掛載武裝 (Skills): {', '.join(target_agent.get('skills', []))}"
            )
            return target_agent
            
        except Exception as e:
             logging.error(f"分發系統運算崩潰 (Dispatch Crash): {e}")
             return None

    def _analyze_intent(self, intent: str) -> Optional[str]:
        """這是一段暫代 (Mock) 判斷式，供 N3 進行擴展實作"""
        # [N2]: Legal_Research_Agent (法務專職)
        if any(k in intent for k in ['法', '合規', '爬蟲', '查資料', 'lawsnote', '找文獻', '判決']):
            return 'N2'
            
        # [N3]: Software_Engineer_Agent (基礎架構工程師)
        elif any(k in intent for k in ['錯誤', 'bug', '報錯', '修復', '代碼', '環境', '異常', '改 Code']):
            return 'N3'
            
        # [N5]: Book_Writer_Agent (專書學術撰寫)
        elif any(k in intent for k in ['寫文章', '編排', '專書', '書', '出書', '撰寫', '章節']):
            return 'N5'
            
        # [N4]: Creative_Writer_Agent (行銷與社群文案)
        elif any(k in intent for k in ['行銷', '社群', '發文', '公報', '海報']):
            return 'N4'
            
        return None

# ----- 執行案例 (Mock Usage) -----
if __name__ == "__main__":
    try:
        # 指向我們剛才閱讀到的 config 路徑
        topo_path = r"C:\Users\promy\.gemini\antigravity\task-groups.yaml"
        manager = TopologyManager(topo_path)
        router = HermesDispatcher(manager)
        
        # 模擬任務
        print("\n--- 模擬意圖測試 ---")
        router.dispatch("幫我分析一下剛抓下來的 Lawsnote PDF 法規，看看是否合規。")
        router.dispatch("這段 Python 腳本會噴 OOM error，幫我看一下哪裡有 bug？")
        router.dispatch("第二章第三節的內容架構我不太滿意，重寫這一份。")
        router.dispatch("今天中午吃什麼？")
        
    except Exception as main_e:
        logging.critical(f"Watchdog 偵測到主程序崩潰: {main_e}")
```

## Open Questions

1. **依賴套件**: 確認 `d:\hermes-agent` 的 venv 是否已經安裝了 `PyYAML`。如果沒有，工單將需要指示 N3 執行 `pip install pyyaml`。
2. **與主程式掛載點**: 此模組預計存放在哪裡？是獨立的 `router_dispatcher.py` 還是併入 `adk_engine.py`？
3. **退場機制**: 當 `dispatch` 無法匹配的時候，目前設定回傳 `None`，是應該由 N1 接管還是印出報錯要求使用者重新敘述？

## Verification Plan

### Automated Tests
1. **本機直通測試**:
   我會在沙箱中，直接運行此份草稿，驗證 `print` 出來的 Routing ID 是否精準匹配 N2、N3 與 N5。
2. **斷言測試**:
   測試給定一個錯誤的 YAML 路徑，看 N7 Watchdog 預期內的 `FileNotFoundError` 大防禦網是否確實攔截。
