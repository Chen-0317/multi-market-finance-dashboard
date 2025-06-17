import plotly.graph_objects as go

def plot_price_volume(df, title="價格走勢圖"):
    fig = go.Figure()

    # 收盤價折線圖
    fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["close"],
            mode="lines",
            name="收盤價",
            line=dict(color="#1f77b4")
        )
    )

    # 成交量長條圖（如有）
    if "volume" in df.columns:
        fig.add_trace(
            go.Bar(
                x=df["date"],
                y=df["volume"],
                name="成交量",
                yaxis="y2",
                opacity=0.3,
                marker_color="orange"
            )
        )

        fig.update_layout(
            yaxis2=dict(
                title="成交量",
                overlaying="y",
                side="right",
                showgrid=False,
                rangemode="tozero"
            ),
        )

    fig.update_layout(
        title=title,
        xaxis_title="日期",
        yaxis_title="價格",
        hovermode="x unified",
        legend=dict(
            x=1,
            y=1.05,
            xanchor="right",
            yanchor="bottom",
            orientation="h"
        ),
        margin=dict(l=40, r=40, t=80, b=80),
        height=600
    )
    
    return fig



#✅ 1. 使用 go.Bar 並指定 yaxis="y2" → 會導致 kaleido 或 fig.to_image() 失敗
#Plotly 的 subplot 或 overlaying="y" 類設定有時會讓 kaleido 無法正確 render 圖片（尤其是在導出成 PDF、PNG 時）。

#✅ 2. 中文標題（如 "價格走勢圖"）＋ 預設字型 Arial → 會讓 fpdf 導出 PDF 時卡住
#fpdf 預設不支援中文字（Arial 無中文），如果圖中包含中文字，會無法 render 字型。

