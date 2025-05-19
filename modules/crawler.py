import yfinance as yf
from db_utils import upsert_price_data, get_symbols, get_latest_date
import pandas as pd

def fetch_and_update(symbol: str):
    last_date = get_latest_date(symbol)
    if last_date:
        start_date = pd.to_datetime(last_date) + pd.Timedelta(days=1)
    else:
        start_date = "2000-01-01"  # 或你需要的起始日期

    df = yf.download(symbol, start=start_date)
    if df.empty:
        print(f"No new data for {symbol}")
        return
    
    upsert_price_data(df, symbol)
    print(f"Updated data for {symbol} from {start_date.date()}")

def update_all_symbols():
    symbols = get_symbols()
    for symbol in symbols['symbol']:
        fetch_and_update(symbol)

if __name__ == "__main__":
    update_all_symbols()
