from pathlib import Path
import csv
import json
import re


FOLDER = Path(r"E:\huawei after\paper\谭斐然")
PREFIX_WIDTH = 24
PATTERN = re.compile(r"^(.+?\d{4})\s*-\s*(.+)$")


def aligned(filename: str) -> str:
    if not filename or not filename.lower().endswith(".pdf"):
        return filename
    stem = Path(filename).stem
    match = PATTERN.match(stem)
    if not match:
        return filename
    prefix, title = match.groups()
    return f"{prefix.strip():<{PREFIX_WIDTH}} - {title.strip()}.pdf"


def update_json(value):
    if isinstance(value, dict):
        return {key: aligned(item) if key == "filename" and isinstance(item, str) else update_json(item)
                for key, item in value.items()}
    if isinstance(value, list):
        return [update_json(item) for item in value]
    return value


def main():
    csv_path = next(FOLDER.glob("*.csv"))
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fields = list(rows[0].keys()) if rows else []
    for row in rows:
        row["filename"] = aligned(row.get("filename", ""))
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    json_path = next(FOLDER.glob("*.json"))
    data = json.loads(json_path.read_text(encoding="utf-8-sig"))
    json_path.write_text(json.dumps(update_json(data), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"CSV_ROWS={len(rows)}")
    print(f"CSV={csv_path.name}")
    print(f"JSON={json_path.name}")


if __name__ == "__main__":
    main()
