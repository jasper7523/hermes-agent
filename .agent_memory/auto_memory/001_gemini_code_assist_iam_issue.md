# Issue: Gemini Code Assist Permission Denied (403)
**Timestamp**: 2026-04-28
**Component**: GCP IAM / Infrastructure Layer
**Status**: DIAGNOSED / PENDING_N3_EXECUTION

## Context (上下文)
使用者回報在使用 Gemini Code Assist 時遭遇錯誤：
`A permission denied error was encountered. Please ensure that the correct project ID is configured or that you have permission to call Gemini Code Assist in the project.`

## Root Cause (成因分析)
依據第一性原理，此為 Google Cloud IAM 存取控制阻斷。可能成因包含：
1. 本地開發環境 (IDE/CLI) 未正確設定 `Project ID` 或綁定錯專案。
2. 目標 GCP 專案未啟用 `cloudaicompanion.googleapis.com` API。
3. 請求的帳號缺少 `roles/cloudaicompanion.user` (Cloud AI Companion User) 角色權限。
4. Application Default Credentials (ADC) 已過期。

## Remediation / Action Taken (修復與處置)
N7 已產出基礎架構修復腳本交由 N1/N3 接手處理。
修復核心步驟包含：
1. `gcloud auth login` 及 `gcloud auth application-default login` 刷新憑證。
2. `gcloud config set project <PROJECT_ID>` 強制綁定專案。
3. 啟用對應的 API 服務。
4. 綁定正確的 IAM Policy Binding。

未經沙箱驗證前不應自動覆寫，等待 N3 進行實體驗證。
