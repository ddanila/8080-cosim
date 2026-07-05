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

    checks.append(("Custom branch checked out", branch == "custom", f"Current branch: `{branch or 'unknown'}`."))
    checks.append((
        "Custom branch pushed",
        bool(commit and remote and commit == remote),
        f"HEAD: `{commit or 'unknown'}`; origin/custom: `{remote or 'unknown'}`.",
    ))
    checks.append(("Submodule worktree clean", dirty == "", "No uncommitted fork changes."))

    jar = FREEROUTING / "build" / "libs" / "freerouting-current-executable.jar"
    checks.append(("Custom executable jar built", jar.exists(), f"Jar: `{jar.relative_to(ROOT)}`."))

    scheduler = FREEROUTING / "src" / "main" / "java" / "app" / "freerouting" / "management" / "RoutingJobSchedulerActionThread.java"
    checks.append((
        "Headless scheduler honors v1.9 router",
        contains(
            scheduler,
            "RouterSettings.ALGORITHM_V19.equals(algorithm)",
            "new BatchAutorouterV19(job)",
        ),
        "`RoutingJobSchedulerActionThread` selects `BatchAutorouterV19` for `freerouting-router-v19`.",
    ))
    checks.append((
        "Built jar contains v1.9 scheduler path",
        jar_entry_contains(
            jar,
            "app/freerouting/management/RoutingJobSchedulerActionThread.class",
            "freerouting-router-v19",
            "BatchAutorouterV19",
        ),
        "The built executable jar contains the headless v1.9 scheduler selection, guarding against stale local jars.",
    ))

    headless_test = FREEROUTING / "src" / "test" / "java" / "app" / "freerouting" / "interactive" / "HeadlessRoutingTest.java"
    checks.append((
        "Headless v1.9 regression test present",
        contains(
            headless_test,
            "headlessRouting_usesV19RouterWhenSelected",
            "Starting V1.9 router",
            "job.output.size > 0",
        ),
        "`HeadlessRoutingTest` guards the #508 workaround path and non-empty SES output.",
    ))

    checks.append((
        "VJUGA route script defaults to v1.9",
        contains(ROUTE_SCRIPT, 'FREEROUTING_ALGORITHM="${FREEROUTING_ALGORITHM:-freerouting-router-v19}"'),
        "`route_rev_a_pcb.sh` defaults to `freerouting-router-v19`.",
    ))
    checks.append((
        "VJUGA rejects stock jar for v1.9",
        contains(ROUTE_SCRIPT, 'USING_STOCK_FALLBACK=1', 'requires the custom FreeRouting fork jar'),
        "`route_rev_a_pcb.sh` does not silently run v1.9 mode against the stock jar.",
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
        "depend on the custom Freerouting fork instead of the stock v2.x headless",
        "path discussed in upstream #508. It does not replace a full autoroute",
        "quality run.",
        "",
        "## Summary",
        "",
        f"- Freerouting branch: `{branch or 'unknown'}`",
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
