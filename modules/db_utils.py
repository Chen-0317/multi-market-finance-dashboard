import os
import sqlite3
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'finance_data.db')
DB_PATH = os.path.abspath(DB_PATH)

def get_connection():
    return sqlite3.connect("data/finance_data.db")

def get_symbols():
    conn = get_connection()
    df = pd.read_sql("SELECT id, symbol, name, type, region, currency FROM symbols ORDER BY region, type", conn)
    conn.close()
    return df

def get_price_data(symbol_id, start_date=None, end_date=None):
    conn = get_connection()
    query = """
        SELECT date, open, high, low, close, volume
        FROM price_data
        WHERE symbol_id = ?
    """
    params = [symbol_id] 
    df = pd.read_sql_query(query, conn, params=params, parse_dates=["date"])
    conn.close()   
    return df.sort_values("date")

def load_data(symbol, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    query = """
    SELECT p.date, p.open, p.high, p.low, p.close, p.volume
    FROM price_data p
    JOIN symbols s ON p.symbol_id = s.id
    WHERE s.symbol = ?
    ORDER BY p.date
    """
    df = pd.read_sql(query, conn, params=(symbol,))
    conn.close()
    df['date'] = pd.to_datetime(df['date']).dt.date
    df = df.sort_values('date')  # 確保時間序列正確
    return df