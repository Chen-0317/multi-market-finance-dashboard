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
            region TEXT,
            currency TEXT
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS converted_price_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            price_data_id INTEGER,
            converted_price REAL,
            converted_currency TEXT,
            FOREIGN KEY (price_data_id) REFERENCES price_data(id)
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
        INSERT OR IGNORE INTO symbols (symbol, name, type, region, currency)
        VALUES (?, ?, ?, ?, ?)
    ''', (symbol_data['symbol'], symbol_data['name'], symbol_data['type'], symbol_data['region'], symbol_data.get('currency')))
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

        # 如果有自訂 alias，就覆蓋 symbol
        target_symbol = target.get("alias", target["symbol"])
        symbol_data = {
            "symbol": target_symbol,
            "name": target["name"],
            "type": target["type"],
            "region": target["region"],
            "currency": target.get("currency")
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
        
            cursor.execute('SELECT id FROM price_data WHERE symbol_id = ? AND date = ?', (symbol_id, row['date'].date()))
            price_data_id = cursor.fetchone()[0]
        
            # 判斷原始幣別
            if target['region'] == 'US' or target['symbol'].endswith('.US'):
                original_currency = 'USD'
            elif target['region'] == 'TW' or target['symbol'].endswith('.TW'):
                original_currency = 'TWD'
            else:
                original_currency = None
        
            # 匯率轉換：從 price_data 查詢 USDTWD=X 的最新收盤價
            converted_price = None
            converted_currency = None
        
            if original_currency in ['USD', 'TWD']:
                # 找出 USDTWD=X 的 symbol_id
                cursor.execute("SELECT id FROM symbols WHERE symbol = 'USDTWD=X'")
                usd_twd_symbol_id_row = cursor.fetchone()
        
                if usd_twd_symbol_id_row:
                    usd_twd_symbol_id = usd_twd_symbol_id_row[0]

                    # 查詢最新一筆 USDTWD=X 的收盤價
                    cursor.execute('''
                        SELECT close FROM price_data
                        WHERE symbol_id = ?
                        ORDER BY date DESC
                        LIMIT 1
                    ''', (usd_twd_symbol_id,))
                    rate_row = cursor.fetchone()
        
                    if rate_row:
                        exchange_rate = rate_row[0]
        
                        if original_currency == 'USD':
                            converted_price = row['close'] * exchange_rate
                            converted_currency = 'TWD'
                        elif original_currency == 'TWD':
                            converted_price = row['close'] / exchange_rate
                            converted_currency = 'USD'
        
            # 寫入 converted_price_data
            if converted_price and converted_currency:
                cursor.execute('''
                    INSERT OR REPLACE INTO converted_price_data
                    (price_data_id, converted_price, converted_currency)
                    VALUES (?, ?, ?)
                ''', (price_data_id, converted_price, converted_currency))
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

    pd.set_option('display.float_format', '{:.6f}'.format)

    print("\n📌 symbols 資料表內容：")
    df_symbols = pd.read_sql_query("SELECT * FROM symbols", conn)
    print(df_symbols)

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM price_data")
    print("📦 price_data 資料筆數：", cursor.fetchone()[0])

    print("\n📊 price_data 近 10 筆資料：")
    df_prices = pd.read_sql_query("""
        SELECT s.symbol, p.date, p.open, p.high, p.low, p.close, p.volume
        FROM price_data p
        JOIN symbols s ON p.symbol_id = s.id
        ORDER BY p.date DESC
        LIMIT 10
    """, conn)
    print(df_prices)

    print("\n💱 每個 symbol 的最新轉換資料：")
    df_converted = pd.read_sql_query("""
        SELECT s.symbol, p.date, c.converted_price, c.converted_currency
        FROM converted_price_data c
        JOIN price_data p ON c.price_data_id = p.id
        JOIN symbols s ON p.symbol_id = s.id
        WHERE (s.symbol, p.date) IN (
            SELECT s2.symbol, MAX(p2.date)
            FROM converted_price_data c2
            JOIN price_data p2 ON c2.price_data_id = p2.id
            JOIN symbols s2 ON p2.symbol_id = s2.id
            GROUP BY s2.symbol
        )
        ORDER BY p.date DESC
    """, conn)
    print(df_converted)

    
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
        {"symbol": "USDTWD=X", "name": "美元/台幣", "type": "currency", "region": "TW", "currency": "TWD"},
        {"symbol": "USDJPY=X", "name": "美元/日圓", "type": "currency", "region": "JP", "currency": "JPY"},
        {"symbol": "TWDJPY=X", "name": "台幣/日圓", "type": "currency", "region": "JP", "currency": "JPY"},
        {"symbol": "^GSPC", "name": "S&P 500", "type": "index", "region": "US", "currency": "USD"},
        {"symbol": "^IXIC", "name": "納斯達克綜合指數", "type": "index", "region": "US", "currency": "USD"},
        {"symbol": "^DJI", "name": "道瓊斯工業平均指數", "type": "index", "region": "US", "currency": "USD"},
        {"symbol": "URTH", "name": "MSCI全球指數", "type": "index", "region": "Global", "currency": "USD"},
        {"symbol": "0050.TW", "name": "台灣50", "type": "etf", "region": "TW", "currency": "TWD"},
        {"symbol": "00878.TW", "name": "元大MSCI世界ETF", "type": "etf", "region": "TW", "currency": "TWD"},
        {"symbol": "00646.TW", "name": "富邦科技ETF", "type": "etf", "region": "TW", "currency": "TWD"},
        {"symbol": "00850.TW", "name": "元大台灣 ESG 永續 ETF", "type": "etf", "region": "TW", "currency": "TWD"},
        {"symbol": "AAPL", "name": "蘋果", "type": "stock", "region": "US", "currency": "USD"},
        {"symbol": "MSFT", "name": "微軟", "type": "stock", "region": "US", "currency": "USD"}
    ]

    conn, cursor = init_db()
    fetch_and_save_data(cursor, conn, targets)
    validate_data(cursor)
    preview_data(conn, cursor)
    export_db_to_sql()
    export_symbols_to_csv(conn)
    conn.close()
