from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

fonts_path = settings.BASE_DIR / 'utils' / 'fonts'
file_path = settings.BASE_DIR / 'utils' / 'pdf_gen'

pdfmetrics.registerFont(TTFont('regular', fonts_path / 'Kanit-Cyrillic.ttf'))


def write_pdf(pdf, data):
    x, y = 40 * mm, 210 * mm
    page_number = 1
    pdf.setFont('regular', 10)
    for ingridient in data:
        if y <= 10:
            pdf.setFont('regular', 5)
            pdf.drawString(5, 5, f'Стр. {page_number}')
            page_number += 1
            pdf.showPage()
            pdf.setFont('regular', 10)
            y = 290 * mm
        pdf.drawString(x, y, (
            f'{ingridient.name}, '
            f'{data[ingridient]}({ingridient.measurement_unit})')
        )
        pdf.rect(x - 7 * mm, y - 1 * mm, 5 * mm, 5 * mm, fill=0)
        y -= 10 * mm


def get_pdf(data):
    pdf = canvas.Canvas(filename='ShoppingCatrt.pdf', pagesize=A4)
    pdf.drawInlineImage(f'{file_path}/Logo.png', 100 * mm, 0)
    pdf.drawInlineImage(f'{file_path}/favicon.png', 0, 260 * mm)
    pdf.setFont('regular', 20)
    pdf.drawString(50 * mm, 240 * mm, 'Список покупок для рецептов')
    pdf.setFont('regular', 15)
    pdf.drawString(50 * mm, 230 * mm, (
        f'Всего к покупке: {len(data)} ингридиент(a-ов)'))
    write_pdf(pdf, data)
    pdf.save()
    return pdf._filename
