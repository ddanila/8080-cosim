#include "jukuhost_runner.h"
#include "jukuwin_payloads.h"

#include <stdio.h>
#include <string.h>

int main(int argc, char **argv)
{
    char message[128];
    int result;
    if (argc != 2 || strcmp(argv[1], "--selftest") != 0) {
        fputs("usage: JUKUWIN --selftest\n", stderr);
        return JH_HOST_EXIT_COMMAND;
    }
    result = jh_host_selftest();
    if (result != JH_HOST_EXIT_CLEAN) return result;
    if (jh_jukuwin_payloads_selftest(message, sizeof(message)) != JH_OK) {
        fprintf(stderr, "JUKUWIN embedded payload selftest: FAIL (%s)\n",
                message);
        return JH_HOST_EXIT_ARTIFACT;
    }
    printf("JUKUWIN embedded payload selftest: PASS (%s, source %s)\n",
           message, jh_jukuwin_payload_source_revision);
    return JH_HOST_EXIT_CLEAN;
}
