from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_pdf(data):
    file_name = "report.pdf"
    c = canvas.Canvas(file_name, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, y, "Career Readiness Report")

    c.setFont("Helvetica", 12)
    y -= 40

    for key, value in data.items():
        c.drawString(50, y, f"{key}: {value}")
        y -= 25

    c.save()
    return file_name
