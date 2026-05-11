# N0 缺陷紀錄：KI 路徑解析不一致

> **缺陷等級**：N0 (Harness Runtime)
> **發現日期**：2026-05-11
> **發現者**：N7 Hermes Agent
> **狀態**：已修復（文件化 + dev-guide 追加）

---

## 1. 問題描述

Antigravity 引擎注入的 `appDataDir` 為 `C:\Users\promy\.gemini\antigravity`，
導致系統提示指引 Agent 到 `<appDataDir>\knowledge\` 查找 KI。

但實際上 KI 統一存放於**全域路徑** `C:\Users\promy\.gemini\knowledge\`，
造成 Agent 搜錯路徑、誤判「KI 未持久化」。

## 2. 影響範圍

| 影響 | 說明 |
|---|---|
| KI 讀取失敗 | Agent 在新對話開場時無法自動載入 KI 摘要 |
| 時間浪費 | 需額外搜尋、翻查歷史對話日誌才能定位正確路徑 |
| 誤報風險 | Agent 可能對使用者宣稱「KI 不存在」，實際上 KI 完好 |

## 3. 根本原因

| 路徑 | 用途 | KI 是否存在 |
|---|---|---|
| `C:\Users\promy\.gemini\antigravity\knowledge\` | Antigravity 引擎內部 KI 儲存 | ❌ 僅有 `Behavioral_Incidents` |
| `C:\Users\promy\.gemini\knowledge\` | **全域 KI 儲存（canonical path）** | ✅ 所有 KI 均在此 |

系統提示的 `<appDataDir>` 定義與 KI 的實際儲存位置存在**結構性偏差**。

## 4. 修復措施

1. ✅ 在 `hermes-dev-guide.md` 追加 KI 路徑規範，明確指定 canonical path
2. ✅ 本缺陷紀錄歸檔至 `docs/Harness/`
3. ⚠️ Antigravity 的 `appDataDir` 注入屬於系統層級（N0），N7 無權修改——需使用者層級的設定調整或上游修復

## 5. 預防建議

- 所有 Agent 在查找 KI 時，應以 `C:\Users\promy\.gemini\knowledge\` 為**唯一 canonical 路徑**
- `appDataDir` 的 `knowledge\` 子目錄僅作為 fallback，不作為主查找路徑
- 新建 KI 時，**一律寫入全域路徑**，禁止寫入引擎內部目錄
