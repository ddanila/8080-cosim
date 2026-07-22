#!/usr/bin/env bash
# This list mirrors .github/workflows/reports.yml and hdl.yml; update all three together.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"

deep=0
check=0
for arg in "$@"; do
  case "$arg" in
    --deep) deep=1 ;;
    --check) check=1 ;;
    -h|--help)
      echo "Usage: scripts/regen_all.sh [--deep] [--check]"
      exit 0
      ;;
    *)
      echo "regen_all.sh: unknown argument: $arg" >&2
      echo "Usage: scripts/regen_all.sh [--deep] [--check]" >&2
      exit 2
      ;;
  esac
done

run() {
  printf '==> %s\n' "$*"
  "$@"
}

# Fast report generators, in reports.yml dependency order. Intentional repeats
# preserve the video-slot and owner-shortlist upstream regeneration groups.
run python3 scripts/report_factory_modification_disposition.py
run python3 scripts/report_unmodeled_footprint_inventory.py
run python3 scripts/report_re3_firmware_inspection.py
run python3 scripts/export_reconstructed_proms.py
run python3 scripts/report_d6_physical_decode.py
run python3 scripts/report_d8_physical_decode.py
run python3 scripts/report_d6_firmware_modes.py
run python3 scripts/report_d2_physical_truth.py
run python3 scripts/export_eprom_pair.py
run python3 scripts/report_firmware_gap_ledger.py
run python3 scripts/report_board_fidelity_gap_ledger.py
run python3 scripts/report_decap_value_fidelity.py
run python3 scripts/report_ras_resistor_bank.py
run python3 scripts/report_native_resistor_values.py
run python3 scripts/report_native_capacitor_values.py
run python3 scripts/report_native_semiconductors.py
run python3 scripts/report_d41_timing_boundary.py
run python3 scripts/report_memory_timing_boundary.py
run python3 scripts/report_io_decode_boundary.py
run python3 scripts/report_video_analog_boundary.py
run python3 scripts/model_x7_output_stage.py
run python3 scripts/report_crt_decoder_baseline.py
run python3 scripts/report_s4_interrupt_boundary.py
run python3 scripts/report_ekdos_source_inspection.py
run python3 scripts/report_vendored_disk_catalog.py
run python3 scripts/extract_basic_disk_files.py
run python3 scripts/report_cartridge_basic_firmware_lineage.py
run python3 scripts/report_jmon22_reconstruction.py
run python3 scripts/report_source_coverage_audit.py
run python3 scripts/report_official_009_ic_census.py
run python3 scripts/export_wd1772_pla.py
run python3 scripts/report_wd1772_pla_inspection.py
run python3 scripts/report_d2_reconstruction_constraints.py
run python3 scripts/report_d94_reconstruction_constraints.py
run python3 scripts/report_d41_timing_boundary.py
run python3 scripts/report_video_slot_timing_audit.py
run python3 scripts/report_fdc_bus_polarity.py
run python3 scripts/report_d101_reconstruction_constraints.py
run python3 scripts/report_d99_reconstruction_constraints.py
run python3 scripts/report_d15_d16_firmware_lineage.py
run python3 scripts/report_fdc_hardware_handoff.py
run python3 scripts/report_serial_handoff.py
run python3 scripts/report_decap_value_fidelity.py
run python3 scripts/report_d41_timing_boundary.py
run python3 scripts/report_memory_timing_boundary.py
run python3 scripts/report_io_decode_boundary.py
run python3 scripts/report_video_analog_boundary.py
run python3 scripts/report_s4_interrupt_boundary.py
run python3 scripts/report_unmodeled_footprint_inventory.py
run python3 scripts/report_d30_section_b_scan_chase.py
run python3 scripts/report_8286_pinout_audit.py
run python3 scripts/report_8282_pinout_audit.py
run python3 scripts/report_package_endpoint_coverage.py
run python3 scripts/report_owner_measurement_shortlist.py
run python3 kicad/report_replica_bringup_verification.py
run python3 kicad/report_dual_config_bom.py
run python3 kicad/report_replica_sourcing_readiness.py

if ((deep)); then
  command -v gcc >/dev/null || { echo "regen_all.sh --deep: gcc not found" >&2; exit 2; }
  command -v iverilog >/dev/null || { echo "regen_all.sh --deep: iverilog not found" >&2; exit 2; }

  # HDL/cosim report writers, in hdl.yml dependency order.
  run ./sync/ekdos_fdc_probe.py
  run ./sync/ekdos_jbasic_command_probe.py
  run ./sync/ekdos_timing_reference.py
  run python3 scripts/report_juku_top_fdc_alignment.py
  run ./sync/ekdos_checkpoint_reference.py
  run ./sync/ekdos_ioseq_reference.py
  run ./sync/juku_top_checkpoint_load_check.py
  run ./sync/juku_top_checkpoint_resume_probe.py
  run ./sync/fdc_check.sh
  run ./sync/basic_cart_check.sh
  run ./sync/d2_ready_path_check.sh
  run python3 scripts/report_d6_runtime_path.py
  run ./sync/beeper_check.sh
  run ./sync/serial_check.sh
  run ./sync/ie7_check.sh
  run ./sync/d96_check.sh
  run ./sync/ie10_check.sh
  run ./sync/ag3_check.sh
  run ./sync/juku_top_periph_bus_check.sh
  run ./sync/jmon33_hdl_probe.sh
  run ./sync/jmon33_interrupt_probe.py
  run ./sync/jmon33_ready_probe.py
  run ./sync/jmon33_command_probe.py
  run ./sync/jmon33_idle_command_probe.py
  run ./sync/ir16_check.sh
  run ./sync/kp14_check.sh
  run ./sync/video_timing_check.sh
  run ./sync/video_readout_check.sh
  run python3 scripts/report_video_physical_probes.py
  run python3 scripts/report_video_pit_timing.py
fi

if ((check)); then
  git diff --exit-code -- docs/ ref/
  echo "regen_all.sh: generated docs/ref artifacts are current"
else
  drift=$(git status --short -- docs/ ref/)
  if [[ -n "$drift" ]]; then
    echo "regen_all.sh: generated artifact drift:"
    printf '%s\n' "$drift"
  else
    echo "regen_all.sh: no generated docs/ref drift"
  fi
fi
