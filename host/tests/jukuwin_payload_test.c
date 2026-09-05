#include "jukuhost_runner.h"
#include "jukuwin_payloads.h"

#include <stdio.h>
#include <string.h>

int main(void)
{
    struct jh_host_options options;
    char message[128];
    const struct jh_jukuwin_payload *payload;

    if (jh_jukuwin_payloads_selftest(message, sizeof(message)) != JH_OK) {
        fprintf(stderr, "payload selftest failed: %s\n", message);
        return 1;
    }
    payload = jh_jukuwin_payload_find("stock", "fastboot");
    if (payload == NULL || payload->length != 9704u ||
            strcmp(payload->format, "JF17") != 0) {
        fprintf(stderr, "stock payload lookup differs\n");
        return 1;
    }
    payload = jh_jukuwin_payload_find("stock", "system");
    if (payload == NULL) return 1;
    {
        /* The loader and CP/M adapter both need 9600. The old embedded
         * adapter switched back to 19200 and stalled physical CS00014. */
        static const uint8_t good[] = {0x3e, 0x1f, 0xd3, 0x1b, 0x3e, 8, 0xd3, 0x18};
        static const uint8_t bad[] = {0x3e, 0x15, 0xd3, 0x1b, 0x3e, 4, 0xd3, 0x18};
        size_t offset;
        int found = 0;
        for (offset = 512u; offset + sizeof(good) <= payload->length; ++offset) {
            if (memcmp(payload->bytes + offset, bad, sizeof(bad)) == 0) {
                fprintf(stderr, "stock CP/M adapter still selects 19200\n");
                return 1;
            }
            if (memcmp(payload->bytes + offset, good, sizeof(good)) == 0) found = 1;
        }
        if (!found) {
            fprintf(stderr, "stock CP/M adapter lacks explicit 9600 setup\n");
            return 1;
        }
    }
    payload = jh_jukuwin_payload_find("c11", "fastboot");
    if (payload == NULL || payload->length != 7914u ||
            strcmp(payload->format, "JF16") != 0) {
        fprintf(stderr, "C11 payload lookup differs\n");
        return 1;
    }
    payload = jh_jukuwin_payload_find("c12", "system");
    if (payload == NULL || payload->length != 18432u ||
            strcmp(payload->format, "JUKURM1") != 0) {
        fprintf(stderr, "C12 payload lookup differs\n");
        return 1;
    }
    memset(&options, 0, sizeof(options));
    if (jh_jukuwin_apply_payloads("stock", &options) != JH_OK ||
            options.direct_fastboot || !options.recover_session ||
            options.disk_baud != 9600u ||
            options.system_length != 16896u ||
            options.fast_stage_length != 9704u) {
        fprintf(stderr, "stock payload application differs\n");
        return 1;
    }
    memset(&options, 0, sizeof(options));
    if (jh_jukuwin_apply_payloads("c11", &options) != JH_OK ||
            !options.direct_fastboot || !options.recover_session ||
            options.disk_baud != 19200u ||
            options.system_length != 18432u ||
            options.fast_stage_length != 7914u) {
        fprintf(stderr, "C11 payload application differs\n");
        return 1;
    }
    memset(&options, 0, sizeof(options));
    if (jh_jukuwin_apply_payloads("c12", &options) != JH_OK ||
            !options.direct_fastboot || !options.recover_session ||
            options.disk_baud != 19200u ||
            options.system_length != 18432u ||
            options.fast_stage_length != 7914u) {
        fprintf(stderr, "C12 payload application differs\n");
        return 1;
    }
    if (jh_jukuwin_apply_payloads("unknown", &options) !=
            JH_ERR_UNSUPPORTED) {
        fprintf(stderr, "unknown payload mode accepted\n");
        return 1;
    }
    printf("JUKUWIN-PAYLOAD-TEST: PASS (%s)\n", message);
    return 0;
}
