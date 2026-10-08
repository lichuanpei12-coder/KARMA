from pathlib import Path
import importlib.util, os
base = Path(__file__).resolve().parent
runtime = Path(r'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies')
os.environ['PATH'] = str(runtime / 'native/poppler/Library/bin') + os.pathsep + os.environ.get('PATH','')
renderer = Path(r'C:\Users\Administrator\.codex\plugins\cache\openai-primary-runtime\documents\26.909.61513\skills\documents\render_docx.py')
spec = importlib.util.spec_from_file_location('render_docx', renderer)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
pdf = base / 'QA/preview.pdf'
module.convert_to_pdf = lambda *args, **kwargs: (str(pdf), 'Word export used because bundled LibreOffice is unavailable')
pages = module.rasterize(str(next(base.glob('*.docx'))), str(base/'QA'), 120, False, False)
from pypdf import PdfReader
for i,p in enumerate(PdfReader(pdf).pages,1):
    lines = p.extract_text().splitlines()
    print(i, len(lines), ascii(lines[:2]), ascii(lines[-2:]))
print('Pages:', len(pages))
