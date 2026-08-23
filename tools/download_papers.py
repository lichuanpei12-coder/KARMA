import csv
import json
import re
import time
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import quote

import requests


SOURCE = Path(r"C:\Users\Administrator\.codex\attachments\18c8bdfe-aecf-4d22-bc6f-cdd8e58838fb\pasted-text.txt")
DEST = Path(r"E:\huawei after\paper\谭斐然")
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "AcademicPaperCollector/1.0 (mailto:research@example.com)"})


def parse_titles(text):
    text = re.sub(r"\s+(?=\d+\.\s)", "\n", text.replace("●", ""))
    rows = []
    current = None
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r"(\d+)\.\s*(.*)", line)
        if m:
            if current:
                rows.append(current)
            current = [int(m.group(1)), m.group(2).strip()]
        elif current and line:
            current[1] += " " + line
    if current:
        rows.append(current)
    return rows


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").lower()
    return re.sub(r"[^a-z0-9]+", "", s)


def score(a, b):
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return 0
    return SequenceMatcher(None, na, nb).ratio()


def openalex(title):
    url = "https://api.openalex.org/works?search=" + quote(title) + "&per-page=10&select=id,doi,title,publication_year,primary_location,best_oa_location,locations,content_urls,type"
    data = SESSION.get(url, timeout=30).json()
    candidates = data.get("results", [])
    if not candidates:
        return None, 0
    best = max(candidates, key=lambda x: score(title, x.get("title")))
    return best, score(title, best.get("title"))


def semanticscholar(title):
    fields = "title,year,venue,publicationVenue,openAccessPdf,externalIds,url"
    url = "https://api.semanticscholar.org/graph/v1/paper/search?query=" + quote(title) + "&limit=10&fields=" + fields
    r = SESSION.get(url, timeout=30)
    if r.status_code != 200:
        return None, 0
    candidates = r.json().get("data", [])
    if not candidates:
        return None, 0
    best = max(candidates, key=lambda x: score(title, x.get("title")))
    return best, score(title, best.get("title"))


def venue_label(raw, doi=""):
    s = (raw or "").strip()
    low = s.lower()
    doi = (doi or "").lower()
    rules = [
        ("north american chapter of the association for computational linguistics", "NAACL"),
        ("empirical methods in natural language processing", "EMNLP"),
        ("annual meeting of the association for computational linguistics", "ACL"),
        ("international joint conference on natural language processing", "IJCNLP"),
        ("international conference on computational linguistics", "COLING"),
        ("computational linguistics", "CL"),
        ("world wide web conference", "WWW"),
        ("international conference on world wide web", "WWW"),
        ("web conference", "WWW"),
        ("international conference on learning representations", "ICLR"),
        ("neural information processing systems", "NeurIPS"),
        ("international conference on machine learning", "ICML"),
        ("association for computational linguistics", "ACL"),
        ("international conference on artificial intelligence and statistics", "AISTATS"),
        ("aaai conference on artificial intelligence", "AAAI"),
        ("international joint conference on artificial intelligence", "IJCAI"),
        ("conference on information and knowledge management", "CIKM"),
        ("international semantic web conference", "ISWC"),
        ("knowledge discovery and data mining", "KDD"),
        ("findings of", "FindingsACL"),
        ("arxiv", "arXiv"),
    ]
    for needle, label in rules:
        if needle in low:
            return label
    if "10.18653/v1/" in doi:
        code = doi.split("10.18653/v1/")[-1][:1]
        return {"p": "ACL", "d": "EMNLP", "n": "NAACL", "c": "COLING", "e": "EACL", "w": "ACLWorkshop"}.get(code, "ACL")
    if not s:
        return "arXiv"
    cleaned = re.sub(r"^(Proceedings of (the )?|The )", "", s, flags=re.I)
    cleaned = re.sub(r"\b(19|20)\d{2}\b", "", cleaned)
    cleaned = re.sub(r"[^A-Za-z0-9]+", "", cleaned)
    return cleaned[:35] or "Publication"


def safe_title(title):
    title = re.sub(r'[<>:"/\\|?*]', "-", title)
    title = re.sub(r"\s+", " ", title).strip().rstrip(".")
    return title[:175].rstrip()


def pdf_candidates(oa, ss):
    out = []
    if oa:
        for loc in [oa.get("best_oa_location"), oa.get("primary_location"), *(oa.get("locations") or [])]:
            if loc and loc.get("pdf_url"):
                out.append(loc["pdf_url"])
        content_urls = oa.get("content_urls") or {}
        if content_urls.get("pdf"):
            out.append(content_urls["pdf"])
    if ss and ss.get("openAccessPdf", {}).get("url"):
        out.append(ss["openAccessPdf"]["url"])
    unique = []
    for u in out:
        if u and u not in unique:
            unique.append(u.replace("http://aclanthology.org", "https://aclanthology.org"))
    return unique


def download_pdf(urls, path):
    errors = []
    for url in urls:
        try:
            r = SESSION.get(url, timeout=60, allow_redirects=True)
            ctype = r.headers.get("content-type", "").lower()
            if r.status_code == 200 and (r.content[:4] == b"%PDF" or "application/pdf" in ctype) and len(r.content) > 5000:
                path.write_bytes(r.content)
                return url, len(r.content), ""
            errors.append(f"{r.status_code}/{ctype}/{len(r.content)}:{url}")
        except Exception as e:
            errors.append(f"{type(e).__name__}:{url}")
    return "", 0, " | ".join(errors)[:600]


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    titles = parse_titles(SOURCE.read_text(encoding="utf-8-sig"))
    manifest = []
    for idx, title in titles:
        print(f"[{idx:02d}/{len(titles)}] {title}", flush=True)
        oa = ss = None
        oa_score = ss_score = 0
        try:
            oa, oa_score = openalex(title)
        except Exception as e:
            print("  OpenAlex error:", e, flush=True)
        time.sleep(0.12)
        if oa_score < 0.94 or not pdf_candidates(oa, None):
            try:
                ss, ss_score = semanticscholar(title)
            except Exception as e:
                print("  Semantic Scholar error:", e, flush=True)
            time.sleep(1.05)
        best_title = title
        year = None
        venue = ""
        doi = ""
        matched_score = 0
        if oa and oa_score >= 0.86:
            best_title = oa.get("title") or title
            year = oa.get("publication_year")
            doi = oa.get("doi") or ""
            loc = oa.get("primary_location") or {}
            venue = loc.get("raw_source_name") or ""
            matched_score = oa_score
        if ss and ss_score > matched_score:
            best_title = ss.get("title") or title
            year = ss.get("year") or year
            pv = ss.get("publicationVenue") or {}
            venue = pv.get("name") or ss.get("venue") or venue
            matched_score = ss_score
        urls = pdf_candidates(oa if oa_score >= 0.86 else None, ss if ss_score >= 0.86 else None)
        year = year or "UnknownYear"
        label = venue_label(venue, doi)
        filename = f"{label}{year}-{safe_title(title)}.pdf"
        path = DEST / filename
        used, size, err = download_pdf(urls, path)
        status = "downloaded" if used else ("not_found" if not urls else "download_failed")
        print(f"  {status}: {filename} (match={matched_score:.3f})", flush=True)
        manifest.append({
            "no": idx, "requested_title": title, "matched_title": best_title,
            "match_score": f"{matched_score:.3f}", "venue": venue, "year": year,
            "filename": filename if used else "", "status": status,
            "pdf_url": used, "candidate_urls": " | ".join(urls), "error": err,
        })
    fields = list(manifest[0].keys())
    with (DEST / "检索结果.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(manifest)
    (DEST / "检索结果.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({s: sum(1 for x in manifest if x["status"] == s) for s in {x["status"] for x in manifest}}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
