from modules.db_utils import get_connection
from modules.crawler import fetch_price_data

def update_all_symbols():
    conn = get_connection()
    symbols = get_all_symbols(conn)
    
    for symbol in symbols:
        latest_date = get_latest_date(conn, symbol)
        new_data = fetch_price_data(symbol, start=latest_date)
        upsert_price_data(conn, symbol, new_data)
    
    conn.close()

if __name__ == "__main__":
    update_all_symbols()
