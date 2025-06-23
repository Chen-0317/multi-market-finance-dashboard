import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import json
import time
import sys
import os
import io
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.pdf_export import generate_pdf_report
from datetime import datetime, timedelta
from modules import auto_update, indicators
from modules.db_utils import get_symbols, get_price_data, load_data, save_user_preference
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

pricing_currency = st.sidebar.radio("計價幣別", ["台幣計價", "美元計價"])
if pricing_currency == "台幣計價":
    converted_currency = "TWD"
else:
    converted_currency = "USD"
    
if st.sidebar.button("📈 多標的比較"):
    st.session_state.compare_mode = True

with st.sidebar.popover("💾 儲存偏好設定(單一標的)"):
    st.markdown("### 選擇儲存格式")
    save_pref_format = st.radio("請選擇：", ["JSON", "SQLite"], horizontal=True)
    save_pref_btn = st.button("確認儲存")

with st.sidebar.popover("💾 匯出設定(單一標的)"):
    st.markdown("### 選擇匯出格式")
    export_format = st.radio("請選擇：", ["Excel", "PDF"], horizontal=True)
    export_btn = st.button("確認匯出")

        
df = get_price_data(selected.id, start_date, end_date)
aapl_df = df[["date", "close", "volume"]].copy()

# print(symbols_df["symbol"].unique())  # 看有哪些 symbol
# print(symbols_df[symbols_df["symbol"] == "USDTWD=X"])

symbols_df["symbol"] = symbols_df["symbol"].str.strip()
usdtwd_id = symbols_df[symbols_df["symbol"] == "USDTWD=X"]["id"].values[0]
# print(usdtwd_id)
# print(type(usdtwd_id))

usd_twd_df = get_price_data(int(usdtwd_id), start_date, end_date)
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

    if selected.region == "US" and selected.type == "stock":
        
        st.plotly_chart(plot_price_volume(df, title=selected.name), use_container_width=True)

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
        
        merged = pd.merge(aapl_df, usd_twd_df, on="date", how="left")

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
        
    elif selected.type in ["etf", "index", "currency"]:
        # 類似處理邏輯：適用於 ETF、指數、貨幣
        symbol_name = selected.name or selected.symbol
        price_col_name = f"{symbol_name}_usd"
        volume_col_name = f"{symbol_name}_volume"

        aapl_df.rename(columns={"close": price_col_name}, inplace=True)
        if "volume" in aapl_df.columns:
            aapl_df.rename(columns={"volume": volume_col_name}, inplace=True)

        aapl_df["date"] = pd.to_datetime(aapl_df["date"]).dt.date
        
        # st.write("symbols_df columns", symbols_df.columns.tolist())

        # 對欄位標準化與匯率表處理
        usd_twd_df.columns = [col.lower() for col in usd_twd_df.columns]
        if "adj_close" in usd_twd_df.columns:
            usd_twd_df.rename(columns={"adj_close": "usd_to_twd"}, inplace=True)
        elif "close" in usd_twd_df.columns:
            usd_twd_df.rename(columns={"close": "usd_to_twd"}, inplace=True)
        else:
            st.warning("⚠️ 無法找到 USD/TWD 匯率欄位")
            usd_twd_df = pd.DataFrame(columns=["date", "usd_to_twd"])
        
        # 時間欄位標準化
        usd_twd_df["date"] = pd.to_datetime(usd_twd_df["date"]).dt.date
        aapl_df["date"] = pd.to_datetime(aapl_df["date"]).dt.date
        
        # 合併資料
        merged = pd.merge(aapl_df, usd_twd_df, on="date", how="left")
        
        # 統一處理價格與成交量欄位名稱
        merged["price_twd"] = merged[price_col_name]
        merged["price_usd"] = merged["price_twd"] / merged["usd_to_twd"]
        
        if volume_col_name in merged.columns:
            merged[volume_col_name] = pd.to_numeric(merged[volume_col_name], errors="coerce")
        
        # 根據使用者選擇的幣別決定要顯示哪一個價格欄位
        if converted_currency == "TWD":
            price_col = "price_twd"
            currency_label = "價格（台幣）"
        else:
            price_col = "price_usd"
            currency_label = "價格（美元）"
        
        # 處理圖表資料
        merged[price_col] = pd.to_numeric(merged[price_col], errors="coerce")
        plot_df = merged[["date", price_col]].copy()
        plot_df.rename(columns={price_col: "close"}, inplace=True)
        
        if volume_col_name in merged.columns:
            plot_df["volume"] = merged[volume_col_name]
        
        plot_df.dropna(subset=["close"], inplace=True)
        
        # 繪圖
        if plot_df.empty:
            st.warning("⚠️ 無法顯示圖表：資料可能缺失")
        else:
            fig = plot_price_volume(plot_df, title=f"{symbol_name}（{currency_label}）")
            st.plotly_chart(fig, use_container_width=True)
        
        # 顯示資料表格
        merged_zh = merged[["date", price_col, "usd_to_twd"]].copy()
        merged_zh.columns = ["日期", currency_label, "匯率"]
        
        if volume_col_name in merged.columns:
            merged_zh["成交量"] = merged[volume_col_name]
        
        show_cols = ["日期", currency_label, "匯率"]
        if "成交量" in merged_zh.columns:
            show_cols.append("成交量")
        
        st.dataframe(merged_zh[show_cols].tail(10), use_container_width=True)



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

    st.subheader(f"📐 技術指標（{selected.name}）")
    st.line_chart(df_ind.set_index('date')[[macd_col, ma_col, rsi_col]])

    # --- 新增：計算報酬率指標 ---

    # 只要有收盤價 close 就能算，這裡用 df_ind 的 close
    df_ind = df_ind.dropna(subset=['close']).copy()
    df_ind['return'] = df_ind['close'].pct_change()

    # 累積報酬率
    cumulative_return = (1 + df_ind['return']).prod() - 1

    # 年化報酬率 (假設一年252交易日)
    total_days = (df_ind['date'].max() - df_ind['date'].min()).days
    annualized_return = (1 + cumulative_return) ** (252 / total_days) - 1 if total_days > 0 else np.nan

    # 年化波動率
    annualized_volatility = df_ind['return'].std() * np.sqrt(252)

    # 計算最大回落 (MDD)
    cumulative = (1 + df_ind['return']).cumprod()
    rolling_max = cumulative.cummax()
    drawdown = (cumulative - rolling_max) / rolling_max
    max_drawdown = drawdown.min()

    # 將結果整理成 DataFrame 方便繪圖
    stats_df = pd.DataFrame({
        "指標": ["累積報酬率", "年化報酬率", "年化波動率", "最大回落（MDD）"],
        "數值": [cumulative_return, annualized_return, annualized_volatility, max_drawdown]
    })

    # 畫圖
    fig_stats = go.Figure(go.Bar(
        x=stats_df["指標"],
        y=stats_df["數值"],
        text=stats_df["數值"].apply(lambda x: f"{x:.2%}"),
        textposition='auto',
        marker_color=['blue', 'green', 'orange', 'red']
    ))

    fig_stats.update_layout(
        title=f"{selected.name} 報酬率統計指標",
        yaxis_tickformat=".2%",
        yaxis_title="數值 (%)",
        xaxis_title="指標",
        margin=dict(t=40, b=40, l=40, r=40)
    )

    st.plotly_chart(fig_stats, use_container_width=True)

else:
    st.warning("⚠️ 查無資料，請確認資料庫中是否有該標的歷史資料。")

# -----------------------------------
#            儲存 Json & SQLite
# -----------------------------------

# 1. 取得價格資料與匯率資料
df = get_price_data(selected.id, start_date, end_date)
df_fx = get_price_data(int(usdtwd_id), start_date, end_date)

# 2. 日期轉換（確保一致性）
df["date"] = pd.to_datetime(df["date"]).dt.normalize()  
df_fx["date"] = pd.to_datetime(df_fx["date"]).dt.normalize()  

# 3. 保留匯率欄位並改名
df = df.dropna(subset=["close"])
df_fx = df_fx[["date", "close"]].rename(columns={"close": "usd_to_twd"})

# 4. 合併資料（left join，把匯率接到 df 上）
df_merged = pd.merge(df, df_fx, on="date", how="left")

# 5. 設定 index
df.set_index("date", inplace=True)

# 計算報酬率與統計
daily_returns = df["close"].pct_change().dropna()

acc_return = indicators.cumulative_return(daily_returns)
annual_return = indicators.annualized_return(daily_returns)
volatility = indicators.annualized_volatility(daily_returns)
mdd = indicators.max_drawdown(daily_returns)

stats_df = pd.DataFrame([{
    "指標": ["累積報酬率", "年化報酬率", "年化波動率", "最大回落（MDD）"],
    "數值": [acc_return, annual_return, volatility, mdd]
}]).explode(["指標", "數值"])

# ✅ 包含 日期、美元計價、匯率、台幣計價、成交量
merged_zh = df_merged.reset_index().copy()
merged_zh["Date"] = pd.to_datetime(merged_zh["date"]).dt.strftime("%Y-%m-%d")
merged_zh["Price_TWD"] = merged_zh["close"].round(1)

# 匯率欄位
if "usd_to_twd" not in merged_zh.columns:
    merged_zh["usd_to_twd"] = 0.0  # 若無匯率，補上預設值（或改為 np.nan）

merged_zh["ExchangeRate"] = merged_zh["usd_to_twd"].round(4)

merged_zh["Price_USD"] = (merged_zh["Price_TWD"] / merged_zh["ExchangeRate"]).round(1)

# 成交量欄位
if "volume" in merged_zh.columns:
    merged_zh["Volume"] = merged_zh["volume"].round(0).astype(int)
else:
    merged_zh["Volume"] = 0  # 或 np.nan

# 選出需要的 5 個欄位
merged_zh = merged_zh[["Date", "Price_USD", "ExchangeRate", "Price_TWD", "Volume"]]


# 點擊確認後執行儲存邏輯
PREF_DB_PATH = 'user_preferences.db'

if save_pref_btn:
    # 四個統計指標取小數點後 1 位
    user_pref = {
        "symbol": selected.symbol,
        "symbol_name": selected.name,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "currency": converted_currency,
        "category": category,
        "acc_return": round(acc_return, 1),
        "annual_return": round(annual_return, 1),
        "volatility": round(volatility, 1),
        "mdd": round(mdd, 1)
    }

    df_price = merged_zh.copy()

    # 將中文欄位名改成英文，方便匯出
    df_price.rename(columns={
        "日期": "Date",
        "股價（美元)": "Price_USD",
        "匯率": "ExchangeRate",
        "股價（台幣)": "Price_TWD",
        "成交量": "Volume"
    }, inplace=True)
    
    # 加入每日價格資料（merged_zh 已經有 Date / Price_USD / Volume）
    df_price = merged_zh.copy()
    df_price["Date"] = pd.to_datetime(df_price["Date"]).dt.strftime("%Y-%m-%d")
    df_price["Price_USD"] = df_price["Price_USD"].round(1)
    df_price["Price_TWD"] = df_price["Price_TWD"].round(1)
    df_price["ExchangeRate"] = df_price["ExchangeRate"].round(4)
    df_price["Volume"] = df_price["Volume"].round(0).astype(int)

    # 放入 JSON 中的 "price_data" 欄位
    user_pref["price_data"] = df_price.to_dict(orient="records")

    # 輸出 JSON 格式
    if save_pref_format == "JSON":
        json_str = json.dumps(user_pref, ensure_ascii=False, indent=2)
        st.sidebar.success("✅ 準備下載 JSON，請點下方按鈕")
        st.sidebar.download_button(
            label="⬇️ 點此下載 JSON",
            data=json_str,
            file_name="user_preference.json",
            mime="application/json"
        )

    # SQLite 儲存（可保留原寫法）
    elif save_pref_format == "SQLite":
        db_path = save_user_preference(user_pref)
        time.sleep(2)
        with open('data/user_preferences.db', 'rb') as f:
            db_data = f.read()
        st.sidebar.download_button(
            label="⬇️ 下載偏好設定 (SQLite)",
            data=db_data,
            file_name="user_preference.db",
            mime="application/octet-stream"
        )


# -----------------------------------
#            匯出 Excel / PDF
# -----------------------------------

if export_btn:
    if export_format == "PDF":
        if daily_returns is None or len(daily_returns) == 0:
            st.sidebar.error("⚠️ 無法匯出 PDF：daily_returns 沒有資料。")
        else:
            with st.spinner("📄 產生 PDF 中..."): 
                # print(f"type(fig) = {type(fig)}")
                # print(merged_zh.head(5).to_dict(orient="records"))
                pdf_data = generate_pdf_report(
                    acc_return, annual_return, volatility, mdd,
                    merged_zh
                )

            st.sidebar.success("✅ PDF 產生成功")
            st.sidebar.download_button(
                label="⬇️ 下載 PDF",
                data=pdf_data,
                file_name=f"{selected.symbol}_report.pdf",
                mime="application/pdf"
            )
    elif export_format == "Excel":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # 寫入報酬統計表
            stats_df.to_excel(writer, sheet_name='報酬統計', index=False)
            workbook = writer.book
            worksheet = writer.sheets['報酬統計']
            
            # 設定格式
            bold = workbook.add_format({'bold': True})
            percent_fmt = workbook.add_format({'num_format': '0.00%'})
            worksheet.set_column('A:A', 20, bold)
            worksheet.set_column('B:B', 18, percent_fmt)
    
            # 檢查是否有台幣價格與匯率欄位
            if "ExchangeRate" in merged_zh.columns and "Price_TWD" in merged_zh.columns:
                merged_zh = merged_zh[["Date", "Price_USD", "ExchangeRate", "Price_TWD", "Volume"]]
            else:
                merged_zh = merged_zh[["Date", "Price_USD", "Volume"]]

    
            # 寫入每日價格資料
            merged_zh.to_excel(writer, sheet_name='每日價格資料', index=False)
            worksheet2 = writer.sheets['每日價格資料']
            worksheet2.set_column(0, len(merged_zh.columns)-1, 15)
    
            for idx, col in enumerate(merged_zh.columns):
                worksheet2.set_column(idx, idx, 20)
        output.seek(0)
    
        st.sidebar.success("✅ 準備下載 Excel，請點下方按鈕")
        st.sidebar.download_button(
            label="⬇️ 匯出 Excel",
            data=output,
            file_name=f"{selected.symbol}_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# -----------------------------------
#            多標的收比較
# -----------------------------------

if st.session_state.compare_mode:
    st.header("📈 多標的指標比較")

    all_symbol_options = list(symbols_df.itertuples(index=False))
    compare_selection = st.multiselect(
        "選擇要比較的標的（可跨類型多選）",
        all_symbol_options,
        default=[selected],
        format_func=lambda x: f"{x.name} ({x.symbol})"
    )

    indicator_options = [
        "close", "rsi14", "MA5", "MA20", "MA60", "macd", 
        "累積報酬率", "年化報酬率", "年化波動率", "最大回落（MDD）"
    ]
    selected_indicator = st.selectbox("選擇要比較的指標", indicator_options, index=0)

    if compare_selection:
        result_dict = {}
        for item in compare_selection:
            df = get_price_data(item.id, start_date, end_date).copy()
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)
            df = df.dropna(subset=["close"])

            # 計算技術指標 (會自動加上 ma5, ma20, ma60, rsi14, macd...)
            df_ind = indicators.compute_indicators(df)

            if selected_indicator == "close":
                series = df_ind["close"]
                result_dict[item.symbol] = series

            elif selected_indicator == "rsi14":
                series = df_ind.get("rsi14")
                result_dict[item.symbol] = series

            elif selected_indicator.lower() in ["ma5", "ma20", "ma60"]:
                ma_col = selected_indicator.upper()  # "MA5", "MA20", ...
                series = df_ind.get(ma_col)
                if series is not None:
                    result_dict[item.symbol] = series

            elif selected_indicator == "macd":
                series = df_ind.get("macd")
                result_dict[item.symbol] = series

            elif selected_indicator == "累積報酬率":
                daily_returns = df_ind["close"].pct_change().dropna()
                cum_ret = indicators.cumulative_return(daily_returns)
                result_dict[item.symbol] = cum_ret

            elif selected_indicator == "年化報酬率":
                daily_returns = df_ind["close"].pct_change().dropna()
                ann_ret = indicators.annualized_return(daily_returns)
                result_dict[item.symbol] = ann_ret

            elif selected_indicator == "年化波動率":
                daily_returns = df_ind["close"].pct_change().dropna()
                ann_vol = indicators.annualized_volatility(daily_returns)
                result_dict[item.symbol] = ann_vol

            elif selected_indicator == "最大回落（MDD）":
                daily_returns = df_ind["close"].pct_change().dropna()
                mdd = indicators.max_drawdown(daily_returns)
                result_dict[item.symbol] = mdd

        if selected_indicator in ["close", "rsi14", "MA5", "MA20", "MA60", "macd"]:
            combined_df = pd.concat(result_dict.values(), axis=1)
            combined_df.columns = result_dict.keys()
            combined_df.dropna(how='all', inplace=True)

            fig = go.Figure()
            for col in combined_df.columns:
                fig.add_trace(go.Scatter(x=combined_df.index, y=combined_df[col], mode="lines", name=col))

            fig.update_layout(
                title=f"📊 多標的 {selected_indicator} 比較",
                xaxis_title="日期",
                yaxis_title=selected_indicator,
                hovermode="x unified"
            )
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("📋 比較資料 (最後5筆)")
            st.dataframe(combined_df.tail(5), use_container_width=True)

        else:
            summary_df = pd.DataFrame(result_dict, index=[0]).T
            summary_df.columns = [selected_indicator]

            st.subheader(f"📋 多標的 {selected_indicator} 比較")
            st.dataframe(summary_df, use_container_width=True)

            # 新增視覺化長條圖
            fig = go.Figure()
            for symbol, value in result_dict.items():
                fig.add_trace(go.Bar(
                    x=[symbol],
                    y=[value],
                    name=symbol,
                    text=f"{value:.2%}" if '報酬率' in selected_indicator else f"{value:.2f}",
                    textposition="auto"
                ))
        
            fig.update_layout(
                title=f"📊 多標的 {selected_indicator} 長條圖比較",
                xaxis_title="標的",
                yaxis_title=selected_indicator,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

    if st.button("🔙 關閉多標的分析"):
        st.session_state.compare_mode = False
        st.rerun()
