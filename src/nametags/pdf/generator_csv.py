import csv
from typing import TextIO

GeneratorRow = dict[str, str]
MAX_GENERATOR_ROWS = 5000
MAX_FIELD_LENGTH = 500
GENERATOR_TYPES = {"uones", "nuches", "ausimm", "nuwie", "student", "industry"}


def read_generator_csv_stream(csv_file: TextIO) -> list[GeneratorRow]:
    reader = csv.DictReader(csv_file)
    if reader.fieldnames is None:
        raise ValueError("CSV file does not contain a header row.")

    normalized_fields = [
        field.lstrip("\ufeff").strip().lower() for field in reader.fieldnames
    ]
    if len(normalized_fields) != len(set(normalized_fields)):
        raise ValueError("CSV column names must be unique.")
    field_map = dict(zip(normalized_fields, reader.fieldnames))
    required_columns = ("type", "name", "header")
    missing_columns = [column for column in required_columns if column not in field_map]
    if missing_columns:
        raise ValueError(
            f"CSV must contain type, name, and header columns. Missing: {', '.join(missing_columns)}"
        )

    rows: list[GeneratorRow] = []
    for raw_row in reader:
        row = {
            "type": (raw_row.get(field_map["type"]) or "").strip().casefold(),
            "name": (raw_row.get(field_map["name"]) or "").strip(),
            "header": (raw_row.get(field_map["header"]) or "").strip(),
        }
        if any(row.values()):
            if row["type"] not in GENERATOR_TYPES:
                raise ValueError(
                    f"CSV type must be one of: {', '.join(sorted(GENERATOR_TYPES))}."
                )
            if not row["name"] or not row["header"]:
                raise ValueError("CSV rows must contain type, name, and header values.")
            if any(len(value) > MAX_FIELD_LENGTH for value in row.values()):
                raise ValueError(
                    f"CSV fields must contain no more than {MAX_FIELD_LENGTH} characters."
                )
            rows.append(row)
            if len(rows) > MAX_GENERATOR_ROWS:
                raise ValueError(
                    f"CSV files may contain no more than {MAX_GENERATOR_ROWS} rows."
                )

    if not rows:
        raise ValueError("CSV does not contain any non-empty rows.")

    return rows
