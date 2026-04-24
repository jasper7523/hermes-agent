# Wiki-Writer 實戰攻略計畫：Financial Intelligence Playbook

指揮官，我們即將用剛剛升級完畢的**「全配備進化版 wiki-writer (含 NLP 字典回饋機制)」**對 `E:\我的雲端硬碟G\05.Deloitte\FinCrime\Deloitte FinCrime\Financial Intelligence Playbook` 發起總攻。

剛剛掃描了目標目錄，發現共有 **22 份檔案**（包含系統測試計畫、ETL 架構、資料轉換、邏輯模型等極度硬核的 IT 實施文獻。注意：我們將自動過濾掉 .jpg 等無視覺辨識價值的圖檔）。

這是我為此次行動設計的 S.O.P 規劃：

## 階段 1：無損碎紙與透明註記 (Rule A & Rule C1)
* 撰寫 `playbook_extractor_with_nlp.py`。針對此目錄下的 20 多份文本檔案進行萃取，並寫入到核心的 `playbook_raw.txt`。
* **觸發防呆機制**：在每一份原始文字被匯出的瞬間，程式將同步跑過 TF-IDF 頻率分析，並在 `FILE: {檔名}` 正下方打上醒目的 `[KEYWORDS: ...]` 戳記。確保您隨時能肉眼覆核！

## 階段 2：自動繁衍中央字典 (Rule C2)
* 這包 playbook 充斥著如 `ETL`, `Data Conversion`, `SVVP`, `UAT`, `Logical Model` 等強烈的資訊架構用詞。我預期現有字典將產生「未命中警報」。
* 系統將自動抓取這些極具價值的高頻字眼，**自動擴充寫入** `_Wiki_Clustering_Dictionary.md` 這本中央法典中的「第三象限：電腦稽核與資安」或直接新建「第六象限：AML 系統建置工程（System Implementation）」。

## 階段 3：歸檔去重複與雙向連結 (Rule B)
* **樞紐建立**：因這是一個高度專精的 IT 系統操作包，系統將自動創立 `_MOC_Financial_Intelligence_Playbook.md` (金融情資系統架構與實施手冊) 專區。
* **防線串接**：把這套系統實施的心法，利用雙向連結 `[[]]` 回扣到我們之前的 `[[資訊安全與電腦稽核]]` 跟 `[[洗錢防制與 KYC 基礎標準]]`，完成理論與工程實踐的合體。

## ⚠️ User Review Required
**請指揮官覆核此攻略路徑！** 
一旦您點頭，我就會啟動這套進化版爬蟲與 NLP 引擎，並把帶有 `[KEYWORDS]` 戳記的 `playbook_raw.txt` 與初步的字典擴充結果交付給您，讓您行使「Rule C3 絕對覆核權」！
