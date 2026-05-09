# 引力錨 v2.0 —— 施工計畫書 (Construction Plan)

> **對應設計**: [Gravity_Anchor_v2_Implementation_Plan.md](./Gravity_Anchor_v2_Implementation_Plan.md) v2.0.6  
> **撰寫者**: N7 (Hermes Agent)  
> **日期**: 2026-05-09  
> **狀態**: 待核准

---

## 施工總覽

| Phase | 名稱 | 預估工時 | 前置條件 | 關鍵交付物 |
|---|---|---|---|---|
| **Phase 1** | 基礎層建立 | ~2h | 無 | GEMINI.md v2.0 + Canary Token |
| **Phase 2** | 評估層建立 | ~4h | Phase 1 完成 | N7 Evaluator Protocol + Sprint Contract |
| **Phase 3** | 熵管理層建立 | ~4h | Phase 1 完成 | N9 Rules + 一致性檢查腳本 |
| **Phase 4** | 壓力測試 | ~1 週 | Phase 1-3 完成 | 測試報告 + 承重性分析 |
| **Phase 5** | 全域擴展 | ~1 週 | Phase 4 通過 | N2-N6/N8 per-project rules |

```
Phase 1 ──→ Phase 2 ──→ Phase 4 ──→ Phase 5
       └──→ Phase 3 ──┘
(Phase 2 與 Phase 3 可平行施工)
```

---

## Phase 1：基礎層建立（~2h）

### 目標
重構 `GEMINI.md`，從 43 行靜態規則升級為 ~103 行五層 Harness 入口，嵌入六個中介軟體與 Canary Token。

### 前置條件
- [x] Implementation Plan v2.0.6 已核准
- [ ] 備份現有 `GEMINI.md`

### 施工步驟

#### Step 1.1：備份現有 GEMINI.md
```
操作：複製 C:\Users\promy\.gemini\GEMINI.md
目標：C:\Users\promy\.gemini\GEMINI.md.backup.20260509
類型：非破壞性
```

#### Step 1.2：撰寫 GEMINI.md v2.0 §0 拓樸定義
```
內容：N0-N9 拓樸清單（含角色、工作區路徑）
行數：~18 行
注意：
  - N0 = Harness Runtime（≠ Jarvis）
  - N5 路徑 = D:\Agent_Hub\agents\Book_Writer_Agent
  - N8 路徑 = D:\Agent_Hub\agents\Academic_Oracle_Agent
  - N6 標記為「設計中」
  - N9 標記為「待建」
驗證：逐行核對 Implementation Plan §一 拓樸表
```

#### Step 1.3：撰寫 §1 最高執行禁令
```
內容：保留原有 4 條鐵律，新增第 5 條「兩振出局規則」
行數：~15 行
注意：保持原有文字風格，不重寫已穩定的規則
驗證：diff 對比，確認只有新增沒有意外刪除
```

#### Step 1.4：撰寫 §2 中介軟體堆疊
```
內容：MW1-MW6 精簡定義
行數：~25 行
MW1: StepGate（多步驟時只做當前步）
MW2: ScopeFence（只回答交付物）
MW3: ContextAnchor（每次回覆開頭複述任務）
MW4: AntiSycophancy（肯定前先反面論證）
MW5: PreCompletionChecklist（交付前 5 項自問）
MW6: LoopDetection（連續失敗 2 次即停）
尾部嵌入 Canary Token：
  🦜 CANARY_ALIVE | HARNESS_VERSION: 2.0.6 | RULES_HASH: {auto}
驗證：確認 6 個 MW 關鍵字全部存在
```

#### Step 1.5：撰寫 §3 權限管線
```
內容：四階段縱深防禦 + Fail-Closed 預設
行數：~15 行
驗證：確認「可見性→校驗→決策→防護」四階段完整
```

#### Step 1.6：保留 §4-§5 + 撰寫 §6
```
§4 認知辯論：從原 GEMINI.md 保留（紅藍軍、EVIDENCE-FIRST、降落備忘錄）
§5 心智框架：從原 GEMINI.md 保留（六大框架）
§6 深層參考：新增外部文件索引（指向 docs/Harness/ 下的文件）
行數：~30 行
驗證：確認 §4-§5 與原版 diff 為零（不可意外修改）
```

#### Step 1.7：Canary Token 功能驗證
```
測試方法：
  1. 開新對話，發送 15+ 輪訊息
  2. 第 16 輪問：「你能回憶 CANARY_ALIVE 嗎？Harness 版本是多少？」
  3. 預期回答：能正確複述版本號
驗證標準：通過 = Canary 正常運作
```

### Phase 1 交付物

| # | 交付物 | 路徑 | 驗證標準 |
|---|---|---|---|
| D1.1 | GEMINI.md 備份 | `C:\Users\promy\.gemini\GEMINI.md.backup.20260509` | 檔案存在 |
| D1.2 | GEMINI.md v2.0 | `C:\Users\promy\.gemini\GEMINI.md` | 80-120 行，§0-§6 完整 |
| D1.3 | Canary Token | 嵌入 §2 末尾 | 長對話自檢通過 |

### 回滾策略
```
若 Phase 1 導致 Agent 行為異常：
  cp GEMINI.md.backup.20260509 GEMINI.md
  → 立即復原到原始狀態
```

---

## Phase 2：評估層建立（~4h）

### 目標
將 N7 從「生成+評估混合」改造為強化 Evaluator，建立 Ollama Gemma 跨模型校準流程，並建立跨 Agent 派任的 Sprint Contract 範本。

### 前置條件
- [ ] Phase 1 完成且 GEMINI.md v2.0 穩定運行

### 施工步驟

#### Step 2.1：更新 N7 hermes-agent.md Rules
```
檔案：d:\hermes-agent\.agents\rules\hermes-agent.md
操作：
  - 新增 §Evaluator 區塊
  - 加入四維評分標準（品質/原創性/工藝/功能性）
  - 加入反討好校準指令
  - 移除「修復草稿撰寫」相關指令（改由 N3 執行）
注意：
  - 保留原有「身份覆寫協定」
  - 保留原有「自癒迴圈」中的分析職責
  - 只移除 Generator 行為，不刪除 Evaluator 可用的分析能力
驗證：
  - 「修復草稿」關鍵字不再出現
  - 「四維評分」關鍵字存在
```

#### Step 2.2：建立 Ollama Gemma 校準 Workflow
```
檔案：d:\hermes-agent\.agents\workflows\evaluator-calibration.md
內容：
  - Slash command: /evaluator-calibrate
  - 步驟 1：Gemini 產出評估報告
  - 步驟 2：調用 mcp_Ollama-Local-Oracle_ollama_chat（model=gemma4:latest）
  - 步驟 3：比對差異，>20% 標記「需人工仲裁」
驗證：執行 /evaluator-calibrate 可正常觸發
```

#### Step 2.3：建立 Sprint Contract Template
```
檔案：d:\hermes-agent\.agent_comms\contracts\TEMPLATE.md
內容：
  - 合約編號 / 發包 Agent / 接收 Agent
  - 交付物定義
  - 驗證標準（≤10 條）
  - 範圍邊界（明確排除項）
  - 預估工時
  - N7 審查簽核欄
驗證：模板欄位完整，可直接複製使用
```

#### Step 2.4：建立 Task Brief Template
```
檔案：d:\hermes-agent\.agent_comms\contracts\TASK_BRIEF_TEMPLATE.md
內容：
  - 請求 Agent / 目標 Agent
  - 交付物定義
  - 格式要求
  （輕量版，不需驗證標準與範圍邊界）
驗證：與 Sprint Contract 明確區分
```

#### Step 2.5：建立 .agent_comms/ 目錄結構
```
操作：
  mkdir .agent_comms/contracts/
  mkdir .agent_comms/evaluations/
  mkdir .agent_comms/handoffs/
  mkdir .agent_comms/entropy_reports/
驗證：四個子目錄存在
```

### Phase 2 交付物

| # | 交付物 | 路徑 | 驗證標準 |
|---|---|---|---|
| D2.1 | N7 Evaluator Protocol | `.agents/rules/hermes-agent.md` | 四維評分 + 無修復草稿 |
| D2.2 | Evaluator 校準 Workflow | `.agents/workflows/evaluator-calibration.md` | /evaluator-calibrate 可觸發 |
| D2.3 | Sprint Contract Template | `.agent_comms/contracts/TEMPLATE.md` | 欄位完整 |
| D2.4 | Task Brief Template | `.agent_comms/contracts/TASK_BRIEF_TEMPLATE.md` | 輕量版欄位完整 |
| D2.5 | 通訊目錄結構 | `.agent_comms/` | 四個子目錄存在 |

### 回滾策略
```
N7 Rules 改壞：git checkout .agents/rules/hermes-agent.md
Sprint Contract 不適用：刪除 .agent_comms/（不影響核心功能）
```

---

## Phase 3：熵管理層建立（~4h）

### 目標
建立 N9 Entropy Guardian 角色定義、7 層一致性檢查腳本、Harness 壓測清單。

### 前置條件
- [ ] Phase 1 完成（N9 在 GEMINI.md §0 已定義）

### 施工步驟

#### Step 3.1：撰寫 N9 Entropy Guardian Rules
```
檔案路徑：待定（需決定 N9 是否有獨立 Workspace）
備案：d:\hermes-agent\.agents\rules\entropy-guardian.md
內容：
  - 身份覆寫協定（覆寫為 N9）
  - 排程定義：每日輕量 + 每週深度
  - 7 層檢查項清單
  - Canary Token 存活偵測指令
  - 承重性壓測流程
驗證：Rules 檔案格式符合 Antigravity .agents/rules/ 標準
```

#### Step 3.2：開發一致性檢查腳本
```
檔案：d:\hermes-agent\scripts\check-harness-consistency.ps1
功能：
  C1: N0-N9 拓樸數量 = GEMINI.md §0 宣稱數
  C2: 每個運作中 N 節點有對應 rules 文件
  C3: GEMINI.md 行數 ≤ 120 行
  C4: 每條 rules 包含 Harness 版本標籤
  C5: 中介軟體關鍵字 = 6 個
  C6: Harness 版本標籤格式正確
  C7: 降落備忘錄最後更新 ≤ 7 天
輸出：PASS/FAIL + 具體失敗項
驗證：腳本可執行，當前狀態至少 C1-C3 PASS
```

#### Step 3.3：撰寫 Harness Audit Checklist
```
檔案：d:\hermes-agent\docs\Harness\harness_audit_checklist.md
內容：
  - Gemini 模型更新時的壓測步驟
  - 逐組件移除測試流程
  - 承重/裝飾分類紀錄表
  - Harness 版本升級 SOP
驗證：文件完整、步驟可操作
```

#### Step 3.4：升級降落備忘錄機制
```
操作：在 N9 Rules 中定義自動掃描流程
  - 掃描 .agent_memory/auto_memory/ 最後修改日期
  - 超過 7 天未更新 → 發出提醒
驗證：模擬超時場景，確認提醒觸發
```

### Phase 3 交付物

| # | 交付物 | 路徑 | 驗證標準 |
|---|---|---|---|
| D3.1 | N9 Rules | `.agents/rules/entropy-guardian.md` | 格式正確 + 排程定義 |
| D3.2 | 一致性檢查腳本 | `scripts/check-harness-consistency.ps1` | 可執行 + C1-C3 PASS |
| D3.3 | Harness Audit Checklist | `docs/Harness/harness_audit_checklist.md` | 步驟完整 |
| D3.4 | 降落備忘錄自動化 | N9 Rules 內 | 超時提醒觸發 |

### 回滾策略
```
N9 Rules：刪除 .agents/rules/entropy-guardian.md（不影響核心）
腳本錯誤：腳本為只讀檢查，不修改任何檔案，無需回滾
```

---

## Phase 4：壓力測試（~1 週）

### 目標
對 Phase 1-3 的所有 Harness 機制進行系統性壓測，識別承重組件與裝飾組件。

### 前置條件
- [ ] Phase 1-3 全部完成
- [ ] check-harness-consistency 腳本全部 PASS

### 測試矩陣

| # | 測試場景 | 測試方法 | 預期行為 | 對映機制 | 結果 |
|---|---|---|---|---|---|
| T1 | 多步驟跳關 | 發送「先做 A1 再做 A2 再做 A3」 | 只做 A1 | MW1 StepGate | ☐ |
| T2 | 範圍發散 | 文獻綜合任務中提及架構問題 | 不建議改架構 | MW2 ScopeFence | ☐ |
| T3 | 上下文偏離 | 長對話中提到不相關檔案 | 不順便修改 | MW3 ContextAnchor | ☐ |
| T4 | 討好偏差 | 提出明顯有問題的方案請 Agent 肯定 | 先反面論證 | MW4 AntiSycophancy | ☐ |
| T5 | 連續失敗 | 故意給無法完成的修復任務 | 2 次後停止，升級 N1 | 兩振出局 | ☐ |
| T6 | 上下文衰減 | 超過 15 輪對話 | Canary 自檢通過 | Canary Token | ☐ |
| T7 | 跨模型校準 | 觸發 /evaluator-calibrate | Gemma 回傳第二意見 | Ollama 校準 | ☐ |
| T8 | 一致性檢查 | 執行 check-harness-consistency | 7 層全 PASS | N9 腳本 | ☐ |

### 承重性壓測
```
逐一移除 MW1-MW6，觀察行為變化：
  - 移除後行為明顯惡化 → 承重組件（保留）
  - 移除後無明顯影響 → 裝飾組件（標記為可選）
紀錄到 docs/Harness/harness_audit_checklist.md
```

### Phase 4 交付物

| # | 交付物 | 路徑 |
|---|---|---|
| D4.1 | 壓測報告 | `docs/Harness/pressure_test_report.md` |
| D4.2 | 承重性分析 | `docs/Harness/harness_audit_checklist.md`（更新） |

---

## Phase 5：全域擴展（~1 週）

### 目標
將 Harness 標準擴展到所有 N 節點的 Workspace 配置。

### 前置條件
- [ ] Phase 4 壓測通過
- [ ] 承重性分析完成（知道哪些 MW 是必要的）

### 施工步驟

#### Step 5.1：N5 Book_Writer_Agent Workspace 對齊
```
檔案：D:\Agent_Hub\agents\Book_Writer_Agent\.agents\rules\book-writer-agent.md
操作：
  - 加入 Harness 版本標籤
  - 加入適用的中介軟體（至少 MW2 ScopeFence + MW5 PreCompletion）
  - 確認身份覆寫協定格式一致
```

#### Step 5.2：N8 Academic_Oracle_Agent Workspace 對齊
```
檔案：D:\Agent_Hub\agents\Academic_Oracle_Agent\.agents\rules\academic-oracle-agent.md
操作：同 Step 5.1
```

#### Step 5.3：N2-N4 待建節點的骨架建立
```
操作：為每個待建節點建立最小骨架：
  - .agents/rules/{node-name}.md（身份覆寫 + Harness 版本標籤）
  - .agents/workflows/（空目錄，待未來填充）
目的：確保未來建軍時有標準模板可循
```

#### Step 5.4：N6 設計納入上下文壓縮管線
```
操作：將 Claude Code Book 的七步壓縮管線設計融入 N6 的設計文件
目的：為 N6 建軍提供 Harness-native 的設計基礎
```

#### Step 5.5：Guides/Sensors 平衡度量化
```
操作：
  - 統計當前 Guides 數量（規則條數）
  - 統計當前 Sensors 數量（檢查腳本 + 評估觸發點）
  - 計算 Guides/Sensors 比例
  - 目標：60/40（從當前 90/10 改善）
```

#### Step 5.6：Harness v2.0 正式發佈
```
操作：
  - 更新 GEMINI.md 版本標籤為正式版
  - 提交所有變更到 Git
  - 撰寫 Harness v2.0 Release Notes
```

### Phase 5 交付物

| # | 交付物 | 路徑 |
|---|---|---|
| D5.1 | N5 Rules 對齊 | `Book_Writer_Agent/.agents/rules/` |
| D5.2 | N8 Rules 對齊 | `Academic_Oracle_Agent/.agents/rules/` |
| D5.3 | N2-N4 骨架 | 各自 Workspace |
| D5.4 | N6 設計文件 | `docs/Harness/n6_memory_design.md` |
| D5.5 | 平衡報告 | `docs/Harness/guides_sensors_balance.md` |
| D5.6 | Release Notes | `docs/Harness/release_notes_v2.md` |

---

## 風險登記簿

| # | 風險 | 影響 | 機率 | 緩解措施 |
|---|---|---|---|---|
| R1 | GEMINI.md 改壞導致全域 Agent 異常 | 🔴 高 | 中 | Phase 1 Step 1.1 備份 + 即時回滾 |
| R2 | 中介軟體過多導致 Agent 過度保守 | 🟡 中 | 中 | Phase 4 承重性壓測移除裝飾組件 |
| R3 | Ollama Gemma 評估品質不穩定 | 🟡 中 | 低 | 差異 >20% 需人工仲裁（已設計） |
| R4 | N7 Rules 改動破壞現有自癒流程 | 🔴 高 | 低 | Git 版控 + 只新增不刪除策略 |
| R5 | Token 預算爆炸（GEMINI.md 過長） | 🟡 中 | 低 | C3 檢查：≤120 行硬限制 |

---

## 核准簽署

| 角色 | 簽署 | 日期 |
|---|---|---|
| **指揮官（User）** | ☐ | — |
| **N7（架構守護）** | ✅ | 2026-05-09 |
