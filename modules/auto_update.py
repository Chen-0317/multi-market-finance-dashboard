# auto_update.py
import sqlite3
import yfinance as yf
from datetime import datetime, timedelta

DB_PATH = 'data/finance_data.db'  # 修改成你資料庫路徑

def get_all_symbols(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT symbol FROM symbols")
    symbols = [row[0] for row in cursor.fetchall()]
    return symbols

def get_latest_date(conn, symbol):
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(date) FROM price_data WHERE symbol = ?", (symbol,))
    result = cursor.fetchone()
    if result and result[0]:
        return datetime.strptime(result[0], '%Y-%m-%d')
    return None

def update_symbol_data(conn, symbol):
    latest_date = get_latest_date(conn, symbol)

    # 若無資料，從較早時間開始
    if latest_date is None:
        start_date = '2000-01-01'
    else:
        # 往後推一天，避免資料遺漏
        start_date = (latest_date + timedelta(days=1)).strftime('%Y-%m-%d')

    print(f"更新 {symbol} 從 {start_date} 開始")

    # 抓取資料
    data = yf.download(symbol, start=start_date, progress=False)
    if data.empty:
        print(f"{symbol} 沒有新資料")
        return

    data.reset_index(inplace=True)
    cursor = conn.cursor()

    for _, row in data.iterrows():
        date_str = row['Date'].strftime('%Y-%m-%d')

        cursor.execute('''
            INSERT OR REPLACE INTO price_data 
            (symbol, date, open, high, low, close, volume) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            symbol,
            date_str,
            row['Open'],
            row['High'],
            row['Low'],
            row['Close'],
            row['Volume']
        ))
    conn.commit()
    print(f"{symbol} 更新完成，共新增/更新 {len(data)} 筆資料")

def main():
    conn = sqlite3.connect(DB_PATH)
    symbols = get_all_symbols(conn)
    print(f"共有 {len(symbols)} 個標的要更新")

    for symbol in symbols:
        try:
            update_symbol_data(conn, symbol)
        except Exception as e:
            print(f"更新 {symbol} 發生錯誤：{e}")

    conn.close()
    print("全部標的更新完成")

if __name__ == '__main__':
    main()
