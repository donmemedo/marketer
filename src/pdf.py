import datetime

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from bidi.algorithm import get_display
import arabic_reshaper
from khayyam import JalaliDatetime as jd

def pdf_maker(args):


    pdfmetrics.registerFont(TTFont("BNazanin", "BNazanin.ttf"))
    styles = getSampleStyleSheet()
    right = ParagraphStyle(
        "border",  # border on
        parent=styles["Normal"],  # Normal is a defaul style  in  getSampleStyleSheet
        borderColor="#333333",
        borderWidth=1,
        borderPadding=6,
        fontName="BNazanin",
        alignment=2
        # previously we named our custom font "Arabic"
    )
    left = ParagraphStyle(
        "border",  # border on
        parent=styles["Normal"],  # Normal is a defaul style  in  getSampleStyleSheet
        borderColor="#333333",
        borderWidth=1,
        borderPadding=6,
        fontName="BNazanin",
        alignment=0
        # previously we named our custom font "Arabic"
    )
    cent = ParagraphStyle(
        "border",  # border on
        parent=styles["Normal"],  # Normal is a defaul style  in  getSampleStyleSheet
        borderColor="#333333",
        borderWidth=1,
        borderPadding=6,
        fontName="Bnazanin",
        alignment=1
        # previously we named our custom font "Arabic"
    )
    storys = []


    text1 = "محاسبات صورتحساب بازاریاب"

    shobe = args.shobe# "تهران"
    name = args.name# "خواجه زاده"
    doreh = jd(datetime.strptime(args.doreh, '%Y-%m-%d')).monthname()# "بهمن"

    doreh2 = jd(datetime.strptime(args.doreh, '%Y-%m-%d')).monthname(-2)# "آبان"
    total_fee=args.total_fee
    pure_fee=args.pure_fee
    marketer_fee=args.marketer_fee
    tax=args.tax
    colat2 = args.colat2
    colat = args.colat
    mandeh=args.mandeh
    pardakhti = args.pardakhti# 1000
    date = args.date#"2023-03-01"
    # date= reversed(date)
    text2 = f"شعبه: {shobe}  نام بازاریاب:{name}  دوره پرداخت: {doreh} 1401"

    text31 = f"کارمزد ساخته شده مشتریان در {doreh}"
    text22 = f" {total_fee}"

    text41 = f"کارمزد خالص در {doreh}"
    text32 = f" {pure_fee}"

    text51 = f"سهم نماینده در {doreh}"
    text42 = f" {marketer_fee}"

    text6 = f"اضافه می‌شود:"
    text7 = f"برگشت حسن انجام کار در {doreh2}"
    text62 = f" {colat2}"


    text8 = f"کسر می‌شود:"
    text9 = f"مانده قبل"
    text82 = f" {mandeh}"

    text10 = f"حسن انجام کار {doreh}"
    text92 = f" {colat}"

    text11 = f"مالیات سهم نماینده در {doreh}"
    text102 = f" {tax}"

    text12 = f"قابل پرداخت {pardakhti}"
    text112 = f" {pardakhti}"

    text13 = f"تاریخ صدور: {date}"
    text122 = f" {pardakhti}"


    # reshape the text
    rehaped_text1 = arabic_reshaper.reshape(text1)
    bidi_text1 = get_display(rehaped_text1)
    storys.append(Paragraph(bidi_text1, cent))
    storys.append(Spacer(1, 12))  # set the space here

    rehaped_text2 = arabic_reshaper.reshape(text2)
    bidi_text2 = get_display(rehaped_text2)
    storys.append(Paragraph(bidi_text2, cent))
    storys.append(Spacer(1, 12))  # set the space here

    rehaped_text22 = arabic_reshaper.reshape(text22)
    bidi_text22 = get_display(rehaped_text22)
    storys.append(Paragraph(bidi_text22, left))
    storys.append(Spacer(1, -12))  # set the space here

    rehaped_text31 = arabic_reshaper.reshape(text31)
    bidi_text31 = get_display(rehaped_text31)
    storys.append(Paragraph(bidi_text31, right))
    storys.append(Spacer(1, 12))  # set the space here

    rehaped_text32 = arabic_reshaper.reshape(text32)
    bidi_text32 = get_display(rehaped_text32)
    storys.append(Paragraph(bidi_text32, left))
    storys.append(Spacer(1, -12))  # set the space here

    rehaped_text41 = arabic_reshaper.reshape(text41)
    bidi_text41 = get_display(rehaped_text41)
    storys.append(Paragraph(bidi_text41, right))
    storys.append(Spacer(1, 12))  # set the space here

    rehaped_text42 = arabic_reshaper.reshape(text42)
    bidi_text42 = get_display(rehaped_text42)
    storys.append(Paragraph(bidi_text42, left))
    storys.append(Spacer(1, -12))  # set the space here

    rehaped_text51 = arabic_reshaper.reshape(text51)
    bidi_text51 = get_display(rehaped_text51)
    storys.append(Paragraph(bidi_text51, right))
    storys.append(Spacer(1, 12))  # set the space here

    rehaped_text6 = arabic_reshaper.reshape(text6)
    bidi_text6 = get_display(rehaped_text6)
    storys.append(Paragraph(bidi_text6, right))
    storys.append(Spacer(1, 12))  # set the space here

    rehaped_text62 = arabic_reshaper.reshape(text62)
    bidi_text62 = get_display(rehaped_text62)
    storys.append(Paragraph(bidi_text62, left))
    storys.append(Spacer(1, -12))  # set the space here

    rehaped_text7 = arabic_reshaper.reshape(text7)
    bidi_text7 = get_display(rehaped_text7)
    storys.append(Paragraph(bidi_text7, right))
    storys.append(Spacer(1, 12))  # set the space here

    rehaped_text8 = arabic_reshaper.reshape(text8)
    bidi_text8 = get_display(rehaped_text8)
    storys.append(Paragraph(bidi_text8, right))
    storys.append(Spacer(1, 12))  # set the space here

    rehaped_text82 = arabic_reshaper.reshape(text82)
    bidi_text82 = get_display(rehaped_text82)
    storys.append(Paragraph(bidi_text82, left))
    storys.append(Spacer(1, -12))  # set the space here

    rehaped_text9 = arabic_reshaper.reshape(text9)
    bidi_text9 = get_display(rehaped_text9)
    storys.append(Paragraph(bidi_text9, right))
    storys.append(Spacer(1, 12))  # set the space here

    rehaped_text92 = arabic_reshaper.reshape(text92)
    bidi_text92 = get_display(rehaped_text92)
    storys.append(Paragraph(bidi_text92, left))
    storys.append(Spacer(1, -12))  # set the space here


    rehaped_text10 = arabic_reshaper.reshape(text10)
    bidi_text10 = get_display(rehaped_text10)
    storys.append(Paragraph(bidi_text10, right))
    storys.append(Spacer(1, 12))  # set the space here

    rehaped_text102 = arabic_reshaper.reshape(text102)
    bidi_text102 = get_display(rehaped_text102)
    storys.append(Paragraph(bidi_text102, left))
    storys.append(Spacer(1, -12))  # set the space here


    rehaped_text11 = arabic_reshaper.reshape(text11)
    bidi_text11 = get_display(rehaped_text11)
    storys.append(Paragraph(bidi_text11, right))
    storys.append(Spacer(1, 12))  # set the space here

    rehaped_text112 = arabic_reshaper.reshape(text112)
    bidi_text112 = get_display(rehaped_text112)
    storys.append(Paragraph(bidi_text112, left))
    storys.append(Spacer(1, -12))  # set the space here

    rehaped_text12 = arabic_reshaper.reshape(text12)
    bidi_text12 = get_display(rehaped_text12)
    storys.append(Paragraph(bidi_text12, right))
    storys.append(Spacer(1, 12))  # set the space here

    # rehaped_text122 = arabic_reshaper.reshape(text122)
    # bidi_text122 = get_display(rehaped_text122)
    # storys.append(Paragraph(bidi_text122,left))
    # storys.append(Spacer(1,-12)) # set the space here

    rehaped_text13 = arabic_reshaper.reshape(text13)
    bidi_text13 = get_display(rehaped_text13)
    storys.append(Paragraph(bidi_text13, cent))
    # storys.append(Spacer(1,12)) # set the space here
    #
    # rehaped_text14 = arabic_reshaper.reshape(text14)
    # bidi_text14 = get_display(rehaped_text14)
    # storys.append(Paragraph(bidi_text14,right))
    # storys.append(Spacer(1,12)) # set the space here
    #
    # rehaped_text15 = arabic_reshaper.reshape(text15)
    # bidi_text15 = get_display(rehaped_text15)
    # storys.append(Paragraph(bidi_text15,right))
    # storys.append(Spacer(1,12)) # set the space here
    #
    # rehaped_text16 = arabic_reshaper.reshape(text16)
    # bidi_text16 = get_display(rehaped_text16)
    # storys.append(Paragraph(bidi_text16,right))
    # storys.append(Spacer(1,12)) # set the space here

    # add the text to pdf
    doc = SimpleDocTemplate("mydoc.pdf", pagesize=letter)
    ## add the storys array to the pdf document
    doc.build(storys)
