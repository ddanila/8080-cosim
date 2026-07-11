#!/usr/bin/python3
"""Report systematic footprint-placement residuals from unique solder snaps."""
import csv, math, re, statistics
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; ENDPOINTS=ROOT/"ref/photos/juku-pcb-2/endpoints.csv"
CSV_OUT=ROOT/"docs/photo-placement-residuals.csv"; MD_OUT=ROOT/"docs/photo-placement-residuals.md"
pattern=re.compile(r"projected \(([-0-9.]+),([-0-9.]+)\)"); groups=defaultdict(list); snapped=0
for row in csv.DictReader(ENDPOINTS.open(newline="")):
    if row["confidence"]!="registration+unique-hole-snap": continue
    snapped += 1
    match=pattern.search(row["note"])
    if match:
        ox,oy=map(float,match.groups()); groups[row["refdes"]].append((float(row["x_px"])-ox,float(row["y_px"])-oy,row["pin"]))
summary=[]
for ref,values in groups.items():
    dx=statistics.median(v[0] for v in values); dy=statistics.median(v[1] for v in values)
    rms=math.sqrt(sum((x-dx)**2+(y-dy)**2 for x,y,_ in values)/len(values)); mag=math.hypot(dx,dy)
    posture="review-translation" if len(values)>=3 and mag>=20 and rms<=12 else "insufficient/ambiguous"
    summary.append((ref,len(values),dx,dy,mag,rms,posture," ".join(pin for _,_,pin in values)))
summary.sort(key=lambda r:(-r[4],r[0]))
with CSV_OUT.open("w",newline="") as out:
    w=csv.writer(out); w.writerow(("refdes","snapped_pins","median_dx_px","median_dy_px","median_offset_px","rms_about_median_px","posture","pins"))
    for r in summary:w.writerow((r[0],r[1],*(f"{v:.3f}" for v in r[2:6]),r[6],r[7]))
status = "CANDIDATE GEOMETRY / REVIEW REQUIRED" if summary else "NO REPRODUCIBLE PLACEMENT RESIDUALS"
lines=["# Photo placement residual audit","",f"Status: **{status}**","",
f"The endpoint registry contains `{snapped}` unique-hole snaps, but only rows whose notes retain an explicit `projected (x,y)` baseline can produce a residual. Current calculable rows: `{sum(len(v) for v in groups.values())}`.",
"No row is electrical evidence and no placement is changed automatically.","",
"| Ref | Pins | dx px | dy px | Offset px | RMS px | Posture | Pin list |","| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |"]
for r in summary:lines.append(f"| {r[0]} | {r[1]} | {r[2]:.1f} | {r[3]:.1f} | {r[4]:.1f} | {r[5]:.1f} | {r[6]} | {r[7]} |")
lines += ["","`review-translation` requires at least three pins, >=20 px median displacement, and <=12 px RMS scatter. Review both-side source crops before editing KiCad."]
if not summary:
    lines += ["", "The former residual table is intentionally retired: its endpoint notes no longer preserve the projection origins needed to reproduce those offsets. Use validated package-local fits instead of the stale global-placement deltas."]
MD_OUT.write_text("\n".join(lines)+"\n"); print(f"wrote {MD_OUT.relative_to(ROOT)} and {CSV_OUT.relative_to(ROOT)} ({len(summary)} refs)")
