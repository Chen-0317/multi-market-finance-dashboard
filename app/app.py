import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import sqlite3
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from datetime import datetime, timedelta
from modules import auto_update, indicators
from modules.db_utils import get_symbols, get_price_data, load_data
from modules.plot_utils import plot_price_volume

if "compare_mode" not in st.session_state:
    st.session_state.compare_mode = False
    
st.set_page_config("📈 金融資料視覺化", layout="wide")
st.sidebar.title("📌 選擇條件")

DB_PATH = 'data/finance_data.db'
type_mapping = {
    'stock': '股價',
    'currency': '匯率',
    'index': '指數',
    'etf': 'ETF',
    'commodity': '商品',
    'bond': '債券',
}

symbols_df = get_symbols()
symbols_df['type_cn'] = symbols_df['type'].map(type_mapping)

category = st.sidebar.selectbox("類型", symbols_df["type_cn"].unique())
filtered_symbols = symbols_df[symbols_df["type_cn"] == category]

symbol_options = list(filtered_symbols.itertuples(index=False))
selected = st.sidebar.selectbox(
    "選擇標的",
    symbol_options,
    format_func=lambda x: f"{x.name} ({x.symbol})"
)

today = datetime.today().date()
default_start = today - timedelta(days=180)
start_date = st.sidebar.date_input("起始日期", default_start)
end_date = st.sidebar.date_input("結束日期", today)

if st.sidebar.button("📈 多標的比較"):
    st.session_state.compare_mode = True

df = get_price_data(selected.id, start_date, end_date)
aapl_df = df[["date", "close", "volume"]].copy()

# print(symbols_df["symbol"].unique())  # 看有哪些 symbol
# print(symbols_df[symbols_df["symbol"] == "USDTWD=X"])

# symbols_df["symbol"] = symbols_df["symbol"].str.strip()
# usdtwd_id = symbols_df[symbols_df["symbol"] == "USDTWD=X"]["id"].values[0]

usd_twd_df = get_price_data(2, start_date, end_date)
# print(usd_twd_df)

if not st.session_state.compare_mode:
    st.title(f"📊 {selected.name} ({selected.symbol}) 歷史走勢")

    region_label = {
        "TW": "📌 台灣市場",
        "US": "🇺🇸 美國市場",
        "JP": "🇯🇵 日本市場",
        "Global": "🌐 全球市場"
    }
    
    type_desc = {
        "stock": "個股價格資料",
        "etf": "ETF 基金價格資料",
        "index": "股市指數",
        "currency": "匯率（即時兌換比價）",
        "commodity": "大宗商品",
        "bond": "債券殖利率"
    }

    st.markdown(f"**市場地區**：{region_label.get(selected.region, selected.region)}")
    st.markdown(f"**資料類型**：{type_desc.get(selected.type, selected.type)}")

    st.plotly_chart(plot_price_volume(df, title=selected.name), use_container_width=True)

    if selected.region == "US" and selected.type == "stock":
        symbol_name = selected.name or selected.symbol
        price_col_name = f"{symbol_name}_usd"
        volume_col_name = f"{symbol_name}_volume"
    
        aapl_df.rename(columns={"close": price_col_name}, inplace=True)
        if "volume" in aapl_df.columns:
            aapl_df.rename(columns={"volume": volume_col_name}, inplace=True)
        
        # ✅ 嘗試從 close / adj_close 擷取匯率欄位
        usd_twd_df.columns = [col.lower() for col in usd_twd_df.columns]  # 欄位轉小寫
        
        if "adj_close" in usd_twd_df.columns:
            usd_twd_df.rename(columns={"adj_close": "usd_to_twd"}, inplace=True)
        elif "close" in usd_twd_df.columns:
            usd_twd_df.rename(columns={"close": "usd_to_twd"}, inplace=True)
        else:
            st.warning("⚠️ 無法找到 USD/TWD 匯率欄位（adj_close 或 close），請確認資料格式正確")
            st.write("⚠️ 匯率資料欄位為：", usd_twd_df.columns.tolist())
            usd_twd_df = pd.DataFrame(columns=["date", "usd_to_twd"])  # 保持 merge 時不會報錯

        # ✅ 標準化日期格式
        aapl_df['date'] = pd.to_datetime(aapl_df['date']).dt.date
        usd_twd_df['date'] = pd.to_datetime(usd_twd_df['date']).dt.date
        
        # ✅ 標準化欄位名稱
        usd_twd_df.columns = [col.lower() for col in usd_twd_df.columns]
        usd_twd_df.rename(columns={"close": "usd_to_twd"}, inplace=True)

        # st.write("✅ aapl_df 預覽", aapl_df.head())
        # st.write("✅ usd_twd_df 預覽", usd_twd_df.head())
        # st.write("✅ 匯率欄位名稱", usd_twd_df.columns.tolist())
        # st.write("✅ 匯率資料長度", len(usd_twd_df))
        
        merged = pd.merge(aapl_df, usd_twd_df, on="date", how="left")

        # st.write("✅ 合併後 preview", merged.head(10))
        # st.write("✅ 合併後匯率 NaN 數量：", merged["usd_to_twd"].isna().sum())

        merged[f"{symbol_name}_twd"] = merged[price_col_name] * merged["usd_to_twd"]
    
        # 中文資料表
        merged_zh = merged[["date", price_col_name, "usd_to_twd", f"{symbol_name}_twd"]].copy()
        merged_zh.columns = ["日期", "股價（美元)", "匯率", "股價（台幣)"]
        if volume_col_name in merged.columns:
            merged_zh["成交量"] = merged[volume_col_name]
    
        # 整理 plot_df ( 資料清洗與轉換 ) 
        price_col = f"{symbol_name}_twd"
        merged[price_col] = pd.to_numeric(merged[price_col], errors="coerce")
    
        plot_df = merged[["date", price_col]].copy()
        plot_df.rename(columns={price_col: "close"}, inplace=True)
    
        if volume_col_name in merged.columns:
            merged[volume_col_name] = pd.to_numeric(merged[volume_col_name], errors="coerce")
            plot_df["volume"] = merged[volume_col_name]
    
        # 丟掉 close 為空的資料（避免空圖）
        plot_df.dropna(subset=["close"], inplace=True)
    
        # 判斷資料是否為空
        if plot_df.empty:
            st.warning("⚠️ 無法顯示圖表：股價或匯率資料可能缺失，請確認資料是否齊全。")
        else:
            fig_twd = plot_price_volume(plot_df, title=f" {symbol_name} 台幣計價")
            st.plotly_chart(fig_twd, use_container_width=True)
    
        # 顯示表格
        st.subheader(f"📋 {symbol_name} 計價資料預覽")
        show_cols = ["日期", "股價（美元)", "匯率", "股價（台幣)"]
        if volume_col_name in merged.columns:
            show_cols.append("成交量")
        st.dataframe(merged_zh.tail(10)[show_cols], use_container_width=True)

if st.session_state.compare_mode:
    st.header("📈 多標的收盤價比較")

    all_symbol_options = list(symbols_df.itertuples(index=False))
    compare_selection = st.multiselect(
        "選擇要比較的標的（可跨類型多選）",
        all_symbol_options,
        default=[selected],
        format_func=lambda x: f"{x.name} ({x.symbol})"
    )

    if compare_selection:
        compare_data_list = []
        for item in compare_selection:
            temp_df = get_price_data(item.id, start_date, end_date)[["date", "close"]].copy()
            temp_df.rename(columns={"close": f"{item.symbol}"}, inplace=True)
            temp_df.set_index("date", inplace=True)
            compare_data_list.append(temp_df)

        merged_df = pd.concat(compare_data_list, axis=1).dropna()
        normalized_df = merged_df / merged_df.iloc[0] * 100

        fig_compare = go.Figure()
        for col in merged_df.columns:
            fig_compare.add_trace(go.Scatter(x=merged_df.index, y=merged_df[col], mode="lines", name=col))

        fig_compare.update_layout(
            title="📊 多標的收盤價比較",
            xaxis_title="日期",
            yaxis_title="收盤價",
            hovermode="x unified"
        )

        st.plotly_chart(fig_compare, use_container_width=True)
        st.subheader("📋 比較資料 (最後5筆)")
        st.dataframe(merged_df.tail(5), use_container_width=True)

    if st.button("🔙 返回單一標的分析"):
        st.session_state.compare_mode = False
        st.rerun()

# -----------------------------------
#            計算指標
# -----------------------------------

df_ind = load_data(selected.symbol)

ma_window = st.sidebar.selectbox("MA 期數", [5, 20, 60], index=1)
macd_window = st.sidebar.selectbox("MACD 期數", [9, 12, 26], index=1)

if not df_ind.empty:
    df_ind = indicators.calculate_ma(df_ind, window=ma_window)
    df_ind = indicators.calculate_rsi(df_ind, length=14)
    df_ind = indicators.calculate_macd(df_ind, base_period=macd_window)

    ma_col = f'MA{ma_window}'
    rsi_col = "rsi14"
    macd_col = 'macd'

    # st.write("👉 df_ind 欄位", df_ind.columns.tolist())
    st.subheader(f"📐 技術指標（{selected.name}）")
    st.line_chart(df_ind.set_index('date')[[macd_col, ma_col, rsi_col]])
else:
    st.warning("⚠️ 查無資料，請確認資料庫中是否有該標的歷史資料。")

