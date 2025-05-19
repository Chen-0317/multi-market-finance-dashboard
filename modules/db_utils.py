import sqlite3
import pandas as pd

DB_PATH = "finance.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def create_tables():
    sql = """
    CREATE TABLE IF NOT EXISTS symbols (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT UNIQUE,
        name TEXT,
        market TEXT
    );
    CREATE TABLE IF NOT EXISTS price_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        date TEXT,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume INTEGER,
        UNIQUE(symbol, date)
    );
    """
    conn = get_connection()
    conn.executescript(sql)
    conn.commit()
    conn.close()

def upsert_price_data(df: pd.DataFrame, symbol: str):
    conn = get_connection()
    cursor = conn.cursor()
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT OR IGNORE INTO price_data (symbol, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (symbol, row.name.strftime("%Y-%m-%d"), row['Open'], row['High'], row['Low'], row['Close'], row['Volume']))
    conn.commit()
    conn.close()

def get_symbols():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM symbols", conn)
    conn.close()
    return df

def get_latest_date(symbol):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(date) FROM price_data WHERE symbol = ?", (symbol,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result and result[0] else None

def get_price_data(symbol):
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM price_data WHERE symbol = ? ORDER BY date", conn, params=(symbol,))
    conn.close()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
    return df
