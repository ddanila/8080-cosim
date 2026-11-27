#!/usr/bin/env bash
# Source this file to select the pinned upstream Open Watcom V2 toolchain.

ow_project_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
export WATCOM="$ow_project_root/.tools/open-watcom-v2-20260801"
export INCLUDE="$WATCOM/h"
export PATH="$WATCOM/binl64:$PATH"
