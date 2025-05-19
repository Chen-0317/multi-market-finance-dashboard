# Multi-Market Finance Dashboard

🚀 一個跨市場的金融資料查詢與視覺化分析平台。

## 📌 功能特色
- 支援多標的資料（股票、ETF、指數、匯率）
- 自動化歷史資料更新（每日）
- 常見技術指標分析：MA、RSI、MACD
- 使用 SQLite 資料庫管理與擴展方便
- Streamlit 視覺化介面

## 📂 專案結構
```
multi-market-finance-dashboard/
├── app/
│   └── dashboard.py           # Streamlit 主應用
├── data/                     # 資料備份（gitignore）
├── sql/                      # SQL 建表與查詢腳本
│   ├── create_tables.sql
│   └── test_queries.sql
├── modules/
│   ├── crawler.py            # 初始資料擷取模組
│   ├── auto_update.py        # 每日自動更新資料
│   ├── indicators.py         # 技術指標模組
│   └── db_utils.py           # 資料庫工具
├── finance.db                # 資料庫檔案（可忽略）
├── .gitignore
├── requirements.txt
└── README.md
```

## 🧪 快速開始
```bash
pip install -r requirements.txt
streamlit run app/dashboard.py
```

## ⏱ 自動更新
```bash
python modules/auto_update.py
```