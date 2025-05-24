# 金融資料視覺化專案

## 專案結構
- `/modules`：功能模組（資料庫操作、繪圖函式）
- `/app`：Streamlit 主應用程式碼
- `/sql`：資料庫建表語法
- `/data`：資料匯出備份（可忽略）
- `requirements.txt`：Python 套件需求
- `finance_data.db`：SQLite 資料庫（請自行準備）

## 使用說明
1. 建立 SQLite 資料庫及表格：
```bash
sqlite3 finance_data.db < sql/create_tables.sql
