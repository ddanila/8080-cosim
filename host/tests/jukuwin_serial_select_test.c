#include "jukuwin_serial.h"

#include <errno.h>
#include <stdio.h>
#include <string.h>

int main(void)
{
    struct jh_jukuwin_serial_device devices[2];
    char port[16];
    size_t selected = 99u;
    memset(devices, 0, sizeof(devices));
    memcpy(devices[0].port, "COM3", 5u);
    memcpy(devices[0].instance_id, "USB\\VID_067B\\ONE", 17u);
    memcpy(devices[1].port, "COM17", 6u);
    memcpy(devices[1].instance_id, "USB\\VID_067B\\TWO", 17u);

    if (jh_jukuwin_serial_select(devices, 2u, "auto",
            "usb\\vid_067b\\two", port, sizeof(port), &selected) != 0 ||
            strcmp(port, "COM17") != 0 || selected != 1u) {
        fputs("stable identity did not follow changed COM number\n", stderr);
        return 1;
    }
    if (jh_jukuwin_serial_select(devices, 2u, "COM42", "ignored",
            port, sizeof(port), &selected) != 0 ||
            strcmp(port, "COM42") != 0 || selected != (size_t)-1) {
        fputs("explicit COM selection differs\n", stderr);
        return 1;
    }
    if (jh_jukuwin_serial_select(devices, 1u, "auto", "", port,
            sizeof(port), &selected) != 0 || strcmp(port, "COM3") != 0) {
        fputs("unambiguous auto selection differs\n", stderr);
        return 1;
    }
    errno = 0;
    if (jh_jukuwin_serial_select(devices, 2u, "auto", "", port,
            sizeof(port), NULL) == 0 || errno != EBUSY) {
        fputs("ambiguous adapters were accepted\n", stderr);
        return 1;
    }
    errno = 0;
    if (jh_jukuwin_serial_select(devices, 0u, "auto", "", port,
            sizeof(port), NULL) == 0 || errno != ENOENT) {
        fputs("missing adapter was accepted\n", stderr);
        return 1;
    }
    puts("JUKUWIN-SERIAL-SELECT-TEST: PASS (identity + ambiguity)");
    return 0;
}
