#!/usr/bin/env python3
import csv
import hashlib
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


GERBER_DRILL_FILES = [
    "gerbers/rev-a-physical-F_Cu.gtl",
    "gerbers/rev-a-physical-In1_Cu.g1",
    "gerbers/rev-a-physical-In2_Cu.g2",
    "gerbers/rev-a-physical-B_Cu.gbl",
    "gerbers/rev-a-physical-F_Mask.gts",
    "gerbers/rev-a-physical-B_Mask.gbs",
    "gerbers/rev-a-physical-F_Silkscreen.gto",
    "gerbers/rev-a-physical-B_Silkscreen.gbo",
    "gerbers/rev-a-physical-Edge_Cuts.gm1",
    "gerbers/rev-a-physical-job.gbrjob",
    "drill/rev-a-physical.drl",
]

UPLOAD_COPIES = [
    ("assembly/jlcpcb-bom-draft.csv", "upload/vjuga-rev-a-jlcpcb-bom.csv"),
    ("assembly/jlcpcb-cpl-draft.csv", "upload/vjuga-rev-a-jlcpcb-cpl.csv"),
    ("assembly/manual-assembly.csv", "upload/vjuga-rev-a-manual-assembly.csv"),
    ("assembly/post-assembly-insertion.csv", "upload/vjuga-rev-a-post-assembly-insertion.csv"),
    ("assembly/rev-a-assembly-orientation-notes.md", "upload/vjuga-rev-a-assembly-notes.md"),
]

ZIP_NAME = "upload/vjuga-rev-a-gerbers-drill.zip"
MANIFEST_NAME = "upload/package-manifest.md"
SHA256_NAME = "upload/SHA256SUMS.txt"
README_NAME = "upload/README-upload.md"
FIXED_ZIP_DATE = (1980, 1, 1, 0, 0, 0)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_files(out_dir, names):
    missing = []
    for name in names:
        path = out_dir / name
        if not path.exists() or path.stat().st_size == 0:
            missing.append(name)
    if missing:
        raise SystemExit("missing upload package inputs: " + ", ".join(missing))


def git_revision():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def csv_count(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def write_deterministic_zip(out_dir):
    zip_path = out_dir / ZIP_NAME
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in GERBER_DRILL_FILES:
            source = out_dir / name
            info = zipfile.ZipInfo(Path(name).name)
            info.date_time = FIXED_ZIP_DATE
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, source.read_bytes())
    return zip_path


def copy_upload_files(out_dir):
    copied = []
    for source_name, dest_name in UPLOAD_COPIES:
        source = out_dir / source_name
        dest = out_dir / dest_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        copied.append(dest)
    return copied


def write_readme(out_dir):
    path = out_dir / README_NAME
    lines = [
        "# VJUGA Rev A upload bundle",
        "",
        "Bare-PCB first-sample order:",
        "",
        "- Upload `vjuga-rev-a-gerbers-drill.zip` as the PCB fabrication archive.",
        "- Do not enable factory assembly for the first concept sample.",
        "- Do not upload the BOM/CPL files unless deliberately switching to the",
        "  optional assembled-board path.",
        "",
        "Do not upload `rev-a.engineering-bom.csv` as the assembly BOM. It is kept",
        "outside this upload directory because it records design intent and manual",
        "owner-supplied insertion notes, not the factory placement subset.",
        "",
        "The BOM/CPL, manual assembly list, post-assembly insertion list, and",
        "assembly notes are retained as reference material for a later assembled",
        "order. Review root `order-readiness.md` and SHA256 checksums before the",
        "bare-PCB order upload.",
        "",
    ]
    path.write_text("\n".join(lines))
    return path


def write_sha256(out_dir, files):
    path = out_dir / SHA256_NAME
    lines = []
    for file_path in sorted(files, key=lambda item: item.relative_to(out_dir).as_posix()):
        rel = file_path.relative_to(out_dir).as_posix()
        lines.append(f"{sha256(file_path)}  {rel}")
    path.write_text("\n".join(lines) + "\n")
    return path


def write_manifest(out_dir, files, sha_path):
    path = out_dir / MANIFEST_NAME
    bom_rows = csv_count(out_dir / "assembly/jlcpcb-bom-draft.csv")
    cpl_rows = csv_count(out_dir / "assembly/jlcpcb-cpl-draft.csv")
    manual_rows = csv_count(out_dir / "assembly/manual-assembly.csv")
    post_rows = csv_count(out_dir / "assembly/post-assembly-insertion.csv")

    lines = [
        "# VJUGA Rev A upload package manifest",
        "",
        f"Package: `{out_dir}`",
        f"Git revision: `{git_revision()}`",
        "",
        "## Upload Files",
        "",
        "| File | Bytes | SHA256 |",
        "| --- | ---: | --- |",
    ]
    for file_path in sorted(files, key=lambda item: item.relative_to(out_dir).as_posix()):
        rel = file_path.relative_to(out_dir).as_posix()
        lines.append(f"| `{rel}` | {file_path.stat().st_size} | `{sha256(file_path)}` |")
    lines.extend(
        [
            f"| `{sha_path.relative_to(out_dir).as_posix()}` | {sha_path.stat().st_size} | `{sha256(sha_path)}` |",
            "",
            "## Assembly Counts",
            "",
            f"- JLCPCB BOM rows: {bom_rows}",
            f"- JLCPCB CPL placements: {cpl_rows}",
            f"- Manual/non-factory rows: {manual_rows}",
            f"- Post-assembly insertions: {post_rows}",
            "",
            "## Upload Policy",
            "",
            "- Upload the Gerber/drill ZIP for PCB fabrication.",
            "- Select PCB fabrication only / no assembly for the first concept sample.",
            "- Keep the generated JLCPCB BOM/CPL CSV pair as later assembly references; do not upload them for the bare-PCB order.",
            "- Keep manual and post-assembly insertion files with the order notes.",
            "- Run independent Gerber review before order.",
            "",
        ]
    )
    path.write_text("\n".join(lines))
    return path


def main():
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "fab/minimal-vga")
    require_files(out_dir, GERBER_DRILL_FILES + [source for source, _ in UPLOAD_COPIES])
    shutil.rmtree(out_dir / "upload", ignore_errors=True)
    zip_path = write_deterministic_zip(out_dir)
    copied = copy_upload_files(out_dir)
    readme_path = write_readme(out_dir)
    upload_files = [zip_path, readme_path] + copied
    sha_path = write_sha256(out_dir, upload_files)
    manifest_path = write_manifest(out_dir, upload_files, sha_path)
    print(f"Wrote {zip_path}")
    print(f"Wrote {sha_path}")
    print(f"Wrote {manifest_path}")


if __name__ == "__main__":
    main()
