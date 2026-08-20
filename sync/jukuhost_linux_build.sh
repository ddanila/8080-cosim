#!/usr/bin/env bash
# Build the native Linux Juku host without introducing a second build system.
set -euo pipefail
cd "$(dirname "$0")/.."
CC=${CC:-cc}
mkdir -p build
"$CC" -std=c99 -O2 -pedantic -Wall -Wextra -Werror -Wconversion -Wshadow \
  -D_DEFAULT_SOURCE -Ihost/include -Ihost/src \
  host/src/jukuhost_core.c host/src/jukuhost_bootstrap.c \
  host/src/jukuhost_evidence.c host/src/jukuhost_media.c \
  host/src/jukuhost_service.c host/src/jukuhost_session.c \
  host/src/platform_posix.c host/src/jukuhost_posix.c \
  -o build/jukuhost
build/jukuhost --version
