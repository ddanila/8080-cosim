#include "jukuwin_serial.h"

#include <errno.h>
#include <string.h>

static int ascii_equal(const char *left, const char *right)
{
    while (*left != '\0' && *right != '\0') {
        char a = *left++;
        char b = *right++;
        if (a >= 'A' && a <= 'Z') a = (char)(a - 'A' + 'a');
        if (b >= 'A' && b <= 'Z') b = (char)(b - 'A' + 'a');
        if (a != b) return 0;
    }
    return *left == '\0' && *right == '\0';
}

static int copy_port(const char *source, char *target, size_t capacity)
{
    size_t length = strlen(source);
    if (length == 0u || length >= capacity) {
        errno = EINVAL;
        return -1;
    }
    memcpy(target, source, length + 1u);
    return 0;
}

int jh_jukuwin_serial_select(
    const struct jh_jukuwin_serial_device *devices, size_t count,
    const char *configured, const char *instance_id,
    char *port, size_t port_capacity, size_t *selected_index)
{
    size_t index;
    if ((devices == NULL && count != 0u) || configured == NULL ||
            instance_id == NULL || port == NULL || port_capacity == 0u) {
        errno = EINVAL;
        return -1;
    }
    if (!ascii_equal(configured, "auto")) {
        if (selected_index != NULL) *selected_index = (size_t)-1;
        return copy_port(configured, port, port_capacity);
    }
    if (instance_id[0] != '\0') {
        for (index = 0u; index < count; ++index) {
            if (ascii_equal(devices[index].instance_id, instance_id)) {
                if (selected_index != NULL) *selected_index = index;
                return copy_port(devices[index].port, port, port_capacity);
            }
        }
        errno = ENOENT;
        return -1;
    }
    if (count == 0u) {
        errno = ENOENT;
        return -1;
    }
    if (count != 1u) {
        errno = EBUSY;
        return -1;
    }
    if (selected_index != NULL) *selected_index = 0u;
    return copy_port(devices[0].port, port, port_capacity);
}
