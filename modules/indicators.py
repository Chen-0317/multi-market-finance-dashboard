import pandas as pd
import pandas_ta as ta
import numpy as np
import sqlite3

def calculate_ma(df, window=20):
    """短中長期移動平均"""
    df = df.copy()
    df[f'MA{window}'] = df['close'].rolling(window=window).mean()
    return df

def calculate_rsi(df, length=14):
    """相對強弱指標"""
    df[f"rsi{length}"] = ta.rsi(df["close"], length=length)
    return df
    
def calculate_macd(df, base_period=12):
    """移動平均收斂擴散指標"""
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

def cumulative_return(returns: pd.Series) -> float:
    """計算累積報酬率"""
    return (1 + returns).prod() - 1

def annualized_return(returns: pd.Series, periods_per_year=252) -> float:
    """計算年化報酬率"""
    cumulative = cumulative_return(returns)
    n_periods = len(returns)
    return (1 + cumulative) ** (periods_per_year / n_periods) - 1

def annualized_volatility(returns: pd.Series, periods_per_year=252) -> float:
    """計算年化波動率"""
    return returns.std() * np.sqrt(periods_per_year)

def max_drawdown(returns: pd.Series) -> float:
    """計算最大回落（Maximum Drawdown）"""
    cumulative = (1 + returns).cumprod()
    peak = cumulative.cummax()
    drawdown = (cumulative - peak) / peak
    return drawdown.min()
    
def save_indicators_to_db(symbol, db_path="finance_data.db"):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(f"SELECT * FROM price_data WHERE symbol = '{symbol}' ORDER BY date", conn)
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["close"])

    df_ind = compute_indicators(df)
    df_ind["symbol"] = symbol  # 加入 symbol 欄位
    
    # 儲存到新資料表，避免覆蓋整體表格
    df_ind.to_sql("price_data_indicators", conn, if_exists="append", index=False)
    conn.close()
