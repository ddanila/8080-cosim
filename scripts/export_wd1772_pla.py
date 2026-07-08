#!/usr/bin/env python3
"""Export the vendored WD1772 PLA/PLM table in normalized machine-readable forms."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from wd1772_pla import ROOT, SOURCE, parse_rows, sha256, validate_shape


OUTDIR = ROOT / "ref" / "wd1772-vg93"
OUT_JSON = OUTDIR / "wd1772pla.normalized.json"
OUT_CSV = OUTDIR / "wd1772pla.normalized.csv"
SUMS = OUTDIR / "SHA256SUMS"


def normalized_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rendered = []
    for row in rows:
        rendered.append(
            {
                "index": row["index"],
                "section": row["section"],
                "a_label": row["a"],
                "r_label": row["r"],
                "input_bits": row["inputs"],
                "output_bits": row["outputs"],
                "ambiguous_output_columns": row["ambiguous_output_columns"],
            }
        )
    return rendered


def write_json(rows: list[dict[str, object]], ignored: list[str], sections: int) -> None:
    input_widths, output_widths, input_chars, output_chars, rows_with_9, failures = validate_shape(
        rows,
        ignored,
    )
    if failures:
        raise SystemExit("; ".join(failures))
    payload = {
        "schema": "wd1772-pla-normalized-v1",
        "source": SOURCE.relative_to(ROOT).as_posix(),
        "source_sha256": sha256(SOURCE),
        "row_count": len(rows),
        "sections": sections,
        "input_width": input_widths[0],
        "output_width": output_widths[0],
        "input_alphabet": input_chars,
        "output_alphabet": output_chars,
        "ambiguous_rows": [
            {
                "index": row["index"],
                "a_label": row["a"],
                "r_label": row["r"],
                "ambiguous_output_columns": row["ambiguous_output_columns"],
                "output_bits": row["outputs"],
            }
            for row in rows_with_9
        ],
        "footer_guide_rows": ignored,
        "rows": normalized_rows(rows),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def write_csv(rows: list[dict[str, object]]) -> None:
    with OUT_CSV.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "index",
                "section",
                "a_label",
                "r_label",
                "input_bits",
                "output_bits",
                "ambiguous_output_columns",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for row in normalized_rows(rows):
            writer.writerow(
                {
                    **row,
                    "ambiguous_output_columns": ",".join(
                        str(index) for index in row["ambiguous_output_columns"]
                    ),
                }
            )


def write_sums() -> None:
    names = [
        "wd1772.pdf",
        "wd1772pla.txt",
        OUT_CSV.name,
        OUT_JSON.name,
    ]
    lines = [f"{sha256(OUTDIR / name)}  {name}" for name in names]
    SUMS.write_text("\n".join(lines) + "\n")


def main() -> int:
    rows, ignored, sections = parse_rows()
    write_json(rows, ignored, sections)
    write_csv(rows)
    write_sums()
    print(f"Wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"Wrote {OUT_CSV.relative_to(ROOT)}")
    print(f"Wrote {SUMS.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
