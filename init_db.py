import os
import sqlite3
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# ----------------------
# 資料庫初始化
# ----------------------
def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect("data/finance_data.db")
    cursor = conn.cursor()

    # 建立資料表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS symbols (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE,
            name TEXT,
            type TEXT,
            region TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol_id INTEGER,
            date DATE,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            UNIQUE(symbol_id, date)
        )
    ''')

    # 建立索引以提升查詢效能
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol ON symbols(symbol)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol_id ON price_data(symbol_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON price_data(date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol_date ON price_data(symbol_id, date)')

    # 確認 symbols 表格是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='symbols'")
    result = cursor.fetchone()
    if result:
        print("✅ symbols 表格已建立")
    else:
        print("❌ symbols 表格不存在")
        
    conn.commit()
    return conn, cursor

# ----------------------
# 插入 symbol 並取得 id
# ----------------------
def insert_symbol_get_id(cursor, conn, symbol_data):
    cursor.execute('''
        INSERT OR IGNORE INTO symbols (symbol, name, type, region)
        VALUES (?, ?, ?, ?)
    ''', (symbol_data['symbol'], symbol_data['name'], symbol_data['type'], symbol_data['region']))
    conn.commit()
    cursor.execute('SELECT id FROM symbols WHERE symbol = ?', (symbol_data['symbol'],))
    return cursor.fetchone()[0]

# ----------------------
# 擷取並寫入資料
# ----------------------
def fetch_and_save_data(cursor, conn, targets):
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365)

    for target in targets:
        print(f"▶ 擷取 {target['symbol']} 資料中...")
        df = yf.download(target["symbol"], start=start_date, end=end_date, auto_adjust=False)

        print(f"欄位：{df.columns.tolist()}")
        print(f"原始資料筆數：{len(df)}")
    
        if df.empty:
            print(f"⚠️ 無法擷取 {target['symbol']} 資料（可能無歷史資料或格式異常），已跳過")
            continue

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)

        df = df.reset_index()
        df.columns.name = None
        df.columns = [col.lower() for col in df.columns]

        if "close" in df.columns and not all(col in df.columns for col in ["open", "high", "low"]):
            df["open"] = df["high"] = df["low"] = df["close"]
        if "volume" not in df.columns:
            df["volume"] = 0

        df = df.dropna()
        df = df[(df[["open", "high", "low", "close"]] > 0).all(axis=1)]

        print(f"清理後資料筆數：{len(df)}")
        print(df.head())

        # 如果有自訂 alias，就覆蓋 symbol（用於統一名稱，像是 USD_TWD）
        target_symbol = target.get("alias", target["symbol"])
        symbol_data = {
            "symbol": target_symbol,
            "name": target["name"],
            "type": target["type"],
            "region": target["region"]
        }
        symbol_id = insert_symbol_get_id(cursor, conn, symbol_data)

        # 寫入 price_data
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT OR IGNORE INTO price_data
                (symbol_id, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol_id,
                row['date'].date(),
                row['open'],
                row['high'],
                row['low'],
                row['close'],
                row['volume']
            ))
        conn.commit()

# ----------------------
# 驗證資料
# ----------------------
def validate_data(cursor):
    cursor.execute('''
        SELECT s.name, s.symbol, COUNT(p.id), MIN(p.date), MAX(p.date)
        FROM symbols s
        JOIN price_data p ON s.id = p.symbol_id
        GROUP BY s.symbol
        LIMIT 3
    ''')
    print("✅ 隨機抽查結果：")
    for row in cursor.fetchall():
        print(f"✔ {row[0]} ({row[1]}): {row[2]} 筆，期間 {row[3]} ~ {row[4]}")

# ----------------------
# 顯示前幾筆資料
# ----------------------
def preview_data(conn, cursor):
    print("\n📌 symbols 資料表內容：")
    df_symbols = pd.read_sql_query("SELECT * FROM symbols", conn)
    print(df_symbols)

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM price_data")
    print("📦 price_data 資料筆數：", cursor.fetchone()[0])

    print("\n📊 price_data 前 10 筆資料：")
    df_prices = pd.read_sql_query("""
        SELECT s.symbol, p.date, p.open, p.high, p.low, p.close, p.volume
        FROM price_data p
        JOIN symbols s ON p.symbol_id = s.id
        ORDER BY p.date
        LIMIT 10
    """, conn)
    print(df_prices)

# ----------------------
# 資料庫匯出為 SQL 檔案
# ----------------------
def export_db_to_sql():
    conn = sqlite3.connect('data/finance_data.db')
    with open('data/finance_data.sql', 'w') as f:
        for line in conn.iterdump():
            f.write('%s\n' % line)
    print("資料庫已匯出為 data/finance_data.sql")

# ----------------------
# 生成 csv
# ----------------------
def export_symbols_to_csv(conn):
    df_symbols = pd.read_sql_query("SELECT * FROM symbols", conn)
    df_symbols.to_csv('symbol_list.csv', index=False)
    print("標的資訊已匯出為 symbol_list.csv")

# ----------------------
# 主程式
# ----------------------
if __name__ == "__main__":
    targets = [
        {"symbol": "USDJPY=X", "name": "美元/日圓", "type": "currency", "region": "JP"},
        {"symbol": "USDTWD=X", "name": "美元/台幣", "type": "currency", "region": "TW", "alias": "USD_TWD"},
        {"symbol": "TWDJPY=X", "name": "台幣/日圓", "type": "currency", "region": "JP"},
        {"symbol": "^GSPC", "name": "S&P 500", "type": "index", "region": "US"},
        {"symbol": "^IXIC", "name": "納斯達克綜合指數", "type": "index", "region": "US"},
        {"symbol": "^DJI", "name": "道瓊斯工業平均指數", "type": "index", "region": "US"},
        {"symbol": "URTH", "name": "MSCI全球指數", "type": "index", "region": "Global"},
        {"symbol": "0050.TW", "name": "台灣50", "type": "etf", "region": "TW"},
        {"symbol": "00878.TW", "name": "元大MSCI世界ETF", "type": "etf", "region": "TW"},
        {"symbol": "00646.TW", "name": "富邦科技ETF", "type": "etf", "region": "TW"},
        {"symbol": "00850.TW", "name": "元大台灣 ESG 永續 ETF", "type": "etf", "region": "TW"},
        {"symbol": "AAPL", "name": "蘋果", "type": "stock", "region": "US"},
        {"symbol": "MSFT", "name": "微軟", "type": "stock", "region": "US"}
    ]

    conn, cursor = init_db()
    fetch_and_save_data(cursor, conn, targets)
    validate_data(cursor)
    preview_data(conn, cursor)
    export_db_to_sql()
    export_symbols_to_csv(conn)
    conn.close()
