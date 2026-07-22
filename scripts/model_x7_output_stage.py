#!/usr/bin/env python3
"""Generate the evidence-bounded static Juku X7 output-stage model report."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import struct
import subprocess
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
BOARD_PATH = ROOT / "kicad" / "juku.board.json"
CENSUS_PATH = ROOT / "ref" / "juku-official-009-ic-census.json"
SEMICONDUCTOR_PATH = ROOT / "ref" / "schematics" / "native-semiconductor-registration.json"
MODEL_PATH = ROOT / "ref" / "video" / "x7-output-stage-model.json"
SUMMARY_PATH = ROOT / "ref" / "video" / "x7-output-stage-summary.json"
REPORT_PATH = ROOT / "docs" / "x7-output-stage-model.md"
REPOSITORY = "https://github.com/ddanila/8080-cosim"
STATES = ((0, 0), (0, 1), (1, 0), (1, 1))


def parallel(a: float, b: float | None) -> float:
    return a if b is None else 1.0 / (1.0 / a + 1.0 / b)


def solve_stage(
    sync: int,
    signal: int,
    *,
    resistors: dict[str, float],
    low_v: float,
    high_v: float,
    supply_v: float,
    load_ohm: float | None,
    beta: float,
    vbe_v: float,
    vce_saturation_v: float,
) -> dict[str, float | str | bool]:
    """Solve the DC emitter follower using KCL at its base and emitter."""
    sync_v = high_v if sync else low_v
    signal_v = high_v if signal else low_v
    r62, r63, r64, r65 = (resistors[name] for name in ("R62", "R63", "R64", "R65"))
    emitter_resistance = parallel(r65, load_ohm)
    conductance = 1.0 / r62 + 1.0 / r63 + 1.0 / r64
    drive = sync_v / r62 + signal_v / r63
    open_base_v = drive / conductance

    if open_base_v <= vbe_v:
        base_v = open_base_v
        output_v = base_current_a = emitter_current_a = collector_current_a = 0.0
        region = "off"
    else:
        base_load_conductance = 1.0 / ((beta + 1.0) * emitter_resistance)
        base_v = (drive + vbe_v * base_load_conductance) / (
            conductance + base_load_conductance
        )
        output_v = base_v - vbe_v
        emitter_current_a = output_v / emitter_resistance
        base_current_a = emitter_current_a / (beta + 1.0)
        collector_current_a = emitter_current_a - base_current_a
        region = "active"

    saturation_limit_v = supply_v - vce_saturation_v
    saturated = output_v > saturation_limit_v + 1e-12
    if saturated:
        region = "saturation-outside-model"

    return {
        "region": region,
        "saturated": saturated,
        "base_v": base_v,
        "output_v": output_v,
        "vce_v": supply_v - output_v,
        "saturation_margin_v": saturation_limit_v - output_v,
        "base_current_ma": base_current_a * 1000.0,
        "collector_current_ma": collector_current_a * 1000.0,
        "collector_dissipation_mw": (supply_v - output_v) * collector_current_a * 1000.0,
        "emitter_current_ma": emitter_current_a * 1000.0,
        "external_load_current_ma": 0.0 if load_ohm is None else output_v / load_ohm * 1000.0,
        "r65_current_ma": output_v / r65 * 1000.0,
        "d34_sync_pin_current_ma": (sync_v - base_v) / r62 * 1000.0,
        "d34_signal_pin_current_ma": (signal_v - base_v) / r63 * 1000.0,
    }


def state_name(state: tuple[int, int]) -> str:
    return f"sync={state[0]},signal={state[1]}"


def rounded(result: dict[str, Any]) -> dict[str, Any]:
    return {
        key: round(value, 9) if isinstance(value, float) else value
        for key, value in result.items()
    }


def nodes(board: dict[str, Any], net: str) -> set[tuple[str, str]]:
    return {tuple(item) for item in board["nets"][net]["nodes"]}


def find_chip(board: dict[str, Any], ref: str) -> dict[str, Any]:
    return next(chip for chip in board["chips"] if chip.get("ref") == ref)


def topology_checks(
    board: dict[str, Any],
    census: dict[str, Any],
    semiconductors: dict[str, Any],
    model: dict[str, Any],
) -> list[dict[str, Any]]:
    expected_nets = {
        "D34_SYNC": {("D34", "8"), ("R62", "1")},
        "D34_SIG": {("D34", "11"), ("R63", "1")},
        "VT2_BASE": {("R62", "2"), ("R63", "2"), ("R64", "1"), ("VT2", "3")},
        "VIDEO_OUT": {("VT2", "1"), ("R65", "1"), ("X7", "1")},
    }
    checks: list[dict[str, Any]] = []
    for net, expected in expected_nets.items():
        actual = nodes(board, net)
        checks.append({
            "name": f"{net} endpoint contract",
            "pass": actual == expected,
            "evidence": ", ".join(f"{ref}.{pin}" for ref, pin in sorted(actual)),
        })
    checks.extend([
        {
            "name": "R64 and R65 fitted returns are grounded",
            "pass": {("R64", "2"), ("R65", "2")} <= nodes(board, "GND"),
            "evidence": "R64.2 + R65.2 on GND",
        },
        {
            "name": "VT2 collector is on +5 V",
            "pass": ("VT2", "2") in nodes(board, "P5V"),
            "evidence": "VT2.2 on P5V",
        },
        {
            "name": "VT2 device and E-C-B mapping are guarded",
            "pass": (
                find_chip(board, "VT2").get("value") == "КТ315"
                and find_chip(board, "VT2").get("pins") == {"1": "E", "2": "C", "3": "B"}
            ),
            "evidence": "VT2 = КТ315; 1=E, 2=C, 3=B",
        },
    ])
    d34_census = next(
        (item for item in census["rows"] if "D34" in item["refs"]), None
    )
    checks.append({
        "name": "Exact-revision D34 identity is К555ЛП5",
        "pass": d34_census is not None
        and d34_census["marking"] == "К555ЛП5"
        and find_chip(board, "D34").get("type") == "LP5_XOR",
        "evidence": "ДГШ5.109.009 ПЭЗ census D34 + board LP5_XOR type",
    })
    expected_values = {"R62": "2к", "R63": "1к", "R64": "5,1к", "R65": "430"}
    board_values = {ref: find_chip(board, ref).get("value") for ref in expected_values}
    config_values = model["nominal"]["resistance_ohm"]
    checks.append({
        "name": "Fitted resistor identities and model values agree",
        "pass": board_values == expected_values and config_values == {
            "R62": 2000.0, "R63": 1000.0, "R64": 5100.0, "R65": 430.0
        },
        "evidence": "R62=2 kΩ, R63=1 kΩ, R64=5.1 kΩ, R65=430 Ω",
    })
    checks.append({
        "name": "C94 is absent from the nominal model",
        "pass": "C94" not in model["nominal"].get("resistance_ohm", {})
        and any("C94" in item for item in model["scope"]["excluded"]),
        "evidence": "unresolved population/value/endpoints retained as a boundary",
    })
    d34_reference = model["d34_output_reference"]
    exact_d34 = d34_reference["exact_device"]
    exact_d34_path = ROOT / exact_d34["datasheet"].split(",", 1)[0]
    checks.append({
        "name": "Preserved exact-device К555ЛП5 datasheet hash and limits match",
        "pass": (
            hashlib.sha256(exact_d34_path.read_bytes()).hexdigest()
            == exact_d34["datasheet_sha256"]
            and exact_d34["voh_min_v"] == 2.7
            and exact_d34["vol_max_v"] == 0.5
            and exact_d34["fanout"] == 10
            and exact_d34["input_low_current_abs_max_ma"] == 0.8
            and exact_d34["input_high_current_max_ma"] == 0.04
            and exact_d34["fanout_derived_high_source_current_ma"]
            == exact_d34["fanout"] * exact_d34["input_high_current_max_ma"]
            and exact_d34["fanout_derived_low_sink_current_ma"]
            == exact_d34["fanout"] * exact_d34["input_low_current_abs_max_ma"]
            and exact_d34["output_current_values_are_derived_not_explicit"]
            and not exact_d34["output_current_test_conditions_present"]
            and not exact_d34["nonlinear_output_curve_present"]
        ),
        "evidence": "К555ЛП5: VOH >=2.7 V, VOL <=0.5 V; fanout-derived 0.4 mA source/8 mA sink; no output I/V curve",
    })
    comparison = d34_reference["current_condition_comparison"]
    comparison_path = ROOT / comparison["datasheet"].split(",", 1)[0]
    checks.append({
        "name": "Preserved SN74LS86A current-comparison datasheet hash matches",
        "pass": hashlib.sha256(comparison_path.read_bytes()).hexdigest()
        == comparison["datasheet_sha256"],
        "evidence": "TI SDLS124 page 4; current threshold only, not К555ЛП5 equivalence",
    })
    vt2 = model["vt2_output_reference"]
    vt2_path = ROOT / vt2["datasheet"].split(",", 1)[0]
    checks.append({
        "name": "Preserved КТ315Б datasheet hash, package, and model limits match",
        "pass": (
            hashlib.sha256(vt2_path.read_bytes()).hexdigest()
            == vt2["datasheet_sha256"]
            and vt2["board_device"] == "КТ315Б"
            and "Б/8901" in semiconductors["physical_source"]["observation"]
            and vt2["pin_order_front_view"] == ["E", "C", "B"]
            and model["sweep"]["beta"] == [50.0, 100.0, 350.0]
            and vt2["hfe_at_vce_10v_ic_1ma"] == [50.0, 350.0]
            and model["nominal"]["transistor"]["vce_saturation_v"]
            == vt2["vce_saturation_max_v_at_ic_20ma_ib_2ma"]
            and vt2["vbe_saturation_max_v_at_ic_20ma_ib_2ma"] == 1.0
            and vt2["continuous_vce_max_v_with_rbe_10kohm"] == 20.0
            and vt2["collector_current_max_ma"] == 100.0
            and vt2["collector_dissipation_max_mw_at_25c"] == 150.0
            and vt2["collector_junction_capacitance_max_pf_at_vcb_10v"] == 7.0
            and vt2["transition_frequency_min_mhz_at_vce_10v_ic_1ma"] == 250.0
        ),
        "evidence": "owner marking Б/8901; old KT-13 E-C-B; hFE 50..350; VCE(sat) <=0.4 V",
    })
    return checks


def nominal_results(model: dict[str, Any], load_ohm: float | None) -> dict[str, Any]:
    nominal = model["nominal"]
    transistor = nominal["transistor"]
    return {
        state_name(state): rounded(solve_stage(
            *state,
            resistors=nominal["resistance_ohm"],
            low_v=nominal["ttl_pin_voltage_v"]["low"],
            high_v=nominal["ttl_pin_voltage_v"]["high"],
            supply_v=nominal["supply_v"],
            load_ohm=load_ohm,
            beta=transistor["beta"],
            vbe_v=transistor["vbe_v"],
            vce_saturation_v=transistor["vce_saturation_v"],
        )) for state in STATES
    }


def resistor_corners(nominal: dict[str, float], tolerance: float) -> Iterable[dict[str, float]]:
    names = tuple(nominal)
    for signs in itertools.product((-1.0, 1.0), repeat=len(names)):
        yield {
            name: nominal[name] * (1.0 + sign * tolerance)
            for name, sign in zip(names, signs)
        }


def sweep_results(model: dict[str, Any], terminated: bool) -> tuple[int, dict[str, Any]]:
    nominal = model["nominal"]
    sweep = model["sweep"]
    transistor = nominal["transistor"]
    resistor_sets = tuple(resistor_corners(
        nominal["resistance_ohm"], sweep["resistor_tolerance_fraction"]
    ))
    loads: tuple[float | None, ...] = (
        tuple(sweep["external_load_ohm"]) if terminated else (None,)
    )
    parameter_sets = itertools.product(
        resistor_sets,
        sweep["ttl_low_v"],
        sweep["ttl_high_v"],
        sweep["supply_v"],
        loads,
        sweep["beta"],
        sweep["vbe_v"],
    )
    extrema: dict[str, dict[str, float | int]] = {
        state_name(state): {
            "output_v_min": math.inf,
            "output_v_max": -math.inf,
            "base_v_min": math.inf,
            "base_v_max": -math.inf,
            "collector_current_ma_max": 0.0,
            "collector_dissipation_mw_max": 0.0,
            "vce_v_max": 0.0,
            "abs_d34_sync_pin_current_ma_max": 0.0,
            "abs_d34_signal_pin_current_ma_max": 0.0,
            "d34_sync_fanout_envelope_warning_count": 0,
            "d34_signal_fanout_envelope_warning_count": 0,
            "saturation_margin_v_min": math.inf,
            "saturated_corner_count": 0,
        } for state in STATES
    }
    corner_count = 0
    for resistors, low_v, high_v, supply_v, load_ohm, beta, vbe_v in parameter_sets:
        corner_count += 1
        for state in STATES:
            result = solve_stage(
                *state,
                resistors=resistors,
                low_v=low_v,
                high_v=high_v,
                supply_v=supply_v,
                load_ohm=load_ohm,
                beta=beta,
                vbe_v=vbe_v,
                vce_saturation_v=transistor["vce_saturation_v"],
            )
            item = extrema[state_name(state)]
            for field in ("output_v", "base_v"):
                item[f"{field}_min"] = min(float(item[f"{field}_min"]), float(result[field]))
                item[f"{field}_max"] = max(float(item[f"{field}_max"]), float(result[field]))
            item["collector_current_ma_max"] = max(
                float(item["collector_current_ma_max"]), float(result["collector_current_ma"])
            )
            item["collector_dissipation_mw_max"] = max(
                float(item["collector_dissipation_mw_max"]),
                float(result["collector_dissipation_mw"]),
            )
            item["vce_v_max"] = max(float(item["vce_v_max"]), float(result["vce_v"]))
            for source in ("sync", "signal"):
                field = f"abs_d34_{source}_pin_current_ma_max"
                item[field] = max(float(item[field]), abs(float(result[f"d34_{source}_pin_current_ma"])))
            exact_d34 = model["d34_output_reference"]["exact_device"]
            for source, logic_level in zip(("sync", "signal"), state):
                current = float(result[f"d34_{source}_pin_current_ma"])
                relevant_current = max(0.0, current if logic_level else -current)
                limit = exact_d34[
                    "fanout_derived_high_source_current_ma"
                    if logic_level else "fanout_derived_low_sink_current_ma"
                ]
                field = f"d34_{source}_fanout_envelope_warning_count"
                item[field] = int(item[field]) + int(relevant_current > limit + 1e-12)
            item["saturation_margin_v_min"] = min(
                float(item["saturation_margin_v_min"]), float(result["saturation_margin_v"])
            )
            item["saturated_corner_count"] = int(item["saturated_corner_count"]) + int(result["saturated"])
    return corner_count, {
        key: rounded(value) for key, value in extrema.items()
    }


def drive_envelope_result(
    state: tuple[int, int], result: dict[str, Any], model: dict[str, Any]
) -> dict[str, Any]:
    reference = model["d34_output_reference"]["exact_device"]
    output: dict[str, Any] = {}
    for source, logic_level in zip(("sync", "signal"), state):
        current = float(result[f"d34_{source}_pin_current_ma"])
        mode = "source" if logic_level else "sink"
        relevant_current = max(0.0, current if logic_level else -current)
        limit = reference[
            "fanout_derived_high_source_current_ma"
            if logic_level else "fanout_derived_low_sink_current_ma"
        ]
        output[source] = {
            "logic_level": logic_level,
            "drive_mode": mode,
            "relevant_current_ma": round(relevant_current, 9),
            "fanout_derived_limit_ma": limit,
            "within_fanout_derived_limit": relevant_current <= limit + 1e-12,
        }
    return output


def build_summary(
    board: dict[str, Any],
    census: dict[str, Any],
    semiconductors: dict[str, Any],
    model: dict[str, Any],
) -> dict[str, Any]:
    checks = topology_checks(board, census, semiconductors, model)
    loaded = nominal_results(model, model["nominal"]["external_load_ohm"])
    unloaded = nominal_results(model, None)
    loaded_count, loaded_sweep = sweep_results(model, True)
    unloaded_count, unloaded_sweep = sweep_results(model, False)

    order_ok = (
        loaded["sync=0,signal=0"]["output_v"]
        < loaded["sync=1,signal=0"]["output_v"]
        < loaded["sync=0,signal=1"]["output_v"]
        < loaded["sync=1,signal=1"]["output_v"]
    )
    load_ok = all(
        loaded[state_name(state)]["output_v"] <= unloaded[state_name(state)]["output_v"] + 1e-12
        for state in STATES
    )
    no_saturation = all(
        item["saturated_corner_count"] == 0
        for table in (loaded_sweep, unloaded_sweep)
        for item in table.values()
    )
    vt2 = model["vt2_output_reference"]
    vt2_limits_ok = all(
        item["collector_current_ma_max"] <= vt2["collector_current_max_ma"]
        and item["collector_dissipation_mw_max"]
        <= vt2["collector_dissipation_max_mw_at_25c"]
        and item["vce_v_max"] <= vt2["continuous_vce_max_v_with_rbe_10kohm"]
        for table in (loaded_sweep, unloaded_sweep)
        for item in table.values()
    )
    checks.extend([
        {
            "name": "Nominal four-state transfer is ordered by the traced resistor weights",
            "pass": order_ok,
            "evidence": "00 < sync-only < signal-only < 11",
        },
        {
            "name": "A 75-ohm termination never raises the nominal emitter voltage",
            "pass": load_ok,
            "evidence": "terminated output <= unterminated output for all four states",
        },
        {
            "name": "Declared DC corners remain outside transistor saturation",
            "pass": no_saturation,
            "evidence": f"{loaded_count} terminated + {unloaded_count} unterminated parameter corners per logic state",
        },
        {
            "name": "Declared DC corners remain inside published КТ315Б absolute limits",
            "pass": vt2_limits_ok,
            "evidence": "Ic <=100 mA, P <=150 mW at 25 C, VCE <=20 V",
        },
    ])
    nominal_envelope = {
        state_name(state): drive_envelope_result(
            state, loaded[state_name(state)], model
        ) for state in STATES
    }
    envelope_exceeded = any(
        not pin["within_fanout_derived_limit"]
        for state in nominal_envelope.values()
        for pin in state.values()
    )
    numerical_pass = all(item["pass"] for item in checks)
    status = (
        "topology-and-device-limits-pass-d34-drive-open"
        if numerical_pass and envelope_exceeded
        else "pass" if numerical_pass
        else "fail"
    )
    return {
        "schema_version": 2,
        "model_id": model["model_id"],
        "proof_layer": "analog-output static transfer only",
        "status": status,
        "checks": checks,
        "nominal": {
            "terminated_75_ohm": loaded,
            "unterminated": unloaded,
        },
        "sweep": {
            "terminated": {"corner_count_per_state": loaded_count, "states": loaded_sweep},
            "unterminated": {"corner_count_per_state": unloaded_count, "states": unloaded_sweep},
        },
        "d34_output_boundary": {
            "device": model["d34_output_reference"]["board_device"],
            "exact_device_voltage_envelope": model["d34_output_reference"]["exact_device"],
            "independent_current_corroboration_device": (
                model["d34_output_reference"]["current_condition_comparison"]["device"]
            ),
            "corroboration_not_equivalence_evidence": True,
            "nominal_75_ohm": nominal_envelope,
            "nominal_fanout_envelope_exceeded": envelope_exceeded,
            "interpretation": (
                "The fixed-pin-voltage approximation requests more high-state source "
                "current than the exact К555ЛП5 sheet's fanout-derived envelope. "
                "The independent SN74LS86A sheet corroborates the derived 0.4 mA/8 mA "
                "loads, but neither source supplies a nonlinear output curve; physical "
                "X7 voltages still require a better source or measurement."
                if envelope_exceeded else
                "Nominal pin currents stay within the exact-device fanout-derived envelope."
            ),
        },
        "limitations": model["scope"]["excluded"],
    }


def markdown_table_row(values: Iterable[Any]) -> str:
    return "| " + " | ".join(str(value).replace("|", "/") for value in values) + " |"


def write_report(model: dict[str, Any], summary: dict[str, Any]) -> None:
    nominal = summary["nominal"]
    lines = [
        "# X7 output-stage static model",
        "",
        "Status date: **2026-07-22**.",
        "",
        "Status: **TOPOLOGY + DEVICE LIMITS GUARDED / D34 DRIVE CURVE AND HARDWARE CALIBRATION OPEN**.",
        "",
        "This generated report is the first evidence-bounded part of CVBS-plan WP4.",
        "It proves only the DC transfer of the traced X7 emitter-follower topology; it",
        "does not prove a physical D34 waveform, monitor timing, edge shape, or the",
        "installed KT315Б parameters. The published КТ315Б grade limits are guarded,",
        "but they do not measure the individual transistor.",
        "",
        "## Commands",
        "",
        "```sh",
        "python3 scripts/model_x7_output_stage.py",
        "python3 scripts/model_x7_output_stage.py --fixture-dir /tmp/juku-x7-static",
        "```",
        "",
        "The optional fixture is a little-endian float32 stepped-voltage diagnostic,",
        "not a video waveform. Its sidecar records the current source commit, sample",
        "rate, load, state schedule, model hash, and sample hash.",
        "",
        "## Guarded topology and model checks",
        "",
        "| Check | Result | Evidence |",
        "| --- | --- | --- |",
    ]
    lines.extend(markdown_table_row((item["name"], "PASS" if item["pass"] else "FAIL", item["evidence"])) for item in summary["checks"])
    lines.extend([
        "",
        "## D34 drive-current boundary",
        "",
        "The preserved exact-device К555ЛП5 sheet guarantees VOH >=2.7 V,",
        "VOL <=0.5 V, and fanout 10, but omits output-current test conditions and",
        "nonlinear I/V curves. Its stated input currents under the standard fanout",
        "meaning imply 0.4 mA high-state source and 8 mA low-state sink",
        "full-fanout loads. The independent TI SN74LS86A sheet",
        "corroborates those values but does not supply К555ЛП5 curves.",
        "",
        "| State | Pin | Mode | Relevant current (mA) | Fanout-derived limit (mA) | Result |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ])
    for state in STATES:
        for source, item in summary["d34_output_boundary"]["nominal_75_ohm"][state_name(state)].items():
            lines.append(markdown_table_row((
                state_name(state), source, item["drive_mode"],
                f'{item["relevant_current_ma"]:.3f}',
                f'{item["fanout_derived_limit_ma"]:.3f}',
                "WITHIN" if item["within_fanout_derived_limit"] else "EXCEEDS",
            )))
    lines.extend([
        "",
        summary["d34_output_boundary"]["interpretation"],
    ])
    lines.extend([
        "",
        "## Nominal DC transfer",
        "",
        "Positive D34 pin current means current sourced out of that output; negative",
        "means that output is sinking current from the summing node.",
        "",
        "| Load | D34 sync | D34 signal | Region | Base (V) | X7 (V) | Ic (mA) | Sync pin (mA) | Signal pin (mA) |",
        "| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ])
    for load_name, table in (("75 Ω", nominal["terminated_75_ohm"]), ("unterminated", nominal["unterminated"])):
        for state in STATES:
            result = table[state_name(state)]
            lines.append(markdown_table_row((
                load_name, state[0], state[1], result["region"],
                f'{result["base_v"]:.4f}', f'{result["output_v"]:.4f}',
                f'{result["collector_current_ma"]:.3f}',
                f'{result["d34_sync_pin_current_ma"]:.3f}',
                f'{result["d34_signal_pin_current_ma"]:.3f}',
            )))
    lines.extend([
        "",
        "## Declared corner sweep",
        "",
        f"The terminated sweep evaluates **{summary['sweep']['terminated']['corner_count_per_state']:,}**",
        "corners per logic state: all independent ±5% resistor corners crossed with",
        "the declared TTL pin levels, +5 V supply, 75 Ω load, beta, and VBE values.",
        f"The unterminated diagnostic evaluates **{summary['sweep']['unterminated']['corner_count_per_state']:,}**",
        "corners per state with only fitted R65 loading the emitter.",
        "",
        "The two final columns count corners that exceed the exact sheet's",
        "fanout-derived loads. They warn that fixed pin voltages have crossed the",
        "stated same-family load envelope; they do not predict nonlinear droop.",
        "",
        "| Load | State | X7 range (V) | Base range (V) | Max Ic (mA) | Max /D34 sync/ (mA) | Max /D34 signal/ (mA) | Min saturation margin (V) | Sync warnings | Signal warnings |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for load_name, sweep_key in (("75 Ω", "terminated"), ("unterminated", "unterminated")):
        for state in STATES:
            item = summary["sweep"][sweep_key]["states"][state_name(state)]
            lines.append(markdown_table_row((
                load_name,
                state_name(state),
                f'{item["output_v_min"]:.4f}–{item["output_v_max"]:.4f}',
                f'{item["base_v_min"]:.4f}–{item["base_v_max"]:.4f}',
                f'{item["collector_current_ma_max"]:.3f}',
                f'{item["abs_d34_sync_pin_current_ma_max"]:.3f}',
                f'{item["abs_d34_signal_pin_current_ma_max"]:.3f}',
                f'{item["saturation_margin_v_min"]:.3f}',
                item["d34_sync_fanout_envelope_warning_count"],
                item["d34_signal_fanout_envelope_warning_count"],
            )))
    lines.extend([
        "",
        "## Model boundary",
        "",
        "The following are deliberately not inferred by this result:",
        "",
    ])
    lines.extend(f"- {item}" for item in model["scope"]["excluded"])
    lines.extend([
        "",
        "The fixed TTL pin-voltage approximation exposes the D34 source/sink currents",
        "but is not yet a nonlinear К555ЛП5 output model. Beta and VBE are sensitivity",
        "bounds; only beta endpoints are exact-grade data, not installed-part measurements.",
        "C94 remains absent. Consequently the",
        "stepped fixture has ideal discontinuities and must not be used as evidence of",
        "rise/fall time, bandwidth, actual composite polarity, or receiver lock.",
        "",
        "## Next evidence",
        "",
        "- Obtain a К555ЛП5 nonlinear output curve or measure D34 under the traced",
        "  load, then replace the fixed pin-voltage approximation.",
        "- Feed independently timed D34_SYNC/D34_SIG events into this transfer model only",
        "  after the physical video-slot and D34 waveform boundaries close.",
        "- Inspect C94 and capture terminated X7 plus VT2 base on hardware before adding",
        "  any dynamic component or promoting model voltages to calibrated results.",
        "",
    ])
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def git_revision() -> tuple[str, bool]:
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    dirty = bool(subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, text=True
    ).strip())
    return revision, dirty


def emit_fixture(directory: Path, model: dict[str, Any], summary: dict[str, Any]) -> None:
    fixture = model["diagnostic_fixture"]
    directory.mkdir(parents=True, exist_ok=True)
    waveform_path = directory / "x7-static-step.f32"
    metadata_path = directory / "x7-static-step.json"
    samples = bytearray()
    state_values = summary["nominal"]["terminated_75_ohm"]
    for state in fixture["state_sequence"]:
        value = state_values[state_name(tuple(state))]["output_v"]
        packed = struct.pack("<f", value)
        samples.extend(packed * fixture["samples_per_state"])
    waveform_path.write_bytes(samples)
    revision, dirty = git_revision()
    metadata = {
        "schema_version": 1,
        "classification": "synthetic static transfer diagnostic; not a video waveform",
        "sample_format": fixture["sample_format"],
        "sample_rate_hz": fixture["sample_rate_hz"],
        "sample_count": len(samples) // 4,
        "voltage_scale": "1.0 V per stored float unit",
        "voltage_offset_v": 0.0,
        "load_ohm": fixture["load_ohm"],
        "state_sequence": fixture["state_sequence"],
        "samples_per_state": fixture["samples_per_state"],
        "source_repository": REPOSITORY,
        "source_commit": revision,
        "source_tree_dirty": dirty,
        "generator": "python3 scripts/model_x7_output_stage.py --fixture-dir DIR",
        "model_sha256": hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest(),
        "waveform_file": waveform_path.name,
        "waveform_sha256": hashlib.sha256(samples).hexdigest(),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {waveform_path}")
    print(f"Wrote {metadata_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture-dir", type=Path,
        help="also emit a deterministic float32 stepped-voltage diagnostic and metadata",
    )
    args = parser.parse_args()
    board = json.loads(BOARD_PATH.read_text(encoding="utf-8"))
    census = json.loads(CENSUS_PATH.read_text(encoding="utf-8"))
    semiconductors = json.loads(SEMICONDUCTOR_PATH.read_text(encoding="utf-8"))
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    summary = build_summary(board, census, semiconductors, model)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(model, summary)
    print(f"Wrote {SUMMARY_PATH.relative_to(ROOT)}")
    print(f"Wrote {REPORT_PATH.relative_to(ROOT)}")
    if args.fixture_dir:
        emit_fixture(args.fixture_dir.resolve(), model, summary)
    print(f"X7 STATIC MODEL: {summary['status'].upper()}")
    return 1 if summary["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
