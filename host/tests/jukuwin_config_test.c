#include "jukuwin_config.h"

#include <stdio.h>
#include <string.h>

static int expect_failure(const char *text, const char *message)
{
    struct jh_jukuwin_config config;
    struct jh_jukuwin_config_error error;
    int result = jh_jukuwin_config_parse(text, strlen(text), &config, &error);
    if (result == JH_OK || strstr(error.message, message) == NULL) {
        fprintf(stderr, "expected %s failure, got line %lu: %s\n", message,
                (unsigned long)error.line, error.message);
        return 1;
    }
    return 0;
}

int main(void)
{
    static const char text[] =
        "; portable configuration\r\n"
        "[juku]\r\n"
        "mode=stock\r\n"
        "serial=COM17\r\n"
        "serial_id=USB\\VID_067B&PID_2303\\A\r\n"
        "auto_listen=no\r\n"
        "[drive_a]\r\n"
        "image=CPM3.IMG\r\n"
        "mode=snapshot\r\n"
        "working=CPM3-WORK.IMG\r\n"
        "[drive_b]\r\n"
        "image=DOOM.JUK\r\n"
        "[evidence]\r\n"
        "directory=logs\r\n"
        "capture=yes\r\n"
        "verbose=yes\r\n"
        "keep_sessions=42\r\n";
    struct jh_jukuwin_config config;
    struct jh_jukuwin_config reparsed;
    struct jh_jukuwin_config_error error;
    char formatted[4096];
    char path[JH_CONFIG_PATH_MAX];
    size_t length;

    jh_jukuwin_config_init(&config);
    if (config.mode != JH_JUKUWIN_MODE_C12) {
        fprintf(stderr, "default mode is not C12\n");
        return 1;
    }

    if (jh_jukuwin_config_parse(text, sizeof(text) - 1u, &config, &error) !=
            JH_OK || jh_jukuwin_config_validate(&config, &error) != JH_OK) {
        fprintf(stderr, "valid config rejected at %lu: %s\n",
                (unsigned long)error.line, error.message);
        return 1;
    }
    if (config.mode != JH_JUKUWIN_MODE_STOCK ||
            strcmp(config.serial, "COM17") != 0 || config.auto_listen ||
            config.keep_sessions != 42u || !config.capture || !config.verbose) {
        fprintf(stderr, "parsed values differ\n");
        return 1;
    }
    if (jh_jukuwin_config_format(&config, formatted, sizeof(formatted),
            &length) != JH_OK || jh_jukuwin_config_parse(formatted, length,
            &reparsed, &error) != JH_OK ||
            memcmp(&config, &reparsed, sizeof(config)) != 0) {
        fprintf(stderr, "format round trip differs\n");
        return 1;
    }
    if (jh_jukuwin_resolve_path("C:\\JUKU\\JUKUWIN.INI", "CPM3.IMG",
            path, sizeof(path)) != JH_OK ||
            strcmp(path, "C:\\JUKU\\CPM3.IMG") != 0 ||
            jh_jukuwin_default_working_path("C:\\JUKU\\CPM3.IMG", path,
                sizeof(path)) != JH_OK ||
            strcmp(path, "C:\\JUKU\\CPM3-WORK.IMG") != 0) {
        fprintf(stderr, "path handling differs: %s\n", path);
        return 1;
    }
    if (expect_failure("[juku]\nmode=c11\nmode=stock\n", "duplicate") ||
            expect_failure("[bad]\nvalue=x\n", "unknown section") ||
            expect_failure("[juku]\nmagic=yes\n", "unknown key") ||
            expect_failure("[juku]\nauto_listen=maybe\n", "yes or no")) {
        return 1;
    }
    if (jh_jukuwin_config_parse("[juku]\nmode=c11\n",
            strlen("[juku]\nmode=c11\n"),
            &config, &error) != JH_OK ||
            config.mode != JH_JUKUWIN_MODE_C11 ||
            jh_jukuwin_config_parse("[juku]\nmode=c12\n",
            strlen("[juku]\nmode=c12\n"),
            &config, &error) != JH_OK ||
            config.mode != JH_JUKUWIN_MODE_C12) {
        fprintf(stderr, "C11/C12 mode parsing differs\n");
        return 1;
    }
    jh_jukuwin_config_init(&config);
    if (jh_jukuwin_config_validate(&config, &error) == JH_OK ||
            strstr(error.message, "drive A") == NULL) {
        fprintf(stderr, "missing drive A accepted\n");
        return 1;
    }
    puts("JUKUWIN-CONFIG-TEST: PASS (strict parse + round trip + paths)");
    return 0;
}
