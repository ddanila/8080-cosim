#!/usr/bin/env python3
"""Generate and compare exhaustive-opcode C/vm80a instruction vectors."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


BOUNDARY = (0x00, 0x01, 0x0F, 0x10, 0x7F, 0x80, 0xFE, 0xFF)


def generate_vectors(path: Path) -> int:
    lines: list[str] = []
    index = 0
    for opcode in range(256):
        for flags in range(32):
            value = BOUNDARY[(opcode + flags) & 7]
            inverse = value ^ 0xFF
            has_word_operand = (
                opcode in (0xC3, 0xCB, 0xCD, 0xDD, 0xED, 0xFD)
                or opcode & 0xC7 in (0xC2, 0xC4)
            )
            op1 = 0x56 if has_word_operand else value
            op2 = 0x34 if op1 == 0x56 else inverse
            a = value
            bc = ((inverse << 8) | BOUNDARY[(opcode + flags + 1) & 7]) & 0xFFFF
            de = (0x5000 | ((opcode << 1) & 0x0FFE)) & 0xFFFF
            hl = (0x4000 | ((flags << 4) + (opcode & 0x0F))) & 0xFFFF
            sp = (0x9000 | ((flags << 4) + (opcode & 0x0F))) & 0xFFFE
            iff = (opcode ^ flags) & 1
            mem_hl = BOUNDARY[(opcode + flags + 3) & 7]
            # RET/POP receive a controlled target/value; PUSH/CALL overwrite it.
            stack_lo = 0x56
            stack_hi = 0x34
            lines.append(
                f"{index:x} {opcode:02x} {flags:02x} {op1:02x} {op2:02x} "
                f"{a:02x} {bc:04x} {de:04x} {hl:04x} {sp:04x} {iff:x} "
                f"{mem_hl:02x} {stack_lo:02x} {stack_hi:02x}\n"
            )
            index += 1
    path.write_text("".join(lines), encoding="ascii")
    return index


def normalized(output: str) -> list[str]:
    """Canonicalize architectural effects; physical write order may differ."""
    results: dict[int, str] = {}
    writes: dict[int, dict[int, int]] = {}
    io: dict[int, list[tuple[int, int]]] = {}
    for raw in output.splitlines():
        line = raw.strip().lower()
        fields = line.split()
        if not fields:
            continue
        if fields[0] == "result":
            results[int(fields[1])] = line
        elif fields[0] == "write":
            writes.setdefault(int(fields[1]), {})[int(fields[2], 16)] = int(fields[3], 16)
        elif fields[0] == "ioout":
            io.setdefault(int(fields[1]), []).append((int(fields[2], 16), int(fields[3], 16)))
    canonical: list[str] = []
    for index in sorted(results):
        canonical.append(results[index])
        canonical.extend(f"write {index} {address:04x} {value:02x}"
                         for address, value in sorted(writes.get(index, {}).items()))
        canonical.extend(f"ioout {index} {port:02x} {value:02x}"
                         for port, value in io.get(index, []))
    return canonical


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=False)


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {Path(sys.argv[0]).name} C_RUNNER HDL_VVP", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="i8080-vm80a-diff-") as tmp_name:
        vectors = Path(tmp_name) / "instructions.vec"
        count = generate_vectors(vectors)
        c_proc = run([str(Path(sys.argv[1]).resolve()), str(vectors)])
        hdl_proc = run(["vvp", str(Path(sys.argv[2]).resolve()), f"+vectors={vectors}"])
    if c_proc.returncode or hdl_proc.returncode:
        print(f"I8080-VM80A-DIFF: FAIL runner exit C={c_proc.returncode} "
              f"HDL={hdl_proc.returncode}", file=sys.stderr)
        if c_proc.stderr:
            print(f"C stderr: {c_proc.stderr}", file=sys.stderr)
        if hdl_proc.stderr:
            print(f"HDL stderr: {hdl_proc.stderr}", file=sys.stderr)
        return 1
    c_lines = normalized(c_proc.stdout)
    hdl_lines = normalized(hdl_proc.stdout)
    if c_lines != hdl_lines:
        mismatch = next((i for i, pair in enumerate(zip(c_lines, hdl_lines))
                         if pair[0] != pair[1]), min(len(c_lines), len(hdl_lines)))
        print(f"I8080-VM80A-DIFF: FAIL transcript mismatch at line {mismatch}", file=sys.stderr)
        print(f"C:   {c_lines[mismatch] if mismatch < len(c_lines) else '<end>'}", file=sys.stderr)
        print(f"HDL: {hdl_lines[mismatch] if mismatch < len(hdl_lines) else '<end>'}", file=sys.stderr)
        return 1
    results = sum(line.startswith("result ") for line in c_lines)
    if results != count:
        print(f"I8080-VM80A-DIFF: FAIL expected {count} results, got {results}", file=sys.stderr)
        return 1
    print(f"I8080-VM80A-DIFF: PASS ({count} one-instruction cases; all 256 opcodes x "
          "all 32 S/Z/AC/P/C flag combinations, boundary-pattern registers/operands, "
          "memory writes and port I/O)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
