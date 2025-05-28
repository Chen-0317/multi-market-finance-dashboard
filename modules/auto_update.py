import schedule
import time
import pandas as pd
import sqlite3
import yfinance as yf
from datetime import datetime, timedelta

DB_PATH = 'data/finance_data.db'  # 請根據實際路徑調整

def get_all_symbols(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT symbol FROM symbols")
    return [row[0] for row in cursor.fetchall()]

def get_symbol_id(conn, symbol):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM symbols WHERE symbol = ?", (symbol,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        raise ValueError(f"❌ 無法找到 symbol：{symbol} 對應的 symbol_id")

def get_latest_date(conn, symbol):
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(date) FROM price_data WHERE symbol_id = ?", (symbol,))
    result = cursor.fetchone()
    if result and result[0]:
        return datetime.strptime(result[0], '%Y-%m-%d')
    return None

def update_symbol_data(conn, symbol):
    try:
        symbol_id = get_symbol_id(conn, symbol)
        latest_date = get_latest_date(conn, symbol_id)
        today = datetime.now().date()

        # 決定下載的日期範圍
        start_date = (latest_date + timedelta(days=1)).date() if latest_date else datetime(2000, 1, 1).date()
        end_date = today

        if start_date > end_date:
            print(f"⚠️ {symbol} 沒有新資料需要更新 (latest={latest_date.date() if latest_date else '無'}, today={end_date})")
            return

        # 執行資料下載
        try:
            data = yf.download(symbol, start=start_date, end=end_date + timedelta(days=1), progress=False, auto_adjust=False)
        except Exception as e:
            print(f"❌ 無法下載 {symbol} 的資料：{e}")
            return

        if data.empty:
            print(f"⚠️ {symbol} 沒有新資料")
            return

        data.reset_index(inplace=True)
        cursor = conn.cursor()

        count = 0
        for _, row in data.iterrows():
            date = pd.to_datetime(row['Date']).strftime('%Y-%m-%d')

            cursor.execute('''
                INSERT OR REPLACE INTO price_data 
                (symbol_id, date, open, high, low, close, volume) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol_id,
                date,
                row['Open'],
                row['High'],
                row['Low'],
                row['Close'],
                row['Volume']
            ))
            count += 1

        conn.commit()
        print(f"✅ {symbol} 更新完成，共新增/更新 {count} 筆資料")

    except Exception as e:
        print(f"❌ 更新 {symbol} 發生錯誤：{e}")


def update_symbol_data(conn, symbol):
    try:
        symbol_id = get_symbol_id(conn, symbol)
        latest_date = get_latest_date(conn, symbol_id)
        today = datetime.now().date()

        start_date = (latest_date + timedelta(days=1)).date() if latest_date else datetime(2000, 1, 1).date()
        end_date = today

        if start_date > end_date:
            print(f"⚠️ {symbol} 沒有新資料需要更新 (latest={latest_date.date() if latest_date else '無'}, today={end_date})")
            return

        try:
            data = yf.download(symbol, start=start_date, end=end_date + timedelta(days=1), progress=False, auto_adjust=False)
        except Exception as e:
            print(f"❌ 無法下載 {symbol} 的資料：{e}")
            return

        if data.empty:
            print(f"⚠️ {symbol} 沒有新資料")
            return

        data.reset_index(inplace=True)
        # print(data.columns)

        cursor = conn.cursor()
        count = 0

        for _, row in data.iterrows():
            date_val = row[('Date', '')]
            # 確保 date_val 是 Timestamp
            if not isinstance(date_val, pd.Timestamp):
                date_val = pd.to_datetime(date_val)
            date_str = date_val.strftime('%Y-%m-%d')

            open_ = row[('Open', symbol)]
            high_ = row[('High', symbol)]
            low_ = row[('Low', symbol)]
            close_ = row[('Close', symbol)]
            volume_ = row[('Volume', symbol)]
            
            cursor.execute('''
                INSERT OR REPLACE INTO price_data 
                (symbol_id, date, open, high, low, close, volume) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (symbol_id, date_str, open_, high_, low_, close_, volume_))
            count += 1

        conn.commit()
        print(f"✅ {symbol} 更新完成，共新增/更新 {count} 筆資料")

    except Exception as e:
        print(f"❌ 更新 {symbol} 發生錯誤：{e}")

def main():
    print("開始更新所有標的資料")
    conn = sqlite3.connect(DB_PATH)
    try:
        symbols = get_all_symbols(conn)
        for symbol in symbols:
            update_symbol_data(conn, symbol)
    finally:
        conn.close()
    print("所有標的資料更新完成")
    
def job():
    print("⏰ 執行定期更新...")
    main()

if __name__ == '__main__':
    # 先執行一次（開機/手動執行時）
    main()

    # 排程：每天早上 8 點自動更新
    schedule.every().day.at("09:00").do(job)  # 台股收盤後更新
    schedule.every().day.at("18:00").do(job)  # 美股更新時段

    while True:
        schedule.run_pending()
        time.sleep(60)