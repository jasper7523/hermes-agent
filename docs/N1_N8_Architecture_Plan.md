# 賈斯伯戰略中樞 (Jasper Strategic Hub) 
## N1-N8 拓樸架構與建軍實作計畫 (Implementation Plan)

本文件定義了 AI Agent Hub 的最高戰略拓樸 (Topology N1-N8)，確立了「總部調度、專業分工、背景常駐」的三維立體作戰網路，並落實 **MSWA (Monorepo Sub-Workspace Architecture)** 與 **四區沙箱隔離協定**。

---

## 🗺️ N1-N8 全域拓樸架構圖 (Topology Architecture)

```mermaid
graph TD
    User([指揮官 / User]) --> N1
    
    subgraph "總部與調度中心 (Hub & Dispatch)"
        N1[N1: 總部中樞 Hub Coordinator<br/>(意圖解析 / 全域路由分發)]
    end
    
    subgraph "背景常駐守護 (Background Daemons)"
        N6[N6: Mem_Agent<br/>(Zettelkasten / Event Sourcing)]
        N7[N7: Hermes_Agent<br/>(架構守護 / 自癒容錯分析)]
    end
    
    subgraph "專業前線部隊 (Specialized Agents)"
        N2[N2: Legal_Research_Agent<br/>(法務專職 / Analyzer, Comparator, Grader)]
        N3[N3: Software_Engineer_Agent<br/>(基建與除錯 / 系統重構)]
        N4[N4: Creative_Writer_Agent<br/>(行銷與社群文案)]
        N5[N5: Book_Writer_Agent<br/>(專書學術撰寫 / 實務指引)]
        N8[N8: Academic_Oracle_Agent<br/>(學術論文專家 / Consensus MCP)]
    end
    
    N1 -->|法理檢索與分析| N2
    N1 -->|基建部署與修復| N3
    N1 -->|行銷文案生成| N4
    N1 -->|專書寫作與修訂| N5
    N1 -->|學術探勘與論文| N8
    
    %% 背景守護連線
    N1 -.->|調度歷史寫入| N6
    N1 -.->|錯誤回報與容錯| N7
    
    %% 橫向協同
    N5 -.->|學術管線底層呼叫| N8
    N2 -.->|提供法源依據| N5
```

---

## 🛡️ 各防區戰略定位與建軍狀態

### 1. 總部與調度層
*   **N1 (Hub Coordinator)**：最高戰略中樞。負責與指揮官對接，理解意圖後將任務動態路由給對應的子代理人。**嚴守 Zero-Trust 隔離**，無法直接窺探子代理人的沙箱。

### 2. 專業作戰節點 (已實體化或建軍中)
*   **N5 (Book_Writer_Agent)**：【建軍完成】
    *   **職責**：《企業法遵與危機管理實務指引》專書撰寫。
    *   **裝備**：`academic-book-writer`、Consensus MCP、`patch_draft.py` (RCA-0416 防護)。
*   **N8 (Academic_Oracle_Agent)**：【建軍中】
    *   **職責**：SSCI 學術論文撰寫、海量文獻探勘。
    *   **裝備**：12-agent `academic-paper` 管線、Consensus MCP。
*   **N2 (Legal_Research_Agent)**：【待命建軍】
    *   **職責**：法務研究與判例爬梳。下轄 `Analyzer` (分析)、`Comparator` (比對)、`Grader` (評分) 三支微型部隊。
*   **N3 (Software_Engineer_Agent)**：【待命建軍】
    *   **職責**：底層架構除錯、GSD 管線開發。
*   **N4 (Creative_Writer_Agent)**：【待命建軍】
    *   **職責**：短平快的社群媒體、行銷文案撰寫。

### 3. 背景常駐守護 (Daemons)
*   **N6 (Mem_Agent)**：
    *   **職責**：負責 Zettelkasten 長期記憶圖譜構建與每一回合的 Event Sourcing 紀錄。確保系統不會「失憶」。
*   **N7 (Hermes_Agent)**：
    *   **職責**：Watchdog 系統。當 N3 或其他代理人發生崩潰時，負責進行自癒 (Self-healing) 與架構容錯分析。

---

## ⚙️ 核心實作守則 (The 6 Cognitive Frameworks)
任何新防區的建立，必須嚴格遵守以下紀律：
1. **零幻覺與情報窮盡鐵律**：無實證數據絕對不准生成，查無證據一律回報 `STATUS_INSUFFICIENT_INFO`。
2. **四區沙箱隔離**：所有免洗腳本僅限 `.tmp/`，代理人間的資料交換必須透過 N1 路由，嚴禁跨目錄越權讀寫。
3. **EVIDENCE-FIRST 實證鐵律**：程式碼交付前必須在沙箱內獲得 Positive Validation。
4. **降落備忘錄 (Post-flight Hook)**：每當修復一個 Issue，必須寫入 `.agent_memory/auto_memory/0xx_issue.md`。
