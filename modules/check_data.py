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

def main():
    # 1. 取得所有 symbols
    symbols_df = get_symbols()
    print("Symbols 範例資料：")
    print(symbols_df.head(10))  # 顯示前10筆 symbols

    # 2. 目標 symbol 字串 (你要查的 symbol)
    target_symbol = "USDTWD=X"  # 這裡改成你想查的 symbol 字串

    # 3. 找 symbol 對應的 id
    matching = symbols_df.loc[symbols_df['symbol'] == target_symbol, 'id'].values
    if len(matching) == 0:
        print(f"找不到 symbol = '{target_symbol}' 的 symbol_id")
        return
    symbol_id = matching[0]
    print(f"symbol_id for '{target_symbol}' is: {symbol_id}")

    # 不帶日期限制
    price_df_all = get_price_data(2)
    print("USDTWD=X 全部價格資料前5筆:")
    print(price_df_all.head())
    print(f"資料筆數：{len(price_df_all)}")
    
    # 詢問日期範圍
    conn = get_connection()
    query = "SELECT MIN(date) AS min_date, MAX(date) AS max_date FROM price_data WHERE symbol_id = ?"
    df_range = pd.read_sql_query(query, conn, params=[2])
    conn.close()
    print("USDTWD=X 資料日期範圍：")
    print(df_range)



if __name__ == "__main__":
    main()
