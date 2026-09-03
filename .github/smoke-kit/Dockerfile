FROM ubuntu:24.04 AS build

RUN apt-get update \
    && apt-get install --no-install-recommends --yes build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY cosim /src/cosim
COPY host /src/host

RUN mkdir -p /opt/8080-cosim/bin \
    && cc -O2 -Wall -Wextra -I/src/cosim \
        -o /opt/8080-cosim/bin/trace \
        /src/cosim/trace.c \
        /src/cosim/i8080.c \
        /src/cosim/juk_disk.c \
        /src/cosim/juku_fdc.c

RUN cc -std=c99 -O2 -pedantic -Wall -Wextra -Werror -Wconversion -Wshadow \
        -D_DEFAULT_SOURCE -static -I/src/host/include -I/src/host/src \
        /src/host/src/jukuhost_core.c \
        /src/host/src/jukuhost_bootstrap.c \
        /src/host/src/jukuhost_config.c \
        /src/host/src/jukuhost_evidence.c \
        /src/host/src/jukuhost_media.c \
        /src/host/src/jukuhost_service.c \
        /src/host/src/jukuhost_session.c \
        /src/host/src/jukuhost_sha256.c \
        /src/host/src/platform_file.c \
        /src/host/src/platform_posix.c \
        /src/host/src/jukuhost_runner.c \
        /src/host/src/jukuhost_main.c \
        -o /opt/8080-cosim/bin/jukuhost \
    && /opt/8080-cosim/bin/jukuhost --selftest

FROM scratch

COPY --from=build /opt/8080-cosim /opt/8080-cosim
COPY tests /opt/8080-cosim/tests
COPY spinoffs /opt/8080-cosim/spinoffs
COPY smoke-kit.json /opt/8080-cosim/smoke-kit.json
