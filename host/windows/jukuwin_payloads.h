#ifndef JUKUWIN_PAYLOADS_H
#define JUKUWIN_PAYLOADS_H

#include <stddef.h>
#include <stdint.h>

#include "jukuhost_runner.h"

struct jh_jukuwin_payload {
    const char *symbol;
    const char *mode;
    const char *role;
    const char *format;
    const uint8_t *bytes;
    size_t length;
    struct jh_config_artifact identity;
};

extern const struct jh_jukuwin_payload jh_jukuwin_payload_catalog[];
extern const size_t jh_jukuwin_payload_catalog_count;
extern const char jh_jukuwin_payload_source_revision[];

const struct jh_jukuwin_payload *jh_jukuwin_payload_find(
    const char *mode, const char *role);
int jh_jukuwin_payloads_selftest(char *message, size_t capacity);
int jh_jukuwin_apply_payloads(const char *mode,
                              struct jh_host_options *options);

#endif
