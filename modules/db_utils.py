import sqlite3
import pandas as pd

def get_connection():
    return sqlite3.connect("data/finance_data.db")

def get_symbols():
    conn = get_connection()
    df = pd.read_sql("SELECT id, symbol, name, type, region FROM symbols ORDER BY region, type", conn)
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
    if start_date and end_date:
        query += " AND date BETWEEN ? AND ?"
        params += [start_date, end_date]
    df = pd.read_sql_query(query, conn, params=params, parse_dates=["date"])
    conn.close()
    return df.sort_values("date")