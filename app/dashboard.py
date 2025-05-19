import streamlit as st
from modules.db_utils import get_symbols, get_price_data
from indicators import MA, RSI, MACD
import plotly.graph_objs as go

st.title("Multi-Market Finance Dashboard")

symbols_df = get_symbols()
symbol = st.selectbox("選擇標的", symbols_df['symbol'].tolist())

if symbol:
    df = get_price_data(symbol)
    if df.empty:
        st.write("無資料")
    else:
        st.subheader(f"{symbol} 歷史股價")
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='價格'
        ))

        if st.checkbox("顯示移動平均線 (MA20)"):
            ma20 = MA(df, 20)
            fig.add_trace(go.Scatter(x=df.index, y=ma20, mode='lines', name='MA20'))

        if st.checkbox("顯示 RSI"):
            rsi = RSI(df)
            st.line_chart(rsi)

        st.plotly_chart(fig)

