import os
import json
import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'finance_data.db')
DB_PATH = os.path.abspath(DB_PATH)

PREF_DB_PATH = 'data/user_preferences.db'

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

def save_user_preference(preference: dict, path='user_preference.db'):
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_pref (
                    symbol TEXT,
                    symbol_name TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    currency TEXT,
                    category TEXT
                )''')
    c.execute('INSERT INTO user_pref VALUES (?, ?, ?, ?, ?, ?)', (
        preference['symbol'],
        preference['symbol_name'],
        preference['start_date'],
        preference['end_date'],
        preference['currency'],
        preference['category']
    ))
    conn.commit()
    conn.close()

    # 回傳 SQLite 檔案路徑以便下載
    return path