import csv


GeneratorRow = dict[str, str]


def read_generator_csv(csv_path: str) -> list[GeneratorRow]:
    with open(csv_path, newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError("CSV file does not contain a header row.")

        field_map = {field.strip().lower(): field for field in reader.fieldnames}
        required_columns = ("top", "middle", "bottom")
        missing_columns = [column for column in required_columns if column not in field_map]
        if missing_columns:
            raise ValueError(
                f"CSV must contain top, middle, and bottom columns. Missing: {', '.join(missing_columns)}"
            )

        rows: list[GeneratorRow] = []
        for raw_row in reader:
            row = {
                "top": (raw_row.get(field_map["top"]) or "").strip(),
                "middle": (raw_row.get(field_map["middle"]) or "").strip(),
                "bottom": (raw_row.get(field_map["bottom"]) or "").strip(),
            }
            if any(row.values()):
                rows.append(row)

    if not rows:
        raise ValueError("CSV does not contain any non-empty rows.")

    return rows


def format_generator_csv_head(rows: list[GeneratorRow]) -> str:
    preview_rows = rows[:5]
    lines = ["top | middle | bottom"]
    for row in preview_rows:
        lines.append(f"{row['top']} | {row['middle']} | {row['bottom']}")
    if len(rows) > len(preview_rows):
        lines.append(f"... and {len(rows) - len(preview_rows)} more rows")
    return "\n".join(lines)