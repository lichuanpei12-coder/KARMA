import csv
import re
import time
from pathlib import Path
from urllib.parse import quote

import requests

DEST = Path(r"E:\huawei after\paper\谭斐然")
S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0 Academic research downloader"})

MANUAL = {
    1: ("WWW2013", "http://archives.iw3c2.org/www2013/proceedings/p355.pdf"),
    6: ("TALLIP2018", "https://www.researchgate.net/profile/Shengbin-Jia/publication/323198509_Chinese_Open_Relation_Extraction_and_Knowledge_Base_Establishment/links/5ad80644aca272fdaf802ff1/Chinese-Open-Relation-Extraction-and-Knowledge-Base-Establishment.pdf"),
    2: ("IJCAI2007", "https://www.ijcai.org/Proceedings/07/Papers/429.pdf"),
    3: ("IJCAI2011", "https://www.ijcai.org/Proceedings/11/Papers/012.pdf"),
    13: ("WSDM2024", "https://arxiv.org/pdf/2401.11107"),
    14: ("FindingsEMNLP2023", "https://aclanthology.org/2023.findings-emnlp.869.pdf"),
    20: ("COLING2025", "https://aclanthology.org/2025.coling-main.227.pdf"),
    22: ("WWW2025", "https://arxiv.org/pdf/2412.20005"),
    23: ("XLLM2025", "https://aclanthology.org/2025.xllm-1.28.pdf"),
    25: ("arXiv2025", "https://arxiv.org/pdf/2509.20900"),
    27: ("ICLR2023", "https://arxiv.org/pdf/2210.03629"),
    30: ("AAAI2026", "https://arxiv.org/pdf/2511.13118"),
    33: ("AAAI2026", "https://arxiv.org/pdf/2603.02909"),
    39: ("ICML2026", "https://arxiv.org/pdf/2507.21892"),
    41: ("ACL2026", "https://arxiv.org/pdf/2603.06915"),
    42: ("AAAI2026", "https://arxiv.org/pdf/2511.19083"),
    44: ("AAAI2025", "https://arxiv.org/pdf/2412.07289"),
    57: ("ACL2026", "https://aclanthology.org/2026.acl-long.1952.pdf"),
    54: ("TACL2024", "https://arxiv.org/pdf/2401.01183"),
    59: ("EMNLP2025", "https://aclanthology.org/2025.emnlp-main.783.pdf"),
}


def safe(s):
    return re.sub(r'[<>:"/\\|?*]', "-", re.sub(r"\s+", " ", s).strip()).rstrip(".")[:175]


def get_pdf(url):
    last = ""
    for _ in range(3):
        try:
            r = S.get(url, timeout=90, allow_redirects=True)
            if r.status_code == 200 and r.content[:4] == b"%PDF" and len(r.content) > 5000:
                return r.content, ""
            last = f"HTTP {r.status_code}, {r.headers.get('content-type')}, {len(r.content)} bytes"
        except Exception as e:
            last = repr(e)
        time.sleep(2)
    return None, last


def acl_from_openalex(title):
    url = "https://api.openalex.org/works?search=" + quote(title) + "&per-page=5&select=title,doi,publication_year"
    try:
        data = S.get(url, timeout=30).json().get("results", [])
        for x in data:
            doi = (x.get("doi") or "").lower()
            if "10.18653/v1/" in doi:
                aid = doi.split("10.18653/v1/")[-1]
                return f"https://aclanthology.org/{aid}.pdf", x.get("publication_year")
    except Exception:
        pass
    return None, None


rows = list(csv.DictReader((DEST / "检索结果.csv").open(encoding="utf-8-sig")))
for row in rows:
    no = int(row["no"])
    if row["status"].startswith("downloaded"):
        continue
    title = row["requested_title"]
    item = MANUAL.get(no)
    if not item:
        acl, year = acl_from_openalex(title)
        if acl:
            item = (f"ACL{year}", acl)
    if not item:
        continue
    prefix, url = item
    filename = f"{prefix}-{safe(title)}.pdf"
    content, err = get_pdf(url)
    if content:
        (DEST / filename).write_bytes(content)
        row.update(status="downloaded_second_pass", filename=filename, pdf_url=url, error="")
        print("downloaded", no, filename, flush=True)
    else:
        row["error"] = (row.get("error", "") + " | second pass: " + err).strip(" |")
        print("failed", no, err, flush=True)

with (DEST / "检索结果.csv").open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
