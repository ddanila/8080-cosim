#ifndef JUKUWIN_SERIAL_H
#define JUKUWIN_SERIAL_H

#include <stddef.h>

#define JH_JUKUWIN_MAX_SERIAL_DEVICES 64u
#define JH_JUKUWIN_SERIAL_DISPLAY_MAX 160u
#define JH_JUKUWIN_SERIAL_HARDWARE_MAX 256u

struct jh_jukuwin_serial_device {
    char port[16];
    char display[JH_JUKUWIN_SERIAL_DISPLAY_MAX];
    char instance_id[JH_JUKUWIN_SERIAL_HARDWARE_MAX];
    char hardware_id[JH_JUKUWIN_SERIAL_HARDWARE_MAX];
};

int jh_jukuwin_serial_enumerate(struct jh_jukuwin_serial_device *devices,
                                size_t capacity, size_t *count);
int jh_jukuwin_serial_select(
    const struct jh_jukuwin_serial_device *devices, size_t count,
    const char *configured, const char *instance_id,
    char *port, size_t port_capacity, size_t *selected_index);

#endif
