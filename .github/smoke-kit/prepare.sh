#!/usr/bin/env bash
# Prepare the same minimal build context locally and in publishing CI.
set -euo pipefail
cd "$(dirname "$0")/../.."
context=${1:?usage: prepare.sh DESTINATION}
mkdir -p "$context/cosim" "$context/host" "$context/tests/fixtures" \
  "$context/spinoffs/jukuravi/remix" "$context/spinoffs/jukuravi/network-rom" \
  "$context/third_party/dac-emulation" "$context/licenses"
cp cosim/*.c cosim/*.h "$context/cosim/"
# Export the pinned checkout without .git, local build output, or test artifacts.
git -C third_party/dac-emulation archive HEAD | tar -x -C "$context/third_party/dac-emulation"
git -C third_party/dac-emulation rev-parse HEAD > "$context/dac-emulation-revision"
cp third_party/dac-emulation/LICENSE "$context/licenses/dac-emulation-MIT.txt"
cp third_party/dac-emulation/NOTICE "$context/licenses/dac-emulation-NOTICE.txt"
cp third_party/dac-emulation/third_party/cpu/i8080/I8080_LICENSE "$context/licenses/i8080-MIT.txt"
cp -R host/include host/src "$context/host/"
cp tests/fixtures/*.py "$context/tests/fixtures/"
cp spinoffs/jukuravi/remix/ekta4401.bin spinoffs/jukuravi/remix/ekta4402.bin \
  "$context/spinoffs/jukuravi/remix/"
cp spinoffs/jukuravi/network-rom/juku-network-rom-abi1.bin "$context/spinoffs/jukuravi/network-rom/"
cp .github/smoke-kit/Dockerfile .github/smoke-kit/smoke-kit.json "$context/"
