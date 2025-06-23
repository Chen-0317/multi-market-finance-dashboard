from fpdf import FPDF
import io
import tempfile
import plotly.io as pio
import os

# ✅ 指定字型路徑（微軟正黑體）
FONT_PATH_REGULAR = os.path.join(os.path.dirname(__file__), "../fonts/msjh.ttf")

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font("MSJH", "", FONT_PATH_REGULAR, uni=True) 
        self.set_font("MSJH", "", 12)

    def header(self):
        self.set_font("MSJH", "", 12)
        self.cell(0, 10, "財務報告", ln=True, align='C')

    def chapter_title(self, title):
        self.set_font("MSJH", "", 12)
        self.cell(0, 10, title, ln=True, align='L')
        self.ln(5)

    def chapter_body(self, text):
        self.set_font("MSJH", "", 11)
        self.multi_cell(0, 10, text)
        self.ln()

def generate_pdf_report(acc_return, annual_return, volatility, mdd, fig):
    print("🚀 開始產生 PDF")
    pdf = PDF()
    pdf.add_page()

    pdf.chapter_title("📊 報酬統計指標")
    pdf.chapter_body(
        f"""累積報酬率: {acc_return:.2%}
年化報酬率: {annual_return:.2%}
年化波動率: {volatility:.2%}
最大回落（MDD）: {mdd:.2%}"""
    )

    # 插入圖表
    try:
        print("📦 準備儲存圖表成圖片中...")
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_img:
            fig.write_image(tmp_img.name, width=1000, height=600, scale=2)
            tmp_path = tmp_img.name
            print(f"✅ 圖片儲存成功：{tmp_path}")

        pdf.chapter_title("📈 價格走勢圖")
        pdf.image(tmp_path, w=170)
        print("✅ 圖片插入成功")

    except Exception as e:
        print("❌ 圖片轉檔失敗：", e)
        raise

    # 匯出 PDF 為 BytesIO
    try:
        pdf_buffer = io.BytesIO()
        pdf_output = pdf.output(dest='S').encode('latin1')
        pdf_buffer.write(pdf_output)
        pdf_buffer.seek(0)
        print("🎉 PDF 產生成功")
        return pdf_buffer
    except Exception as e:
        print("❌ PDF 匯出失敗：", e)
        raise
