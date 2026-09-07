import csv
from pathlib import Path

DEST = Path(r"E:\huawei after\paper\谭斐然")
csv_path = DEST / "检索结果.csv"
rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig")))

def prefix(venue, year, old):
    v = venue or ""
    if "Findings of the Association for Computational Linguistics" in v:
        if "EMNLP" in v: return f"FindingsEMNLP{year}"
        if "EACL" in v: return f"FindingsEACL{year}"
        if "ACL-IJCNLP" in v: return f"FindingsACL-IJCNLP{year}"
        return f"FindingsACL{year}"
    if "Language Resources and Evaluation Conference" in v:
        return f"LREC{year}"
    return old.split("-", 1)[0]

for row in rows:
    old = row.get("filename") or ""
    if not old or not (DEST / old).exists():
        continue
    p = prefix(row.get("venue"), row.get("year"), old)
    new = p + "-" + old.split("-", 1)[1]
    if new != old:
        (DEST / old).rename(DEST / new)
        row["filename"] = new
        print(old, "=>", new)

with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
