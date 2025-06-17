from fpdf import FPDF
from io import BytesIO
import os

def generate_pdf_report(acc_return, annual_return, volatility, mdd, fig, merged_zh):
    pdf = FPDF()
    pdf.add_page()

    # 字型路徑（msjh.ttf 放在 /fonts 資料夾下）
    font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fonts", "msjh.ttf"))
    pdf.add_font("MSJH", "", font_path, uni=True)
    pdf.set_font("MSJH", size=14)
    pdf.cell(200, 10, txt="財務報表", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("MSJH", size=12)
    pdf.cell(200, 10, txt=f"累積報酬率：{acc_return:.2%}", ln=True)
    pdf.cell(200, 10, txt=f"年化報酬率：{annual_return:.2%}", ln=True)
    pdf.cell(200, 10, txt=f"年化波動率：{volatility:.2%}", ln=True)
    pdf.cell(200, 10, txt=f"最大回落（MDD）：{mdd:.2%}", ln=True)

    # 匯出 Plotly 圖表為圖片（使用的是 plotly）
    img_buf = BytesIO()
    fig.write_image(img_buf, format="png")
    img_buf.seek(0)
    pdf.image(img_buf, x=10, y=None, w=180)

    # 表格資料
    pdf.ln(10)
    pdf.set_font("MSJH", size=10)
    pdf.cell(200, 10, txt="每日價格（前5筆）", ln=True)
    for _, row in merged_zh.head(5).iterrows():
        row_text = " / ".join([f"{col}：{str(row[col])}" for col in merged_zh.columns])
        pdf.multi_cell(0, 8, row_text)

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return BytesIO(pdf_bytes)
