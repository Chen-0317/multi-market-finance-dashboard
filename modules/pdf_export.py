import os
import matplotlib
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from fpdf import FPDF
from io import BytesIO
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        font_path = os.path.join(os.path.dirname(__file__), "../fonts/msjh.ttf")
        self.add_font("MSJH", "", font_path, uni=True)
        self.set_font("MSJH", "", 12)

def safe_str(val):
    if val is None:
        return ""
    if isinstance(val, (float, int)):
        # 把浮點數改用千分位 + 整數顯示，縮短長度
        return f"{val:,.0f}"
    try:
        s = str(val)
        return "".join(c for c in s if c.isprintable())
    except:
        return ""

def format_volume(val):
    try:
        # 整數顯示，千分位分隔符號，字串長度短
        return f"{int(val):,}"
    except Exception:
        return str(val)

def format_price(val):
    try:
        return f"{val:.1f}"  # 小數點第一位
    except Exception:
        return str(val)

def generate_pdf_report(acc_return, annual_return, volatility, mdd, merged_zh):
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("MSJH", "", 12)

    # 統計數據 - 使用 cell 寬度固定，並對齊冒號
    stats = [
        ("累積報酬率", acc_return),
        ("年化報酬率", annual_return),
        ("波動率", volatility),
        ("最大回撤", mdd)
    ]
    for label, val in stats:
        # 左邊欄位固定寬度 40，數值靠右對齊 30，整行寬度合適
        pdf.cell(40, 10, f"{label}：", ln=False)
        pdf.cell(30, 10, f"{val:.2%}", ln=True, align="R")

    pdf.ln(5)
    pdf.cell(0, 10, "近期資料（摘要）", ln=True)

    # 針對每筆資料做欄位排版，建議每行兩欄，每欄寬度約80
    for _, row in merged_zh.iterrows():
        row_texts = []
        for col in merged_zh.columns:
            val = row[col]
            if col.lower() == "volume":
                text = format_volume(val)
            elif col.lower() == "price_usd":
                text = format_price(val)
            else:
                text = str(val)
            # 限制欄位字串長度避免超寬
            text = text[:20]
            row_texts.append(f"{col}：{text}")

        for i in range(0, len(row_texts), 3):
            left = row_texts[i]
            middle = row_texts[i+1] if i+1 < len(row_texts) else ""
            right = row_texts[i+2] if i+2 < len(row_texts) else ""
            pdf.cell(60, 8, left, ln=False)
            pdf.cell(60, 8, middle, ln=False)
            pdf.cell(60, 8, right, ln=True)

    # ✅ 新增：繪製 Matplotlib 圖表（如價格走勢圖）
    merged_zh["Date"] = pd.to_datetime(merged_zh["Date"])

    fig, ax = plt.subplots(figsize=(6, 3))  # 寬6英寸、高3英寸

    font_path = os.path.join(os.path.dirname(__file__), "../fonts/msjh.ttf")
    my_font = font_manager.FontProperties(fname=font_path)
    matplotlib.rcParams['font.family'] = my_font.get_name()

    if "Date" in merged_zh.columns and "Price_TWD" in merged_zh.columns:
        ax.plot(merged_zh["Date"], merged_zh["Price_TWD"], linewidth=1)
        ax.set_title("價格走勢圖（Price_TWD）", fontproperties=my_font)
        ax.set_xlabel("日期", fontproperties=my_font)
        ax.set_ylabel("價格（台幣）", fontproperties=my_font)
        ax.tick_params(axis="x", rotation=45)
        ax.grid(True)

        # 格式化 y 軸價格
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"${x:.1f}"))

        # 設置 X 軸日期格式 - 以月為主，標籤以季度顯示
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))  # 每3個月一標
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

        # 把圖儲存到 BytesIO
        buf = BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format="PNG")
        buf.seek(0)


         # 圖片前換頁判斷
        if pdf.get_y() + 80 > 270:
            pdf.add_page()
            pdf.set_font("MSJH", "", 12)
            
        # 插入圖片進 PDF
        pdf.image(buf, x=10, y=pdf.get_y() + 10, w=180)
        buf.close()
        plt.close(fig)
    else:
        if pdf.get_y() + 10 > 270:
            pdf.add_page()
            pdf.set_font("MSJH", "", 12)
        pdf.cell(0, 10, "⚠️ 無法繪製價格走勢圖：缺少 'Date' 或 'Price_TWD' 欄位", ln=True)

    return BytesIO(pdf.output(dest="S"))