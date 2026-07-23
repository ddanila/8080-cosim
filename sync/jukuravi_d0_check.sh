#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

CC=${CC:-cc}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

python3 spinoffs/jukuravi/firmware/build_d0_alive.py --check
python3 spinoffs/jukuravi/firmware/build_d0_cpu.py --check
python3 spinoffs/jukuravi/firmware/build_d0_usart_local.py --check
python3 spinoffs/jukuravi/firmware/build_d0_serial.py --check
python3 spinoffs/jukuravi/firmware/build_d0_ram.py --check
python3 spinoffs/jukuravi/firmware/build_d0_ram_fallback.py --check
python3 spinoffs/jukuravi/firmware/build_d0_romcheck.py --check
python3 spinoffs/jukuravi/firmware/build_d0_pic.py --check
python3 spinoffs/jukuravi/firmware/build_d0_ppi.py --check
python3 spinoffs/jukuravi/firmware/build_d0_pit.py --check
python3 spinoffs/jukuravi/firmware/build_d0_framebuffer.py --check
"$CC" -std=c11 -O2 -Wall -Wextra -Werror -I cosim \
  -o "$tmp/trace" \
  cosim/trace.c cosim/i8080.c cosim/juku_fdc.c cosim/juk_disk.c
python3 tests/cosim_pit_latch_test.py "$tmp/trace"
python3 tests/jukuravi_d0_alive_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-alive.bin
python3 tests/jukuravi_d0_cpu_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-cpu.bin
python3 tests/jukuravi_d0_usart_local_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-usart-local.bin
python3 tests/jukuravi_d0_serial_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-serial.bin
python3 tests/jukuravi_d0_ram_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-ram.bin
python3 tests/jukuravi_d0_ram_fallback_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-ram-fallback.bin
python3 tests/jukuravi_d0_romcheck_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-romcheck.bin
python3 tests/jukuravi_d0_pic_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-pic.bin
python3 tests/jukuravi_d0_ppi_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-ppi.bin
python3 tests/jukuravi_d0_pit_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-pit.bin
python3 tests/jukuravi_d0_framebuffer_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-framebuffer.bin
python3 tests/jukuravi_host_cli_test.py \
  "$tmp/trace" spinoffs/jukuravi/firmware/diag-d0-framebuffer.bin
./sync/jukuravi_nano_check.sh

command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
iverilog -g2012 -s pit_8253_latch_tb -o "$tmp/pit_8253_latch_tb" \
  hdl/devices.v hdl/sim/pit_8253_latch_tb.v
pit_out=$(vvp "$tmp/pit_8253_latch_tb")
printf '%s\n' "$pit_out"
grep -q "PIT8253-LATCH: PASS" <<<"$pit_out"
if grep -q "PIT8253-LATCH: FAIL" <<<"$pit_out"; then
  exit 1
fi
python3 - "$tmp/success.hex" "$tmp/failure.hex" <<'PY'
from pathlib import Path
import sys

root = Path.cwd()
sys.path.insert(0, str(root / "spinoffs/jukuravi/firmware"))
import build_d0_alive
import build_d0_cpu

image, metadata = build_d0_cpu.build()
success = bytearray(image + bytes([0x76]) * 8192)
# The HDL fixture compresses only the half-second register delay; every CPU
# self-test and terminal-path byte stays identical to the burn image.
success[build_d0_alive.DELAY_COUNT_OFFSET] = 1
success[build_d0_alive.DELAY_COUNT_OFFSET + 1] = 0
failure = bytearray(success)
failure[metadata["signature_expected_offset"]] ^= 1
for path, data in ((Path(sys.argv[1]), success), (Path(sys.argv[2]), failure)):
    path.write_text("\n".join(f"{byte:02x}" for byte in data) + "\n")
PY
read -r success_pc failure_pc < <(
  PYTHONPATH=spinoffs/jukuravi/firmware python3 - <<'PY'
import build_d0_cpu
_, metadata = build_d0_cpu.build()
print(f"{metadata['success_halt']:04x} {metadata['fail_halt']:04x}")
PY
)
iverilog -g2012 -o "$tmp/jukuravi_d0_cpu_tb" \
  hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v hdl/sim/jukuravi_d0_cpu_tb.v
for fixture in success failure; do
  args=(+rom="$tmp/$fixture.hex" +success="$success_pc" +failure="$failure_pc")
  [[ $fixture == failure ]] && args+=(+expect_fail)
  hdl_out=$(vvp "$tmp/jukuravi_d0_cpu_tb" "${args[@]}")
  printf '%s\n' "$hdl_out"
  grep -q "JUKURAVI-D0-CPU-HDL: PASS" <<<"$hdl_out"
  if grep -q "JUKURAVI-D0-CPU-HDL: FAIL" <<<"$hdl_out"; then
    exit 1
  fi
done

python3 - "$tmp/usart-success.hex" "$tmp/usart-stuck.hex" "$tmp/usart-cpu-bad.hex" <<'PY'
from pathlib import Path
import sys

root = Path.cwd()
sys.path.insert(0, str(root / "spinoffs/jukuravi/firmware"))
import build_d0_alive
import build_d0_usart_local

image, metadata = build_d0_usart_local.build()
success = bytearray(image + bytes([0x76]) * 8192)
success[build_d0_alive.DELAY_COUNT_OFFSET] = 1
success[build_d0_alive.DELAY_COUNT_OFFSET + 1] = 0
stuck = bytearray(success)
first_timeout = metadata["timeout_offsets"][0]
stuck[first_timeout] = 1
stuck[first_timeout + 1] = 0
cpu_bad = bytearray(success)
cpu_bad[metadata["signature_expected_offset"]] ^= 1
for path, data in zip(map(Path, sys.argv[1:]), (success, stuck, cpu_bad)):
    path.write_text("\n".join(f"{byte:02x}" for byte in data) + "\n")
PY
read -r usart_success_pc usart_cpu_fail_pc usart_fail_pc < <(
  PYTHONPATH=spinoffs/jukuravi/firmware python3 - <<'PY'
import build_d0_usart_local
_, metadata = build_d0_usart_local.build()
print(f"{metadata['success_halt']:04x} {metadata['cpu_fail_halt']:04x} {metadata['usart_fail_halt']:04x}")
PY
)
iverilog -g2012 -o "$tmp/jukuravi_d0_usart_local_tb" \
  hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v \
  hdl/sim/jukuravi_d0_usart_local_tb.v
for fixture in success stuck cts-blocked cpu-bad; do
  rom_fixture=$fixture
  [[ $fixture == cts-blocked ]] && rom_fixture=stuck
  args=(+rom="$tmp/usart-$rom_fixture.hex" +success="$usart_success_pc" \
        +cpu_fail="$usart_cpu_fail_pc" +usart_fail="$usart_fail_pc")
  [[ $fixture == stuck ]] && args+=(+expect_usart_fail +inject_stuck)
  [[ $fixture == cts-blocked ]] && args+=(+expect_usart_fail +block_cts)
  [[ $fixture == cpu-bad ]] && args+=(+expect_cpu_fail)
  hdl_out=$(vvp "$tmp/jukuravi_d0_usart_local_tb" "${args[@]}")
  printf '%s\n' "$hdl_out"
  grep -q "JUKURAVI-D0-USART-LOCAL-HDL: PASS" <<<"$hdl_out"
  if grep -q "JUKURAVI-D0-USART-LOCAL-HDL: FAIL" <<<"$hdl_out"; then
    exit 1
  fi
done

python3 - "$tmp/serial-valid.hex" "$tmp/serial-timeout.hex" <<'PY'
from pathlib import Path
import sys

root = Path.cwd()
sys.path.insert(0, str(root / "spinoffs/jukuravi/firmware"))
import build_d0_alive
import build_d0_serial

image, metadata = build_d0_serial.build()
valid = bytearray(image + bytes([0x76]) * 8192)
valid[build_d0_alive.DELAY_COUNT_OFFSET] = 1
valid[build_d0_alive.DELAY_COUNT_OFFSET + 1] = 0
ok_delay = metadata["serial_ok_delay_offset"]
valid[ok_delay] = 1
valid[ok_delay + 1] = 0
timeout = bytearray(valid)
ack_timeout = metadata["ack_timeout_offsets"][0]
timeout[ack_timeout] = 1
timeout[ack_timeout + 1] = 0
for path, data in zip(map(Path, sys.argv[1:]), (valid, timeout)):
    path.write_text("\n".join(f"{byte:02x}" for byte in data) + "\n")
PY
read -r serial_ok_pc serial_dead_pc serial_checksum banner_crc ack_crc < <(
  PYTHONPATH=spinoffs/jukuravi/firmware:spinoffs/jukuravi python3 - <<'PY'
import build_d0_serial
_, metadata = build_d0_serial.build()
print(
    f"{metadata['serial_ok_halt']:04x} {metadata['serial_dead_halt']:04x} "
    f"{metadata['checksum']:04x} {metadata['banner'][-1]:02x} "
    f"{metadata['ack'][-1]:02x}"
)
PY
)
iverilog -g2012 -o "$tmp/jukuravi_d0_serial_tb" \
  hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v \
  hdl/sim/jukuravi_d0_serial_tb.v
for fixture in valid malformed timeout; do
  rom_fixture=valid
  args=(+rom="$tmp/serial-$rom_fixture.hex" +serial_ok="$serial_ok_pc" \
        +serial_dead="$serial_dead_pc" +checksum="$serial_checksum" \
        +banner_crc="$banner_crc" +ack_crc="$ack_crc")
  [[ $fixture == malformed ]] && args+=(+malformed)
  if [[ $fixture == timeout ]]; then
    args[0]=+rom="$tmp/serial-timeout.hex"
    args+=(+timeout)
  fi
  hdl_out=$(vvp "$tmp/jukuravi_d0_serial_tb" "${args[@]}")
  printf '%s\n' "$hdl_out"
  grep -q "JUKURAVI-D0-SERIAL-HDL: PASS" <<<"$hdl_out"
  if grep -q "JUKURAVI-D0-SERIAL-HDL: FAIL" <<<"$hdl_out"; then
    exit 1
  fi
done

python3 - "$tmp/ram.hex" <<'PY'
from pathlib import Path
import sys

root = Path.cwd()
sys.path.insert(0, str(root / "spinoffs/jukuravi/firmware"))
import build_d0_alive
import build_d0_ram

image, metadata = build_d0_ram.build()
fixture = bytearray(image + bytes([0x76]) * 8192)
for offset in (
    build_d0_alive.DELAY_COUNT_OFFSET,
    metadata["serial_ok_delay_offset"],
    metadata["retention_delay_offset"],
):
    fixture[offset] = 1
    fixture[offset + 1] = 0
# One page executes the exact survey loop body through the full DRAM bank.
fixture[metadata["end_page_offset"]] = build_d0_ram.SURVEY_START_PAGE
fixture[metadata["alias_end_page_offset"]] = build_d0_ram.SURVEY_START_PAGE
Path(sys.argv[1]).write_text("\n".join(f"{byte:02x}" for byte in fixture) + "\n")
PY
read -r ram_success_pc ram_checksum ram_banner_crc ram_ack_crc ram_clean_crc ram_fault_crc < <(
  PYTHONPATH=spinoffs/jukuravi/firmware:spinoffs/jukuravi python3 - <<'PY'
import build_d0_ram
import protocol

_, metadata = build_d0_ram.build()
clean = protocol.encode_frame(protocol.TYPE_RAM_BLOCK, bytes((0x40, 0x00)))[-1]
fault = protocol.encode_frame(protocol.TYPE_RAM_BLOCK, bytes((0x40, 0x08)))[-1]
print(
    f"{metadata['success_halt']:04x} {metadata['checksum']:04x} "
    f"{metadata['banner'][-1]:02x} {metadata['ack'][-1]:02x} "
    f"{clean:02x} {fault:02x}"
)
PY
)
iverilog -g2012 -o "$tmp/jukuravi_d0_ram_tb" \
  hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v \
  hdl/sim/jukuravi_d0_ram_tb.v
for fixture in clean fault; do
  block_crc=$ram_clean_crc
  args=(+rom="$tmp/ram.hex" +success="$ram_success_pc" \
        +checksum="$ram_checksum" +banner_crc="$ram_banner_crc" \
        +ack_crc="$ram_ack_crc")
  if [[ $fixture == fault ]]; then
    block_crc=$ram_fault_crc
    args+=(+inject_fault)
  fi
  args+=(+block_crc="$block_crc")
  hdl_out=$(vvp "$tmp/jukuravi_d0_ram_tb" "${args[@]}")
  printf '%s\n' "$hdl_out"
  grep -q "JUKURAVI-D0-RAM-HDL: PASS" <<<"$hdl_out"
  if grep -q "JUKURAVI-D0-RAM-HDL: FAIL" <<<"$hdl_out"; then
    exit 1
  fi
done

python3 - "$tmp/ram-fallback.hex" <<'PY'
from pathlib import Path
import sys

root = Path.cwd()
sys.path.insert(0, str(root / "spinoffs/jukuravi/firmware"))
import build_d0_alive
import build_d0_ram_fallback

image, metadata = build_d0_ram_fallback.build()
fixture = bytearray(image + bytes([0x76]) * 8192)
for offset in (
    build_d0_alive.DELAY_COUNT_OFFSET,
    metadata["ack_timeout_offsets"][0],
    metadata["serial_dead_mark_delay_offset"],
    *metadata["fallback_retention_offsets"],
    *metadata["windows_pulse_offsets"],
    *metadata["chip_pulse_offsets"],
):
    fixture[offset] = 1
    fixture[offset + 1] = 0
for offset in metadata["fallback_count_offsets"]:
    fixture[offset] = 0
    fixture[offset + 1] = 1  # 0100h: one page per candidate window
Path(sys.argv[1]).write_text("\n".join(f"{byte:02x}" for byte in fixture) + "\n")
PY
read -r fallback_found_pc fallback_dead_pc fallback_checksum fallback_banner_crc < <(
  PYTHONPATH=spinoffs/jukuravi/firmware python3 - <<'PY'
import build_d0_ram_fallback
_, metadata = build_d0_ram_fallback.build()
print(
    f"{metadata['windows_found_halt']:04x} {metadata['no_windows_halt']:04x} "
    f"{metadata['checksum']:04x} {metadata['banner'][-1]:02x}"
)
PY
)
iverilog -g2012 -o "$tmp/jukuravi_d0_ram_fallback_tb" \
  hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v \
  hdl/sim/jukuravi_d0_ram_fallback_tb.v
for fixture in clean fault; do
  args=(+rom="$tmp/ram-fallback.hex" +windows_found="$fallback_found_pc" \
        +no_windows="$fallback_dead_pc" +checksum="$fallback_checksum" \
        +banner_crc="$fallback_banner_crc")
  [[ $fixture == fault ]] && args+=(+inject_fault)
  hdl_out=$(vvp "$tmp/jukuravi_d0_ram_fallback_tb" "${args[@]}")
  printf '%s\n' "$hdl_out"
  grep -q "JUKURAVI-D0-RAM-FALLBACK-HDL: PASS" <<<"$hdl_out"
  if grep -q "JUKURAVI-D0-RAM-FALLBACK-HDL: FAIL" <<<"$hdl_out"; then
    exit 1
  fi
done

python3 - "$tmp/romcheck-clean.hex" "$tmp/romcheck-corrupt.hex" <<'PY'
from pathlib import Path
import sys

root = Path.cwd()
sys.path.insert(0, str(root / "spinoffs/jukuravi/firmware"))
import build_d0_romcheck

image, metadata = build_d0_romcheck.build()
clean = bytearray(image + bytes([0x76]) * 8192)
# Compress only the already-guarded alive delay. Since that immediate is in
# block 1, regenerate the fixture's historical stored sum before injection.
alive = int(metadata["alive_delay_offset"])
clean[alive] = 1
clean[alive + 1] = 0
offset = int(metadata["rom_checksum_offset"])
start = int(metadata["rom_checksum_start"])
end = int(metadata["rom_checksum_end"])
clean[offset] = sum(clean[start:end]) & 0xFF
corrupt = bytearray(clean)
corrupt[int(metadata["rom_fault_offset"])] ^= 1
for path, data in zip(map(Path, sys.argv[1:]), (clean, corrupt)):
    path.write_text("\n".join(f"{byte:02x}" for byte in data) + "\n")
PY
romcheck_fail_pc=$(
  PYTHONPATH=spinoffs/jukuravi/firmware python3 - <<'PY'
import build_d0_romcheck
_, metadata = build_d0_romcheck.build()
print(f"{metadata['rom_fail_halt']:04x}")
PY
)
iverilog -g2012 -o "$tmp/jukuravi_d0_romcheck_tb" \
  hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v \
  hdl/sim/jukuravi_d0_romcheck_tb.v
for fixture in clean corrupt; do
  args=(+rom="$tmp/romcheck-$fixture.hex" +rom_fail="$romcheck_fail_pc")
  [[ $fixture == corrupt ]] && args+=(+expect_fail)
  hdl_out=$(vvp "$tmp/jukuravi_d0_romcheck_tb" "${args[@]}")
  printf '%s\n' "$hdl_out"
  grep -q "JUKURAVI-D0-ROMCHECK-HDL: PASS" <<<"$hdl_out"
  if grep -q "JUKURAVI-D0-ROMCHECK-HDL: FAIL" <<<"$hdl_out"; then
    exit 1
  fi
done

python3 - "$tmp/pic.hex" <<'PY'
from pathlib import Path
import sys

root = Path.cwd()
sys.path.insert(0, str(root / "spinoffs/jukuravi/firmware"))
import build_d0_pic

image, metadata = build_d0_pic.build()
fixture = bytearray(image + bytes([0x76]) * 8192)
alive = int(metadata["alive_delay_offset"])
fixture[alive] = 1
fixture[alive + 1] = 0
offset = int(metadata["rom_checksum_offset"])
start = int(metadata["rom_checksum_start"])
end = int(metadata["rom_checksum_end"])
fixture[offset] = sum(fixture[start:end]) & 0xFF
Path(sys.argv[1]).write_text("\n".join(f"{byte:02x}" for byte in fixture) + "\n")
PY
pic_fail_pc=$(
  PYTHONPATH=spinoffs/jukuravi/firmware python3 - <<'PY'
import build_d0_pic
_, metadata = build_d0_pic.build()
print(f"{metadata['pic_fail_halt']:04x}")
PY
)
iverilog -g2012 -o "$tmp/jukuravi_d0_pic_tb" \
  hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v \
  hdl/sim/jukuravi_d0_pic_tb.v
for fixture in clean fault; do
  args=(+rom="$tmp/pic.hex" +pic_fail="$pic_fail_pc")
  [[ $fixture == fault ]] && args+=(+inject_fault)
  hdl_out=$(vvp "$tmp/jukuravi_d0_pic_tb" "${args[@]}")
  printf '%s\n' "$hdl_out"
  grep -q "JUKURAVI-D0-PIC-HDL: PASS" <<<"$hdl_out"
  if grep -q "JUKURAVI-D0-PIC-HDL: FAIL" <<<"$hdl_out"; then
    exit 1
  fi
done

python3 - "$tmp/ppi.hex" "$tmp/ppi-fallback.hex" <<'PY'
from pathlib import Path
import sys

root = Path.cwd()
sys.path.insert(0, str(root / "spinoffs/jukuravi/firmware"))
import build_d0_ppi
import build_d0_ram_fallback

image, metadata = build_d0_ppi.build()
early = bytearray(image + bytes([0x76]) * 8192)
alive = int(metadata["alive_delay_offset"])
early[alive] = 1
early[alive + 1] = 0
checksum_offset = int(metadata["rom_checksum_offset"])
checksum_start = int(metadata["rom_checksum_start"])
checksum_end = int(metadata["rom_checksum_end"])
early[checksum_offset] = sum(early[checksum_start:checksum_end]) & 0xFF

fallback = bytearray(early)
for offset in (
    metadata["ack_timeout_offsets"][0],
    metadata["serial_dead_mark_delay_offset"],
    *metadata["fallback_retention_offsets"],
    *metadata["windows_pulse_offsets"],
    *metadata["chip_pulse_offsets"],
):
    fallback[offset] = 1
    fallback[offset + 1] = 0
for offset in metadata["fallback_count_offsets"]:
    fallback[offset] = 0
    fallback[offset + 1] = 1  # 0100h: one page per candidate window
for offset in metadata["fallback_rewind_offsets"]:
    fallback[offset] = 1      # rewind one page after each shortened pass
first_start = build_d0_ram_fallback.FALLBACK_WINDOWS[0][0]
for offset in metadata["fallback_first_end_page_offsets"]:
    fallback[offset] = (first_start + 0x100) >> 8
fallback[checksum_offset] = sum(fallback[checksum_start:checksum_end]) & 0xFF

for path, data in zip(map(Path, sys.argv[1:]), (early, fallback)):
    path.write_text("\n".join(f"{byte:02x}" for byte in data) + "\n")
PY
read -r ppi_fail_pc ppi_found_pc ppi_dead_pc ppi_checksum ppi_banner_crc < <(
  PYTHONPATH=spinoffs/jukuravi/firmware python3 - <<'PY'
import build_d0_ppi
_, metadata = build_d0_ppi.build()
print(
    f"{metadata['ppi_fail_halt']:04x} {metadata['windows_found_halt']:04x} "
    f"{metadata['no_windows_halt']:04x} {metadata['checksum']:04x} "
    f"{metadata['banner'][-1]:02x}"
)
PY
)
iverilog -g2012 -o "$tmp/jukuravi_d0_ppi_tb" \
  hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v \
  hdl/sim/jukuravi_d0_ppi_tb.v
for fixture in clean fault; do
  args=(+rom="$tmp/ppi.hex" +ppi_fail="$ppi_fail_pc")
  [[ $fixture == fault ]] && args+=(+inject_fault)
  hdl_out=$(vvp "$tmp/jukuravi_d0_ppi_tb" "${args[@]}")
  printf '%s\n' "$hdl_out"
  grep -q "JUKURAVI-D0-PPI-HDL: PASS" <<<"$hdl_out"
  if grep -q "JUKURAVI-D0-PPI-HDL: FAIL" <<<"$hdl_out"; then
    exit 1
  fi
done

# Reuse the fixed-window top-level fixture for the version-6 shared loop. Its
# six count, five rewind, and one first-end sentinel immediates are all patched
# together, so the one-page fixture preserves the burn image's two-window flow.
for fixture in clean fault; do
  args=(+rom="$tmp/ppi-fallback.hex" +windows_found="$ppi_found_pc" \
        +no_windows="$ppi_dead_pc" +checksum="$ppi_checksum" \
        +banner_crc="$ppi_banner_crc" +rom_version=06 +prefix_writes=16)
  [[ $fixture == fault ]] && args+=(+inject_fault)
  hdl_out=$(vvp "$tmp/jukuravi_d0_ram_fallback_tb" "${args[@]}")
  printf '%s\n' "$hdl_out"
  grep -q "JUKURAVI-D0-RAM-FALLBACK-HDL: PASS" <<<"$hdl_out"
  if grep -q "JUKURAVI-D0-RAM-FALLBACK-HDL: FAIL" <<<"$hdl_out"; then
    exit 1
  fi
done

python3 - "$tmp/pit.hex" "$tmp/pit-corrupt.hex" "$tmp/pit-fallback.hex" <<'PY'
from pathlib import Path
import sys

root = Path.cwd()
sys.path.insert(0, str(root / "spinoffs/jukuravi/firmware"))
import build_d0_alive
import build_d0_pit
import build_d0_ram_fallback

image, metadata = build_d0_pit.build()
early = bytearray(image + bytes([0x76]) * 8192)
alive = int(metadata["alive_delay_offset"])
early[alive] = 1
early[alive + 1] = 0
checksum_offset = int(metadata["rom_checksum_offset"])
checksum_start = int(metadata["rom_checksum_start"])
checksum_end = int(metadata["rom_checksum_end"])
early[checksum_offset] = sum(early[checksum_start:checksum_end]) & 0xFF

corrupt = bytearray(early)
corrupt[int(metadata["pit_extension_start"])] ^= 1

fallback = bytearray(early)
for offset in (
    metadata["ack_timeout_offsets"][0],
    metadata["serial_dead_mark_delay_offset"],
    *metadata["fallback_retention_offsets"],
    *metadata["windows_pulse_offsets"],
    *metadata["chip_pulse_offsets"],
):
    fallback[offset] = 1
    fallback[offset + 1] = 0
for offset in metadata["fallback_count_offsets"]:
    fallback[offset] = 0
    fallback[offset + 1] = 1  # 0100h: one page per candidate window
for offset in metadata["fallback_rewind_offsets"]:
    fallback[offset] = 1      # rewind one page after each shortened pass
first_start = build_d0_ram_fallback.FALLBACK_WINDOWS[0][0]
for offset in metadata["fallback_first_end_page_offsets"]:
    fallback[offset] = (first_start + 0x100) >> 8
fallback[checksum_offset] = sum(fallback[checksum_start:checksum_end]) & 0xFF

for path, data in zip(map(Path, sys.argv[1:]), (early, corrupt, fallback)):
    path.write_text("\n".join(f"{byte:02x}" for byte in data) + "\n")
PY
read -r pit_fail_pc pit_rom_fail_pc pit_found_pc pit_dead_pc pit_checksum pit_banner_crc < <(
  PYTHONPATH=spinoffs/jukuravi/firmware python3 - <<'PY'
import build_d0_pit
_, metadata = build_d0_pit.build()
print(
    f"{metadata['pit_fail_halt']:04x} {metadata['rom_fail_halt']:04x} "
    f"{metadata['windows_found_halt']:04x} {metadata['no_windows_halt']:04x} "
    f"{metadata['checksum']:04x} {metadata['banner'][-1]:02x}"
)
PY
)
iverilog -g2012 -o "$tmp/jukuravi_d0_pit_tb" \
  hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v \
  hdl/sim/jukuravi_d0_pit_tb.v
for fixture in clean fault extension-corrupt; do
  rom_fixture=pit
  args=(+rom="$tmp/$rom_fixture.hex" +pit_fail="$pit_fail_pc" \
        +rom_fail="$pit_rom_fail_pc")
  [[ $fixture == fault ]] && args+=(+inject_fault)
  if [[ $fixture == extension-corrupt ]]; then
    args[0]=+rom="$tmp/pit-corrupt.hex"
    args+=(+extension_fault)
  fi
  hdl_out=$(vvp "$tmp/jukuravi_d0_pit_tb" "${args[@]}")
  printf '%s\n' "$hdl_out"
  grep -q "JUKURAVI-D0-PIT-HDL: PASS" <<<"$hdl_out"
  if grep -q "JUKURAVI-D0-PIT-HDL: FAIL" <<<"$hdl_out"; then
    exit 1
  fi
done

# Version 7 enters the same fixed-window fallback after the guarded PIT survey.
# The one-page fixture keeps that cumulative predecessor sequence exact.
for fixture in clean fault; do
  args=(+rom="$tmp/pit-fallback.hex" +windows_found="$pit_found_pc" \
        +no_windows="$pit_dead_pc" +checksum="$pit_checksum" \
        +banner_crc="$pit_banner_crc" +rom_version=07 +prefix_writes=56 \
        +prefix_pit_writes=24 +prefix_silences=1)
  [[ $fixture == fault ]] && args+=(+inject_fault)
  hdl_out=$(vvp "$tmp/jukuravi_d0_ram_fallback_tb" "${args[@]}")
  printf '%s\n' "$hdl_out"
  grep -q "JUKURAVI-D0-RAM-FALLBACK-HDL: PASS" <<<"$hdl_out"
  if grep -q "JUKURAVI-D0-RAM-FALLBACK-HDL: FAIL" <<<"$hdl_out"; then
    exit 1
  fi
done

python3 - "$tmp/framebuffer.hex" "$tmp/framebuffer-fallback.hex" <<'PY'
from pathlib import Path
import sys

root = Path.cwd()
sys.path.insert(0, str(root / "spinoffs/jukuravi/firmware"))
import build_d0_framebuffer
import build_d0_ram_fallback

image, metadata = build_d0_framebuffer.build()
early = bytearray(image + bytes([0x76]) * 8192)
for offset in (
    metadata["alive_delay_offset"], metadata["serial_ok_delay_offset"],
    metadata["retention_delay_offset"],
):
    early[offset] = 1
    early[offset + 1] = 0
for key in (
    "start_page_offset", "end_page_offset",
    "alias_start_page_offset", "alias_end_page_offset",
):
    early[metadata[key]] = 0xD8
for offset in metadata["framebuffer_count_offsets"]:
    early[offset] = 0x40
    early[offset + 1] = 0x01  # 0140h: eight 40-byte raster rows
early[metadata["framebuffer_extension_checksum_offset"]] = sum(
    early[metadata["framebuffer_extension_start"]:metadata["framebuffer_extension_end"]]
) & 0xFF
early[metadata["pit_extension_checksum_offset"]] = sum(
    early[metadata["pit_extension_start"]:metadata["pit_extension_end"]]
) & 0xFF
checksum_offset = int(metadata["rom_checksum_offset"])
checksum_start = int(metadata["rom_checksum_start"])
checksum_end = int(metadata["rom_checksum_end"])
early[checksum_offset] = sum(early[checksum_start:checksum_end]) & 0xFF

fallback = bytearray(image + bytes([0x76]) * 8192)
alive = int(metadata["alive_delay_offset"])
fallback[alive] = 1
fallback[alive + 1] = 0
for offset in (
    metadata["ack_timeout_offsets"][0],
    metadata["serial_dead_mark_delay_offset"],
    *metadata["fallback_retention_offsets"],
    *metadata["windows_pulse_offsets"],
    *metadata["chip_pulse_offsets"],
):
    fallback[offset] = 1
    fallback[offset + 1] = 0
for offset in metadata["fallback_count_offsets"]:
    fallback[offset] = 0
    fallback[offset + 1] = 1
for offset in metadata["fallback_rewind_offsets"]:
    fallback[offset] = 1
first_start = build_d0_ram_fallback.FALLBACK_WINDOWS[0][0]
for offset in metadata["fallback_first_end_page_offsets"]:
    fallback[offset] = (first_start + 0x100) >> 8
fallback[checksum_offset] = sum(fallback[checksum_start:checksum_end]) & 0xFF

for path, data in zip(map(Path, sys.argv[1:]), (early, fallback)):
    path.write_text("\n".join(f"{byte:02x}" for byte in data) + "\n")
PY
read -r framebuffer_success_pc framebuffer_fail_pc framebuffer_found_pc framebuffer_dead_pc framebuffer_checksum framebuffer_banner_crc framebuffer_ack_crc framebuffer_clean_crc framebuffer_fault_crc < <(
  PYTHONPATH=spinoffs/jukuravi/firmware:spinoffs/jukuravi python3 - <<'PY'
import build_d0_framebuffer
import protocol

_, metadata = build_d0_framebuffer.build()
clean_crc = protocol.encode_frame(protocol.TYPE_RAM_BLOCK, bytes((0xD8, 0x00)))[-1]
fault_crc = protocol.encode_frame(protocol.TYPE_RAM_BLOCK, bytes((0xD8, 0x01)))[-1]
print(
    f"{metadata['framebuffer_success_halt']:04x} "
    f"{metadata['framebuffer_fail_halt']:04x} "
    f"{metadata['windows_found_halt']:04x} {metadata['no_windows_halt']:04x} "
    f"{metadata['checksum']:04x} {metadata['banner'][-1]:02x} "
    f"{metadata['ack'][-1]:02x} {clean_crc:02x} {fault_crc:02x}"
)
PY
)
iverilog -g2012 -o "$tmp/jukuravi_d0_framebuffer_tb" \
  hdl/vendor/vm80a.v hdl/devices.v hdl/juku_top.v \
  hdl/sim/jukuravi_d0_framebuffer_tb.v
for fixture in clean fault; do
  block_crc=$framebuffer_clean_crc
  args=(+rom="$tmp/framebuffer.hex" +success="$framebuffer_success_pc" \
        +failure="$framebuffer_fail_pc" +checksum="$framebuffer_checksum" \
        +banner_crc="$framebuffer_banner_crc" +ack_crc="$framebuffer_ack_crc")
  if [[ $fixture == fault ]]; then
    block_crc=$framebuffer_fault_crc
    args+=(+inject_fault)
  fi
  args+=(+block_crc="$block_crc")
  hdl_out=$(vvp "$tmp/jukuravi_d0_framebuffer_tb" "${args[@]}")
  printf '%s\n' "$hdl_out"
  grep -q "JUKURAVI-D0-FRAMEBUFFER-HDL: PASS" <<<"$hdl_out"
  if grep -q "JUKURAVI-D0-FRAMEBUFFER-HDL: FAIL" <<<"$hdl_out"; then
    exit 1
  fi
done

# Version 8 retains the version-7 no-ACK flow after validating both extensions.
for fixture in clean fault; do
  args=(+rom="$tmp/framebuffer-fallback.hex" \
        +windows_found="$framebuffer_found_pc" +no_windows="$framebuffer_dead_pc" \
        +checksum="$framebuffer_checksum" +banner_crc="$framebuffer_banner_crc" \
        +rom_version=08 +prefix_writes=56 +prefix_pit_writes=24 \
        +prefix_silences=1)
  [[ $fixture == fault ]] && args+=(+inject_fault)
  hdl_out=$(vvp "$tmp/jukuravi_d0_ram_fallback_tb" "${args[@]}")
  printf '%s\n' "$hdl_out"
  grep -q "JUKURAVI-D0-RAM-FALLBACK-HDL: PASS" <<<"$hdl_out"
  if grep -q "JUKURAVI-D0-RAM-FALLBACK-HDL: FAIL" <<<"$hdl_out"; then
    exit 1
  fi
done
./sync/beeper_check.sh
