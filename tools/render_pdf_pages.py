from pathlib import Path

import pypdfium2 as pdfium


PDF = Path(r"E:\huawei after\KARMA\outputs\qa_literature_v3\自反馈开发信息抽取相关论文参考表.pdf")
OUT = PDF.parent

document = pdfium.PdfDocument(str(PDF))
for index in range(len(document)):
    page = document[index]
    bitmap = page.render(scale=2.0)
    image = bitmap.to_pil()
    image.save(OUT / f"page-{index + 1}.png")

print(len(document))
