from pathlib import Path


def merge_markdown_files(directory: Path, output_file: Path) -> None:
    lines: list[str] = []

    for file_path in directory.rglob("*.md"):
        if file_path == output_file:
            continue

        lines.append(f"\n\n# {file_path.name}\n\n")
        lines.append(file_path.read_text(encoding="utf-8"))

    output_file.write_text("".join(lines), encoding="utf-8")


if __name__ == "__main__":
    target_directory = "/home/cedric/code/auto-sat-control/docs/experiments/pipeline"
    output_file_path = Path(target_directory) / "merged.md"
    merge_markdown_files(Path(target_directory), output_file_path)