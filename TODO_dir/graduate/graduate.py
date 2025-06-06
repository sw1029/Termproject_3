import pdfplumber

with pdfplumber.open("pdf/2024.pdf") as pdf:
    page = pdf.pages[0]
    table = page.extract_table()
    for row in table:
        print(row)
