from pathlib import Path
import re


FOLDER = Path(r"E:\huawei after\paper\谭斐然")
PREFIX_WIDTH = 24
PATTERN = re.compile(r"^(.+?\d{4})\s*-\s*(.+)$")


def main():
    pdfs = sorted(FOLDER.glob("*.pdf"))
    planned = []
    for path in pdfs:
        match = PATTERN.match(path.stem)
        if not match:
            raise ValueError(f"无法识别会议年份前缀：{path.name}")
        prefix, title = match.groups()
        new_name = f"{prefix.strip():<{PREFIX_WIDTH}} - {title.strip()}.pdf"
        planned.append((path, path.with_name(new_name)))

    targets = [target.name.casefold() for _, target in planned]
    if len(targets) != len(set(targets)):
        raise ValueError("对齐后的文件名存在冲突，已停止重命名。")

    staged = []
    for index, (source, target) in enumerate(planned, start=1):
        temporary = source.with_name(f".__tan_paper_rename_{index:03d}__.tmp")
        source.rename(temporary)
        staged.append((temporary, target))
    for temporary, target in staged:
        temporary.rename(target)

    for _, target in planned:
        print(repr(target.name))
    print(f"RENAMED={len(planned)} PREFIX_WIDTH={PREFIX_WIDTH}")


if __name__ == "__main__":
    main()
