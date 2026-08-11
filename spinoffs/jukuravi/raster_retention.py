#!/usr/bin/env python3
"""Run one stage of the CS00024 video-slot refresh experiment.

One invocation is one cold T36 boot and one unrefreshed hold:

1. wait for a fresh exact T36 boot and upload the 64-byte marker at `4D00h`;
2. optionally upload and CALL the exact-EktaSoft raster-arm snippet
   (`--arm raster` or `--arm raster-syncb`; `--arm none` is the control);
3. upload the hold image at `4040h` and RUN it: a register-only busy wait
   during which T36's software refresh provably does not execute;
4. after RETURN, read back the marker and the hold image and map any
   differences to physical MK4564 rows.

A missing RETURN or a post-hold transport loss is itself the decay verdict:
it reproduces the historical T34 idle signature and requires hardware RESET.
See RASTER-REFRESH-EXPERIMENT.md for the pre-registered interpretation.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import host
import raster

HERE = Path(__file__).resolve().parent
DEFAULT_LOG_DIR = HERE / "sessions" / "raster-refresh"
T36_ROM_VERSION = 0x1E
T36_CRC16 = 0xC617
RUN_TIMEOUT_MARGIN_SECONDS = 90.0


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="arm the EktaSoft raster, hold unrefreshed, read back rows"
    )
    parser.add_argument("--port")
    parser.add_argument("--fd", type=int)
    parser.add_argument("--baud", type=int, default=host.DEFAULT_BAUD)
    parser.add_argument(
        "--arm",
        required=True,
        choices=("none",) + raster.ARM_VARIANTS,
        help="none = control stage; raster = D54/D55 only; "
        "raster-syncb adds EktaSoft's D57 channel-2 write",
    )
    parser.add_argument(
        "--hold-seconds",
        type=host.parse_nonnegative_float,
        default=25.0,
        help="requested unrefreshed hold (default 25, past the proven "
        "5..17 s CS00024 T34 decay boundary)",
    )
    parser.add_argument(
        "--effective-mhz",
        type=host.parse_nonnegative_float,
        default=raster.DEFAULT_EFFECTIVE_MHZ,
        help="effective RAM-loop rate used to size the hold loop",
    )
    parser.add_argument(
        "--run-timeout",
        type=host.parse_nonnegative_float,
        help="override the RUN wait (default: estimated hold + margin)",
    )
    parser.add_argument("--loader-timeout", type=float, default=host.DEFAULT_LOADER_TIMEOUT)
    parser.add_argument(
        "--loader-guard-ms",
        type=host.parse_nonnegative_float,
        default=host.SOLICITED_RESPONSE_GUARD_SECONDS * 1000.0,
    )
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR)
    return parser


def return_a(operation: dict[str, object]) -> int | None:
    run = operation.get("run")
    if not isinstance(run, dict):
        return None
    value = run.get("return_a")
    return None if value is None else int(str(value), 16)


def main() -> int:
    args = make_parser().parse_args()
    if (args.port is None) == (args.fd is None):
        print("JUKURAVI-RASTER: pass exactly one of --port or --fd", file=sys.stderr)
        return 2

    outer = raster.outer_for_seconds(args.hold_seconds, args.effective_mhz)
    estimated = raster.hold_seconds(outer, args.effective_mhz)
    hold_image = raster.build_hold_image(outer)
    run_timeout = (
        args.run_timeout
        if args.run_timeout is not None
        else estimated + RUN_TIMEOUT_MARGIN_SECONDS
    )
    arm_snippet = None if args.arm == "none" else raster.build_arm_snippet(args.arm)

    try:
        fd, transport = host.open_transport(args.port, args.fd, args.baud)
    except host.SessionError as error:
        print(f"JUKURAVI-RASTER: ERROR {error}", file=sys.stderr)
        return 1

    logs = host.SessionLogs(args.log_dir, transport)
    session = host.HostSession(
        fd,
        logs,
        600.0,
        600.0,
        T36_ROM_VERSION,
        T36_CRC16,
        False,
        loader_guard_seconds=args.loader_guard_ms / 1000.0,
    )

    experiment: dict[str, object] = {
        "arm": args.arm,
        "arm_writes": (
            None
            if args.arm == "none"
            else [write.describe() for write in raster.arm_writes(args.arm)]
        ),
        "ekta37_sha256": raster.EKTA37_SHA256,
        "pit_window": f"0x{raster.PIT_SEQUENCE_START:04X}..0x{raster.PIT_SEQUENCE_END:04X}",
        "hold_outer": outer,
        "hold_tstates": raster.hold_tstates(outer),
        "effective_mhz": args.effective_mhz,
        "hold_seconds_requested": args.hold_seconds,
        "hold_seconds_estimated": round(estimated, 6),
        "hold_seconds_measured": None,
        "marker_address": f"0x{raster.MARKER_ADDRESS:04X}",
        "hold_address": f"0x{raster.HOLD_ADDRESS:04X}",
        "arm_address": None if args.arm == "none" else f"0x{raster.ARM_ADDRESS:04X}",
        "row_coverage": raster.row_coverage(outer),
        "marker_readback": None,
        "hold_image_readback": None,
        "verdict": "incomplete",
    }
    error_text: str | None = None
    interrupted = False
    try:
        session.begin_attempt(1)
        print(
            f"JUKURAVI-RASTER: stage arm={args.arm} hold~{estimated:.1f}s on "
            f"{transport}; press RESET once",
            flush=True,
        )
        session.run()
        session.run_loader(
            raster.MARKER,
            "<raster-marker>",
            raster.MARKER_ADDRESS,
            None,
            args.loader_timeout,
        )
        print("JUKURAVI-RASTER: marker verified", flush=True)

        if arm_snippet is not None:
            arm_operation = session.run_resident_loader_v2(
                arm_snippet,
                f"<raster-arm:{args.arm}>",
                raster.ARM_ADDRESS,
                raster.ARM_ADDRESS,
                args.loader_timeout,
            )
            observed_a = return_a(arm_operation)
            if observed_a != raster.ARM_RETURN_A:
                raise host.SessionError(
                    f"arm snippet returned A={observed_a}, "
                    f"expected 0x{raster.ARM_RETURN_A:02X}"
                )
            experiment["arm_operation_return_a"] = f"0x{observed_a:02X}"
            print(
                f"JUKURAVI-RASTER: raster armed ({len(arm_snippet)} exact bytes)",
                flush=True,
            )

        print(
            f"JUKURAVI-RASTER: uploading hold and opening the unrefreshed "
            f"window (outer={outer})",
            flush=True,
        )
        window_started = time.monotonic()
        try:
            hold_operation = session.run_resident_loader_v2(
                hold_image,
                f"<raster-hold:outer={outer}>",
                raster.HOLD_ADDRESS,
                raster.HOLD_ADDRESS,
                run_timeout,
            )
        except host.SessionError as error:
            experiment["verdict"] = "no_return"
            experiment["no_return_error"] = str(error)
            experiment["hold_seconds_measured"] = round(
                time.monotonic() - window_started, 6
            )
            print(
                "JUKURAVI-RASTER: NO RETURN from the hold — decay-consistent "
                "T34-family signature; hardware RESET required",
                flush=True,
            )
            raise
        measured = time.monotonic() - window_started
        experiment["hold_seconds_measured"] = round(measured, 6)
        observed_a = return_a(hold_operation)
        if observed_a != raster.HOLD_RETURN_A:
            raise host.SessionError(
                f"hold returned A={observed_a}, expected 0x{raster.HOLD_RETURN_A:02X}"
            )
        print(
            f"JUKURAVI-RASTER: hold returned in {measured:.3f}s "
            "(includes upload/verify time)",
            flush=True,
        )

        marker_read = session.run_resident_loader_v2(
            b"",
            "<raster-read-marker>",
            raster.MARKER_ADDRESS,
            None,
            args.loader_timeout,
            control_read_address=raster.MARKER_ADDRESS,
            control_read_length=len(raster.MARKER),
        )
        observed_marker = bytes.fromhex(str(marker_read["control_read"]["hex"]))
        experiment["marker_readback"] = raster.classify_readback(
            raster.MARKER, observed_marker, raster.MARKER_ADDRESS
        )

        image_read = session.run_resident_loader_v2(
            b"",
            "<raster-read-hold-image>",
            raster.HOLD_ADDRESS,
            None,
            args.loader_timeout,
            control_read_address=raster.HOLD_ADDRESS,
            control_read_length=len(hold_image),
        )
        observed_image = bytes.fromhex(str(image_read["control_read"]["hex"]))
        experiment["hold_image_readback"] = raster.classify_readback(
            hold_image, observed_image, raster.HOLD_ADDRESS
        )

        marker_ok = experiment["marker_readback"]["verdict"] == "pass"
        image_ok = experiment["hold_image_readback"]["verdict"] == "pass"
        experiment["verdict"] = "pass" if marker_ok and image_ok else "decayed"
        for name, result in (
            ("marker", experiment["marker_readback"]),
            ("hold-image", experiment["hold_image_readback"]),
        ):
            print(
                f"JUKURAVI-RASTER: {name} "
                f"{'PASS' if result['verdict'] == 'pass' else 'FAIL'} "
                f"differing_bytes={result['differing_bytes']} "
                f"rows_failed={len(result['rows_failed'])}",
                flush=True,
            )
        session.finish_attempt("ok")
    except KeyboardInterrupt:
        interrupted = True
        error_text = "interrupted by operator"
        if session._attempt_number is not None:
            session.finish_attempt("error", error_text)
    except (host.SessionError, OSError) as error:
        error_text = str(error)
        if session._attempt_number is not None:
            session.finish_attempt("error", error_text)
    finally:
        os.close(fd)

    summary = session.summary("error" if error_text else "ok", error_text)
    summary["raster_experiment"] = experiment
    logs.finish(summary)
    if interrupted:
        print(f"JUKURAVI-RASTER: INTERRUPTED; logs {logs.json_path}", file=sys.stderr)
    elif error_text:
        print(f"JUKURAVI-RASTER: ERROR {error_text}", file=sys.stderr)
    print(
        f"JUKURAVI-RASTER: verdict={experiment['verdict']} logs {logs.json_path}",
        flush=True,
    )
    if interrupted:
        return 130
    return 0 if experiment["verdict"] == "pass" and not error_text else 1


if __name__ == "__main__":
    raise SystemExit(main())
