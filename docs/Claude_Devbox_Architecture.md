# Persistent AI Devbox 架構圖 (Zero-Trust Airlock)

以下是我們為 Claude Code 量身打造的零信任常駐型沙箱架構。

```mermaid
graph TD
    subgraph Host_OS ["💻 Host OS (指揮官本機 / Windows)"]
        User["👨‍💻 指揮官 / N1-N8 代理"]
        Src["📁 專案原始碼<br/>(D:\\hermes-agent)"]
        Airlock["🛡️ 提領閘門<br/>(airlock_transfer.ps1)"]
        Auditor["🔍 白箱稽核 & 掃描器<br/>(whitebox_auditor / egress_scanner)"]
        Safe["✅ 安全輸出區<br/>(D:\\Claude_Output_Safe)"]
    end

    subgraph Docker_Devbox ["🐳 常駐隔離艙 (Docker Container)"]
        Claude["🤖 Claude Code CLI"]
        GitShadow["👁️ Git Shadowing<br/>(inotify 變更側錄)"]
        
        subgraph Mounts ["隔離區掛載點 (Volume Mounts)"]
            Shadow["🪞 影子工作區 (Read-Only)<br/>/workspace/hermes-agent"]
            Quarantine["🏥 檢疫寫入區 (Read/Write)<br/>/workspace/quarantine"]
            AuditLogs["📜 操作日誌區 (Write-Only)<br/>/workspace/audit_logs"]
        end
    end

    %% 指揮與環境配置
    User -- "1. 投射指令 (docker exec)" --> Claude
    Src -. "2. 絕對防寫掛載" .-> Shadow
    
    %% 沙箱內行為
    Claude -- "3. 讀取專案上下文" --> Shadow
    Claude -- "4. 產出代碼/修改" --> Quarantine
    Claude -- "5. 背景原生 Log 側錄" --> AuditLogs
    
    %% 背景監視機制
    Quarantine -- "6. 檔案異動" --> GitShadow
    GitShadow -- "自動 Commit 生成摘要" --> Quarantine
    
    %% 出關提領機制
    User -- "7. 啟動出關審查" --> Airlock
    Airlock -- "呼叫分析" --> Auditor
    Auditor -- "比對越權紀錄" --> AuditLogs
    Airlock -- "8. 針對產出進行惡意掃描" --> Quarantine
    Airlock -- "9. 綠燈放行，搬移檔案" --> Safe

    %% 樣式設定
    classDef secure fill:#e8f4f8,stroke:#2b6cb0,stroke-width:2px;
    classDef danger fill:#fed7d7,stroke:#c53030,stroke-width:2px;
    classDef highlight fill:#fefcbf,stroke:#b7791f,stroke-width:2px;
    
    class Docker_Devbox secure;
    class Quarantine danger;
    class AuditLogs highlight;
```

## 📐 架構運作五大階段 (The 5 Phases)

1. **指令投射 (Command Projection)**：指揮官或 Agent 不在主機上直接執行 AI，而是透過 Docker API 隔空把指令投射進去。
2. **視野受限 (View Restriction)**：AI 能看見 `hermes-agent` 的所有代碼，但那是單向玻璃 (Read-Only)。
3. **活動監視 (Activity Surveillance)**：AI 在裡面的每一次交談、每一個 Bash 指令，都會即時寫入 `AuditLogs`。同時，只要 `Quarantine` 裡面多了一個檔案，`GitShadow` 就會在 2 秒內自動把它 Commit 起來。
4. **越權阻斷 (Unauthorized Blocking)**：如果 AI 在對話中企圖修改 `hermes-agent` (即使被系統擋下)，`whitebox_auditor` 在出關時依然會抓到這條犯罪未遂的 Log，並直接沒收它的所有產出。
5. **氣閘提領 (Airlock Egress)**：經過防毒掃描與日誌清查後，只有乾淨的產出會被搬移到安全區 (`Claude_Output_Safe`)，等待指揮官人工合併。
