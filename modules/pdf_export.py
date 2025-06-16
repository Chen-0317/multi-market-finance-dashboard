from fpdf import FPDF
import io

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "財務報告", ln=True, align='C')

    def chapter_title(self, title):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, title, ln=True, align='L')
        self.ln(5)

    def chapter_body(self, text):
        self.set_font("Arial", "", 11)
        self.multi_cell(0, 10, text)
        self.ln()

def generate_pdf_report(acc_return, annual_return, volatility, mdd, fig):
    """
    產生包含報酬統計與圖表的 PDF，並回傳 BytesIO 物件
    """
    pdf = PDF()
    pdf.add_page()

    # 報酬統計區塊
    pdf.chapter_title("📊 報酬統計指標")
    pdf.chapter_body(
        f"""累積報酬率: {acc_return:.2%}
年化報酬率: {annual_return:.2%}
年化波動率: {volatility:.2%}
最大回落（MDD）: {mdd:.2%}"""
    )

    # 儲存圖表成圖片
    fig_path = "temp_chart.png"
    fig.write_image(fig_path)

    # 插入圖表圖片
    pdf.chapter_title("📈 價格走勢圖")
    pdf.image(fig_path, w=170)

    # 匯出 PDF 為 BytesIO（需用 encode）
    pdf_buffer = io.BytesIO()
    pdf_data = pdf.output(dest='S').encode('latin1')
    pdf_buffer.write(pdf_data)
    pdf_buffer.seek(0)

    return pdf_buffer
