
# 金融資料視覺化專案

一個使用 Streamlit 與 Plotly 製作的金融資料視覺化應用，支援個股、ETF、指數、匯率、商品與債券等多類型金融標的的歷史走勢查詢與多標的比較，並結合技術指標（MA、RSI、MACD）計算與展示。

---

## 功能特色

- 多類型金融標的篩選與查詢（股票、ETF、指數、匯率、商品、債券）  
- 單一標的歷史價格與成交量走勢圖  
- 台幣與美元股價換算（匯率整合）  
- 多標的收盤價比較（跨類型皆可）  
- 技術指標計算與展示：移動平均線(MA)、相對強弱指標(RSI)、MACD  
- 使用 SQLite 儲存與讀取歷史資料，快速查詢  
- 友善互動式介面，提供日期區間選擇  

---

## 專案結構

```
finance-visualization/
│
├── app/
│   └── app.py               # 主程式入口 (Streamlit 應用)
├── data/
│   └── finance_data.db      # SQLite 資料庫
├── modules/                 # 自訂模組
│   ├── check_data.py        # 擷取資料庫資訊並顯示
│   ├── auto_update.py       # 資料自動更新模組
│   ├── db_utils.py          # 資料庫操作工具
│   ├── indicators.py        # 技術指標計算模組
│   └── plot_utils.py        # 繪圖函式模組
├── sql/
│   ├── create_tables.sql    # 定資料表的結構
│   └── test_queries.sql     # 檢查資料表內容
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

確認 `data/finance_data.db` 資料庫已存在並包含所需資料。

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
5. 按下返回按鈕可回到單一標的分析模式。  

---

## 依賴套件

- streamlit  
- pandas  
- plotly  
- sqlite3  

---

## 相關模組說明

- `modules/auto_update.py`：負責金融資料的自動下載與更新  
- `modules/db_utils.py`：封裝 SQLite 資料庫的讀取與寫入函式  
- `modules/indicators.py`：計算技術指標（MA、RSI、MACD）  
- `modules/plot_utils.py`：自訂 Plotly 畫圖工具，如價格與成交量圖  

---

## 其他說明

- 資料庫中的標的及資料欄位格式請依專案需求設計，確保與讀取函式相符。  
- 若資料缺失或日期錯誤，介面會顯示警告訊息。  
- 歡迎依需求擴充功能，如增加更多技術指標或支援其他資料來源。  
