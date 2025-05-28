import pandas as pd
import pandas_ta as ta
import sqlite3

def calculate_ma(df, window=20):
    df = df.copy()
    df[f'MA{window}'] = df['close'].rolling(window=window).mean()
    return df

def calculate_rsi(df, length=14):
    df[f"rsi{length}"] = ta.rsi(df["close"], length=length)
    return df
    
def calculate_macd(df, base_period=12):
    df = df.copy()
    # 用 base_period 來決定 fast, slow, signal
    fast = base_period
    slow = base_period * 2
    signal = max(base_period // 2, 1)

    macd = ta.macd(df["close"], fast=fast, slow=slow, signal=signal)
    df["macd"] = macd[f"MACD_{fast}_{slow}_{signal}"]
    df["macd_signal"] = macd[f"MACDs_{fast}_{slow}_{signal}"]
    df["macd_hist"] = macd[f"MACDh_{fast}_{slow}_{signal}"]
    return df

def compute_indicators(df):
    df = df.copy()
    df = calculate_ma(df, 5)
    df = calculate_ma(df, 20)
    df = calculate_ma(df, 60)
    df = calculate_rsi(df, 14)
    df = calculate_macd(df)
    return df

def save_indicators_to_db(symbol, db_path="finance_data.db"):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(f"SELECT * FROM price_data WHERE symbol = '{symbol}' ORDER BY date", conn)
    df_ind = compute_indicators(df)
    df_ind.to_sql("price_data_indicators", conn, if_exists="replace", index=False)
    conn.close()