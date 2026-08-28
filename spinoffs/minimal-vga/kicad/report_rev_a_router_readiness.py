#!/usr/bin/env python3
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FREEROUTING = ROOT / "external" / "freerouting"
ROUTE_SCRIPT = ROOT / "spinoffs" / "minimal-vga" / "kicad" / "route_rev_a_pcb.sh"


def run_git(args, cwd):
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def contains(path, *needles):
    if not path.exists():
        return False
    text = path.read_text()
    return all(needle in text for needle in needles)


def jar_entry_contains(jar, entry, *needles):
    if not jar.exists():
        return False
    try:
        with zipfile.ZipFile(jar) as archive:
            data = archive.read(entry)
    except Exception:
        return False
    return all(needle.encode() in data for needle in needles)


def row(values):
    return "| " + " | ".join(str(value).replace("|", "/") if value else "-" for value in values) + " |"


def build_report(out_dir):
    checks = []

    submodule_present = FREEROUTING.is_dir()
    checks.append((
        "Freerouting submodule present",
        submodule_present,
        "`external/freerouting` exists.",
    ))

    branch = run_git(["branch", "--show-current"], FREEROUTING) if submodule_present else None
    commit = run_git(["rev-parse", "HEAD"], FREEROUTING) if submodule_present else None
    remote = run_git(["rev-parse", "origin/custom"], FREEROUTING) if submodule_present else None
    dirty = run_git(["status", "--short"], FREEROUTING) if submodule_present else None

    branch_ok = branch == "custom" or (not branch and bool(commit and remote and commit == remote))
    checks.append((
        "Custom branch or exact detached commit selected",
        branch_ok,
        (
            f"Current branch: `{branch or 'detached HEAD'}`; "
            f"HEAD: `{commit or 'unknown'}`; origin/custom: `{remote or 'unknown'}`."
        ),
    ))
    checks.append((
        "Custom branch pushed",
        bool(commit and remote and commit == remote),
        f"HEAD: `{commit or 'unknown'}`; origin/custom: `{remote or 'unknown'}`.",
    ))
    checks.append(("Submodule worktree clean", dirty == "", "No uncommitted fork changes."))

    jar = FREEROUTING / "build" / "libs" / "freerouting-current-executable.jar"
    checks.append(("Custom executable jar built", jar.exists(), f"Jar: `{jar.relative_to(ROOT)}`."))

    polyline = FREEROUTING / "src" / "main" / "java" / "app" / "freerouting" / "board" / "trace" / "PolylineTrace.java"
    checks.append((
        "Bounded trace combining present",
        contains(
            polyline,
            "remainingIterations = 10000",
            "PolylineTrace.combine: iteration limit reached",
        ),
        "`PolylineTrace.combine()` cannot loop forever on degenerate imported geometry.",
    ))
    checks.append((
        "Built jar contains bounded-combine marker",
        jar_entry_contains(
            jar,
            "app/freerouting/board/trace/PolylineTrace.class",
            "PolylineTrace.combine: iteration limit reached",
        ),
        "The executable jar is a custom build rather than an unpatched upstream jar.",
    ))

    ses_test = FREEROUTING / "src" / "test" / "java" / "app" / "freerouting" / "io" / "specctra" / "SesRoundTripTest.java"
    checks.append((
        "KiCad SES regression tests present",
        contains(
            ses_test,
            "sesWriterPreservesSuffixedPackageIdentifiers",
            "host_cad",
            "host_version",
        ),
        "`SesRoundTripTest` guards package identifiers and standard Specctra metadata tokens.",
    ))

    checks.append((
        "VJUGA route script selects current router",
        contains(ROUTE_SCRIPT, 'FREEROUTING_ALGORITHM="${FREEROUTING_ALGORITHM:-freerouting-router}"'),
        "`route_rev_a_pcb.sh` uses the maintained current router.",
    ))
    checks.append((
        "VJUGA disables route optimizer explicitly",
        contains(ROUTE_SCRIPT, "--router.optimizer.enabled=false"),
        "Routing does not inherit optimizer defaults from machine-global configuration.",
    ))
    checks.append((
        "VJUGA uses project-local router state",
        contains(
            ROUTE_SCRIPT,
            '--user_data_path="$REPO/.tools/freerouting-user"',
            '--logging.file.location="$REPO/.tools/freerouting-user"',
        ),
        "Routing does not read or overwrite machine-global Freerouting state.",
    ))
    checks.append((
        "VJUGA route script disables GUI",
        contains(ROUTE_SCRIPT, "--gui.enabled=false"),
        "`route_rev_a_pcb.sh` runs Freerouting headlessly.",
    ))

    status = "READY" if all(ok for _, ok, _ in checks) else "NOT READY"
    lines = [
        "# Rev A router readiness",
        "",
        f"Status: **{status}**",
        "",
        "This report records the fast checks that make VJUGA's autorouting path",
        "depend on the custom Freerouting fork and a project-owned current-router",
        "configuration. It does not replace a full autoroute",
        "quality run.",
        "",
        "## Summary",
        "",
        f"- Freerouting branch: `{branch or ('detached HEAD' if commit else 'unknown')}`",
        f"- Freerouting HEAD: `{commit or 'unknown'}`",
        f"- Built custom jar: {'yes' if jar.exists() else 'no'}",
        f"- Failed checks: {sum(1 for _, ok, _ in checks if not ok)}",
        "",
        "## Checks",
        "",
        "| Check | Status | Detail |",
        "| --- | --- | --- |",
    ]
    for name, ok, detail in checks:
        lines.append(row([name, "PASS" if ok else "FAIL", detail]))
    lines.append("")

    path = out_dir / "router-readiness.md"
    out_dir.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))
    return path, status


def main():
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "fab/minimal-vga")
    path, status = build_report(out_dir)
    print(path.read_text())
    print(f"Wrote {path}")
    return 0 if status == "READY" else 3


if __name__ == "__main__":
    raise SystemExit(main())
