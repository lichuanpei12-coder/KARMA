from pathlib import Path
import json
import re
import pypdfium2 as pdfium
from docx import Document

ROOT = Path(r"E:\huawei after\KARMA\GPT执行\Prompt工程学习报告_20260921")
DOCX = ROOT / "中英文Prompt与双语信息抽取专题学习笔记.docx"
PDF = ROOT / "bilingual_qa" / "bilingual.pdf"
doc = Document(DOCX)
gaps = []
for i, p in enumerate(doc.paragraphs):
    if p.style.name.startswith("Heading"):
        following = []
        for q in doc.paragraphs[i + 1:]:
            if q.style.name.startswith("Heading"):
                break
            if q.text.strip():
                following.append(q.text)
        if not following:
            gaps.append(p.text)
assert not gaps, gaps
whole = "\n".join(p.text for p in doc.paragraphs)
assert "turn35" not in whole
assert whole.count("R1 ") == 2
assert whole.count("R8 ") == 2
document = pdfium.PdfDocument(str(PDF))
details = []
for i in range(len(document)):
    page = document[i]
    page.render(scale=1.5).to_pil().save(PDF.parent / f"page-{i + 1:03d}.png")
    text = page.get_textpage().get_text_range()
    details.append({"page": i + 1, "chars": len(text), "start": text[:110], "end": text[-160:]})
print(json.dumps({"page_count": len(document), "heading_count": sum(p.style.name.startswith("Heading") for p in doc.paragraphs), "table_count": len(doc.tables), "pages": details}, ensure_ascii=True, indent=2))
