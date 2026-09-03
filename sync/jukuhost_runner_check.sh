#!/usr/bin/env bash
# Verify the frontend-neutral production runner and its callback boundary.
set -euo pipefail

project_root=$(cd "$(dirname "$0")/.." && pwd)
cc_bin=${CC:-cc}
output_dir="$project_root/build/runner-test"

mkdir -p "$output_dir"
"$cc_bin" -std=c99 -O2 -pedantic -Wall -Wextra -Werror -Wconversion \
  -Wshadow -D_DEFAULT_SOURCE -DJH_NO_MAIN \
  -I"$project_root/host/include" -I"$project_root/host/src" \
  "$project_root/host/src/jukuhost_core.c" \
  "$project_root/host/src/jukuhost_bootstrap.c" \
  "$project_root/host/src/jukuhost_config.c" \
  "$project_root/host/src/jukuhost_evidence.c" \
  "$project_root/host/src/jukuhost_media.c" \
  "$project_root/host/src/jukuhost_service.c" \
  "$project_root/host/src/jukuhost_session.c" \
  "$project_root/host/src/jukuhost_sha256.c" \
  "$project_root/host/src/platform_file.c" \
  "$project_root/host/src/platform_posix.c" \
  "$project_root/host/src/jukuhost_runner.c" \
  "$project_root/host/tests/runner_test.c" \
  -o "$output_dir/runner_test"
"$output_dir/runner_test"
