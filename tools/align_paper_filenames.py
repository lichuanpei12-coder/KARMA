from pathlib import Path


FOLDER = Path(r"E:\huawei after\paper\GPT基础推荐")
PREFIX_WIDTH = 20


def main():
    pdfs = sorted(FOLDER.glob("*.pdf"))
    planned = []
    for path in pdfs:
        if " - " in path.stem:
            prefix, title = path.stem.split(" - ", 1)
        elif "-" in path.stem:
            prefix, title = path.stem.split("-", 1)
        else:
            raise ValueError(f"无法识别文件名前缀：{path.name}")
        prefix = prefix.strip()
        title = title.strip()
        new_name = f"{prefix:<{PREFIX_WIDTH}} - {title}.pdf"
        planned.append((path, path.with_name(new_name)))

    targets = [target.name.casefold() for _, target in planned]
    if len(targets) != len(set(targets)):
        raise ValueError("对齐后的文件名存在冲突，已停止重命名。")

    # 两阶段改名，避免仅空格变化或大小写变化在 Windows 上发生冲突。
    staged = []
    for index, (source, target) in enumerate(planned, start=1):
        temporary = source.with_name(f".__paper_rename_{index:03d}__.tmp")
        source.rename(temporary)
        staged.append((temporary, target))
    for temporary, target in staged:
        temporary.rename(target)

    for _, target in planned:
        print(repr(target.name))
    print(f"RENAMED={len(planned)} PREFIX_WIDTH={PREFIX_WIDTH}")


if __name__ == "__main__":
    main()
