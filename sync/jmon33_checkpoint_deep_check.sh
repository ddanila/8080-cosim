#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")/.."

./sync/jmon33_checkpoint_cursor_probe.py
./sync/jmon33_hdl_a_command_probe.py
./sync/jmon33_hdl_b_command_probe.py
./sync/jmon33_hdl_fdc_command_probe.py

git diff --exit-code -- \
  docs/jmon33-hdl-command-probe.md \
  docs/jmon33-hdl-b-command-probe.md \
  docs/jmon33-hdl-fdc-command-probe.md
