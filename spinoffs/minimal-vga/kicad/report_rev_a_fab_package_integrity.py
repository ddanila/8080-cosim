#!/usr/bin/env python3
import hashlib
import importlib.util
import json
import sys
import zipfile
from pathlib import Path


PACKAGER_PATH = Path(__file__).with_name("package_rev_a_upload.py")


def load_packager():
    spec = importlib.util.spec_from_file_location("package_rev_a_upload", PACKAGER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_sha256sums(path):
    entries = {}
    if not path.exists():
        return entries
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        digest, name = line.split(None, 1)
        entries[name.strip()] = digest
    return entries


def table_row(values):
    return "| " + " | ".join(str(value).replace("|", "/") if value else "-" for value in values) + " |"


def marker_for(name):
    if name.endswith(".drl"):
        return ["M48", "METRIC", "T"]
    if name.endswith(".gbrjob"):
        return ["Header", "GeneralSpecs", "FilesAttributes"]
    markers = ["%TF.GenerationSoftware,KiCad", "%FSLAX46Y46*%", "%MOMM*%"]
    if "Edge_Cuts" in name:
        markers.append("%TF.FileFunction,Profile")
    elif "_Cu." in name:
        markers.append("%TF.FileFunction,Copper")
    elif "_Mask." in name:
        markers.append("%TF.FileFunction,Soldermask")
    elif "_Silkscreen." in name:
        markers.append("%TF.FileFunction,Legend")
    return markers


def zip_member_ok(info):
    return (
        info.date_time == (1980, 1, 1, 0, 0, 0)
        and not info.filename.startswith("/")
        and ".." not in Path(info.filename).parts
        and info.compress_type == zipfile.ZIP_DEFLATED
    )


def build_report(out_dir):
    packager = load_packager()
    zip_path = out_dir / packager.ZIP_NAME
    sha_path = out_dir / packager.SHA256_NAME
    manifest_path = out_dir / packager.MANIFEST_NAME
    expected_sources = [out_dir / name for name in packager.GERBER_DRILL_FILES]
    expected_zip_names = [Path(name).name for name in packager.GERBER_DRILL_FILES]
    expected_upload_files = [
        packager.ZIP_NAME,
        packager.README_NAME,
        *(dest for _, dest in packager.UPLOAD_COPIES),
    ]

    failures = []
    file_rows = []
    marker_failures = []

    for source in expected_sources:
        rel = source.relative_to(out_dir).as_posix()
        exists = source.exists() and source.stat().st_size > 0
        marker_status = "FAIL"
        if exists:
            text = source.read_text(errors="replace")
            missing_markers = [marker for marker in marker_for(source.name) if marker not in text]
            if source.name.endswith(".gbrjob"):
                try:
                    data = json.loads(text)
                    if data.get("GeneralSpecs", {}).get("LayerNumber") != 4:
                        missing_markers.append("LayerNumber=4")
                except json.JSONDecodeError:
                    missing_markers.append("valid JSON")
            if missing_markers:
                marker_failures.append(f"{rel}: missing " + ", ".join(missing_markers))
            else:
                marker_status = "PASS"
        file_rows.append([rel, source.stat().st_size if exists else 0, marker_status])
        if not exists:
            failures.append(f"Missing or empty fabrication source: {rel}")

    if marker_failures:
        failures.extend(marker_failures)

    zip_names = []
    zip_rows = []
    if not zip_path.exists() or zip_path.stat().st_size == 0:
        failures.append(f"Missing or empty upload ZIP: {packager.ZIP_NAME}")
    else:
        with zipfile.ZipFile(zip_path) as archive:
            infos = archive.infolist()
            zip_names = [info.filename for info in infos]
            if zip_names != expected_zip_names:
                failures.append("Upload ZIP member order/content mismatch: " + ", ".join(zip_names))
            for info in infos:
                member_ok = zip_member_ok(info)
                zip_rows.append([info.filename, info.file_size, "PASS" if member_ok else "FAIL"])
                if not member_ok:
                    failures.append(f"ZIP member has non-deterministic or unsafe metadata: {info.filename}")
                expected_source = next((path for path in expected_sources if path.name == info.filename), None)
                if expected_source and archive.read(info.filename) != expected_source.read_bytes():
                    failures.append(f"ZIP member does not match exported source file: {info.filename}")

    sha_entries = read_sha256sums(sha_path)
    sha_rows = []
    for name in sorted(expected_upload_files):
        path = out_dir / name
        expected = sha256(path) if path.exists() else ""
        actual = sha_entries.get(name)
        ok = path.exists() and actual == expected
        sha_rows.append([name, actual or "-", "PASS" if ok else "FAIL"])
        if not ok:
            failures.append(f"SHA256 mismatch or missing entry: {name}")
    extra_sha = sorted(set(sha_entries) - set(expected_upload_files))
    if extra_sha:
        failures.append("Unexpected SHA256 entries: " + ", ".join(extra_sha))

    manifest = manifest_path.read_text(errors="replace") if manifest_path.exists() else ""
    if "# VJUGA Rev A upload package manifest" not in manifest:
        failures.append("Upload manifest missing expected title")
    if zip_path.exists() and sha256(zip_path) not in manifest:
        failures.append("Upload manifest does not include the Gerber/drill ZIP SHA256")

    status = "READY" if not failures else "NOT READY"
    lines = [
        "# Rev A fabrication package integrity",
        "",
        f"Package: `{out_dir}`",
        f"Status: **{status}**",
        "",
        "This report verifies upload-package structure and checksums before human",
        "Gerber review. It does not validate visual manufacturability.",
        "",
        "## Summary",
        "",
        f"- Expected fabrication files: {len(expected_sources)}",
        f"- ZIP members: {len(zip_names)}",
        f"- SHA256 entries: {len(sha_entries)}",
        f"- Integrity failures: {len(failures)}",
        "",
        "## Fabrication Sources",
        "",
        "| File | Bytes | Format markers |",
        "| --- | ---: | --- |",
    ]
    lines.extend(table_row(row) for row in file_rows)
    lines.extend(["", "## Upload ZIP", "", "| Member | Bytes | Metadata |", "| --- | ---: | --- |"])
    lines.extend(table_row(row) for row in zip_rows)
    lines.extend(["", "## Upload SHA256", "", "| File | SHA256SUMS entry | Status |", "| --- | --- | --- |"])
    lines.extend(table_row(row) for row in sha_rows)

    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in failures)

    lines.append("")
    return "\n".join(lines), status


def main():
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "fab/minimal-vga")
    report, status = build_report(out_dir)
    path = out_dir / "fab-package-integrity.md"
    path.write_text(report)
    print(report)
    print(f"Wrote {path}")
    return 0 if status == "READY" else 3


if __name__ == "__main__":
    raise SystemExit(main())
