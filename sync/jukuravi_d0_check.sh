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
"$CC" -std=c11 -O2 -Wall -Wextra -Werror -I cosim \
  -o "$tmp/trace" \
  cosim/trace.c cosim/i8080.c cosim/juku_fdc.c cosim/juk_disk.c
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

command -v iverilog >/dev/null || { echo "iverilog not found"; exit 2; }
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
./sync/beeper_check.sh
