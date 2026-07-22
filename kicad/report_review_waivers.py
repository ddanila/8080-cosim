#!/usr/bin/env python3
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DRC = ROOT / "fab" / "gerbers" / "juku_routed-drc.json"
DEFAULT_OUT = ROOT / "fab" / "gerbers" / "review-waivers.md"

WAIVED_COUNTS = {
    "courtyards_overlap": 107,
    "pth_inside_courtyard": 0,
    "silk_over_copper": 199,
    "silk_overlap": 199,
    "text_thickness": 199,
}
WAIVER_RATIONALE = {
    "courtyards_overlap": "Dense authentic placement; assembly-fit review item, not a copper/routing fault.",
    "pth_inside_courtyard": "Dense authentic placement; through-hole/socket fit review item, not an electrical fault.",
    "silk_over_copper": "Silkscreen clipped by mask/copper; cosmetic unless assembly-critical marks become unreadable.",
    "silk_overlap": "Silkscreen-to-silkscreen overlap in dense labels/outlines; cosmetic assembly-readability item.",
    "text_thickness": "GOST/TrueType stroke warning; manufacturing-readability item, not fabrication geometry.",
}


def repo_relative(path):
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def table_row(values):
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def build_report(drc_path):
    drc = json.loads(drc_path.read_text())
    counts = Counter(v.get("type", "unknown") for v in drc.get("violations", []))
    unconnected = len(drc.get("unconnected_items", []))
    failures = []

    if unconnected:
        failures.append(f"Unconnected items are not waivable here: {unconnected}")

    for name, expected in WAIVED_COUNTS.items():
        actual = counts.get(name, 0)
        if actual != expected:
            failures.append(f"`{name}` count changed: expected {expected}, got {actual}")

    unexpected = sorted(set(counts) - set(WAIVED_COUNTS))
    if unexpected:
        failures.append(
            "Unexpected non-waived DRC type(s): "
            + ", ".join(f"`{name}`={counts[name]}" for name in unexpected)
        )

    accepted = not failures
    lines = [
        "# Main board DRC waiver review",
        "",
        f"Source DRC: `{repo_relative(drc_path)}`",
        f"Status: **{'ACCEPTED' if accepted else 'NOT ACCEPTED'}**",
        "",
        "This report is intentionally exact-count based. If the board changes and",
        "any remaining DRC count changes, the waiver must be reviewed again rather",
        "than silently carrying an old disposition forward.",
        "",
        "## Waived DRC Classes",
        "",
        "| Type | Count | Rationale |",
        "| --- | ---: | --- |",
    ]
    for name in sorted(WAIVED_COUNTS):
        lines.append(table_row([name, counts.get(name, 0), WAIVER_RATIONALE[name]]))

    lines.extend([
        "",
        "## Independent Gerber Render",
        "",
        "Independent render smoke command used for this package:",
        "",
        "```sh",
        "npx --yes @tracespace/cli --quiet --out=/tmp/juku-tracespace fab/gerbers/juku_routed-F_Cu.gtl fab/gerbers/juku_routed-B_Cu.gbl fab/gerbers/juku_routed-F_Mask.gts fab/gerbers/juku_routed-B_Mask.gbs fab/gerbers/juku_routed-F_Silkscreen.gto fab/gerbers/juku_routed-B_Silkscreen.gbo fab/gerbers/juku_routed-Edge_Cuts.gm1 fab/gerbers/juku_routed.drl",
        "```",
        "",
        "The automated order-readiness gate now runs",
        "`kicad/report_external_gerber_review.py`, which renders the same package",
        "through Tracespace and writes `fab/gerbers/external-gerber-review.md` plus",
        "top/bottom review screenshots.",
    ])

    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)

    lines.append("")
    return "\n".join(lines), accepted


def main():
    drc_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_DRC
    out_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else DEFAULT_OUT
    report, accepted = build_report(drc_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report)
    print(report)
    print(f"Wrote {repo_relative(out_path)}")
    return 0 if accepted else 3


if __name__ == "__main__":
    raise SystemExit(main())
