FROM ubuntu:24.04 AS build

RUN apt-get update \
    && apt-get install --no-install-recommends --yes build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY cosim /src/cosim

RUN mkdir -p /opt/8080-cosim/bin \
    && cc -O2 -Wall -Wextra -I/src/cosim \
        -o /opt/8080-cosim/bin/trace \
        /src/cosim/trace.c \
        /src/cosim/i8080.c \
        /src/cosim/juk_disk.c \
        /src/cosim/juku_fdc.c

FROM scratch

COPY --from=build /opt/8080-cosim /opt/8080-cosim
COPY tools /opt/8080-cosim/tools
COPY spinoffs /opt/8080-cosim/spinoffs
COPY smoke-kit.json /opt/8080-cosim/smoke-kit.json
