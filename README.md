
# 金融資料視覺化專案

一個以 Python 打造的互動式金融資料視覺化應用，使用 Streamlit 和 Plotly 技術，支援股票、ETF、指數、匯率、商品、債券等多種金融標的的歷史走勢查詢、技術指標分析與多標的比較視覺化功能。

---

## 功能特色

- 多類型金融標的篩選與查詢（股票、ETF、指數、匯率、商品、債券）  
- 單一標的歷史價格與成交量走勢圖  
- 台幣與美元股價換算（匯率整合）  
- 多標的比較分析：跨類型標的收盤價走勢比較圖 
- 技術指標計算與展示：移動平均線(MA)、相對強弱指標(RSI)、MACD
- 報酬與風險指標計算與展示：累積報酬率、年化報酬率、年化波動率、最大回落（Max Drawdown, MDD）
- 使用 SQLite 儲存與讀取歷史資料，快速查詢  
- 互動式日期範圍選擇，靈活檢視特定時間段內的金融變化  

---

## 專案結構

```
finance-visualization/
│
├── app/
│   └── app.py               # 主程式入口 (Streamlit 應用)
├── data/
│   └── finance_data.db      # SQLite 資料庫
├── fonts/
│   └── msjh.ttf             # 微軟正黑體
├── modules/                 # 自訂模組
│   ├── check_data.py        # 檢查與預覽資料庫內容
│   ├── auto_update.py       # 金融資料自動下載與更新模組
│   ├── db_utils.py          # 資料庫連線與查詢工具
│   ├── indicators.py        # 技術指標（MA、RSI、MACD）計算
│   ├── pdf_export.py        # 匯出PDF
│   └── plot_utils.py        # 使用 Plotly 製作圖表的輔助函式
├── sql/
│   ├── create_tables.sql    # 建立資料表結構（symbols、price_data）
│   └── test_queries.sql     # 測試 SQL 查詢語句
├── init_db.py               # 初始化並擷取歷史資料
├── requirements.txt         # 相依套件清單
└── README.md                # 專案說明文件
```

---

## 安裝與執行

建議使用 Python 3.8 以上版本。

安裝所需套件：

```bash
pip install -r requirements.txt
```

初始化資料庫（首次執行）：

```bash
python init_db.py
```

啟動 Streamlit 應用：

```bash
streamlit run app/app.py
```

---

## 使用說明

1. 透過左側側邊欄選擇金融標的類型與具體標的，並設定起始與結束日期範圍。  
2. 單一標的模式下，顯示該標的歷史股價與成交量走勢，若為美股則會自動計算台幣價格。  
3. 點擊「多標的比較」可切換至多標的模式，選擇多個標的後會顯示收盤價走勢比較圖。  
4. 技術指標區塊可以調整 MA 期數及 MACD 參數，顯示該標的的 MA、RSI 與 MACD 指標走勢。
5. 報酬與風險指標分析區塊會顯示：
   - **累積報酬率**（Cumulative Return）  
   - **年化報酬率**（Annualized Return）  
   - **年化波動率**（Annualized Volatility）  
   - **最大回落**（Max Drawdown）  
6. 按下返回按鈕可回到單一標的分析模式。  
7. 依據使用者，可以選擇 JSON / SQLite / Excel / PDF 進行匯出/下載
---

## 依賴套件

- streamlit  
- pandas  
- plotly  
- sqlite3
- numpy
- os
- matplotlib
- matplotlib.pyplot
- matplotlib.dates

---

## 相關模組說明

- `modules/auto_update.py`：負責金融資料的自動下載與更新  
- `modules/db_utils.py`：封裝 SQLite 資料庫的讀取與寫入函式  
- `modules/indicators.py`：
    - 計算技術指標（MA、RSI、MACD）
    - 計算報酬與風險指標（累積報酬率、年化報酬率、波動率、最大回落）
- `modules/plot_utils.py`：自訂 Plotly 畫圖工具，如價格與成交量圖  

---

## 其他說明

- 資料庫中的標的及資料欄位格式請依專案需求設計，確保與讀取函式相符。  
- 若資料缺失或日期錯誤，介面會顯示警告訊息。  
- 歡迎依需求擴充功能，如增加更多技術指標或支援其他資料來源。  
