#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <setupapi.h>

#include "jukuwin_serial.h"

#include <ctype.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>

typedef HDEVINFO (WINAPI *get_class_devs_fn)(const GUID *, PCSTR, HWND, DWORD);
typedef BOOL (WINAPI *enum_device_info_fn)(HDEVINFO, DWORD,
                                           PSP_DEVINFO_DATA);
typedef BOOL (WINAPI *get_property_fn)(HDEVINFO, PSP_DEVINFO_DATA, DWORD,
                                       PDWORD, PBYTE, DWORD, PDWORD);
typedef BOOL (WINAPI *get_instance_fn)(HDEVINFO, PSP_DEVINFO_DATA, PSTR,
                                       DWORD, PDWORD);
typedef BOOL (WINAPI *destroy_list_fn)(HDEVINFO);

static const GUID ports_class = {
    0x4d36e978u, 0xe325u, 0x11ceu,
    {0xbfu, 0xc1u, 0x08u, 0x00u, 0x2bu, 0xe1u, 0x03u, 0x18u}
};

static int parse_port(const char *friendly, char output[16])
{
    const char *open = strrchr(friendly, '(');
    const char *cursor;
    size_t length;
    unsigned number = 0u;
    if (open == NULL) return -1;
    cursor = open + 1;
    if (!((cursor[0] == 'C' || cursor[0] == 'c') &&
          (cursor[1] == 'O' || cursor[1] == 'o') &&
          (cursor[2] == 'M' || cursor[2] == 'm'))) return -1;
    cursor += 3;
    if (!isdigit((unsigned char)*cursor)) return -1;
    while (isdigit((unsigned char)*cursor)) {
        number = number * 10u + (unsigned)(*cursor - '0');
        if (number > 256u) return -1;
        ++cursor;
    }
    if (*cursor != ')' || cursor[1] != '\0' || number == 0u) return -1;
    length = (size_t)(cursor - open - 1);
    if (length >= 16u) return -1;
    memcpy(output, open + 1, length);
    output[length] = '\0';
    return 0;
}

static int already_present(const struct jh_jukuwin_serial_device *devices,
                           size_t count, const char *port)
{
    size_t index;
    for (index = 0u; index < count; ++index) {
        if (_stricmp(devices[index].port, port) == 0) return 1;
    }
    return 0;
}

static size_t enumerate_setupapi(struct jh_jukuwin_serial_device *devices,
                                 size_t capacity)
{
    HMODULE library = LoadLibraryA("SETUPAPI.DLL");
    get_class_devs_fn get_class_devs;
    enum_device_info_fn enum_device_info;
    get_property_fn get_property;
    get_instance_fn get_instance;
    destroy_list_fn destroy_list;
    HDEVINFO set;
    DWORD index;
    size_t count = 0u;
    if (library == NULL) return 0u;
    get_class_devs = (get_class_devs_fn)GetProcAddress(
        library, "SetupDiGetClassDevsA");
    enum_device_info = (enum_device_info_fn)GetProcAddress(
        library, "SetupDiEnumDeviceInfo");
    get_property = (get_property_fn)GetProcAddress(
        library, "SetupDiGetDeviceRegistryPropertyA");
    get_instance = (get_instance_fn)GetProcAddress(
        library, "SetupDiGetDeviceInstanceIdA");
    destroy_list = (destroy_list_fn)GetProcAddress(
        library, "SetupDiDestroyDeviceInfoList");
    if (get_class_devs == NULL || enum_device_info == NULL ||
            get_property == NULL || get_instance == NULL ||
            destroy_list == NULL) {
        FreeLibrary(library);
        return 0u;
    }
    set = get_class_devs(&ports_class, NULL, NULL, DIGCF_PRESENT);
    if (set == INVALID_HANDLE_VALUE) {
        FreeLibrary(library);
        return 0u;
    }
    for (index = 0u; count < capacity; ++index) {
        SP_DEVINFO_DATA info;
        DWORD type = 0u;
        char friendly[JH_JUKUWIN_SERIAL_DISPLAY_MAX];
        char hardware[JH_JUKUWIN_SERIAL_HARDWARE_MAX];
        char instance[JH_JUKUWIN_SERIAL_HARDWARE_MAX];
        struct jh_jukuwin_serial_device *device;
        memset(&info, 0, sizeof(info));
        info.cbSize = sizeof(info);
        if (!enum_device_info(set, index, &info)) {
            if (GetLastError() == ERROR_NO_MORE_ITEMS) break;
            continue;
        }
        memset(friendly, 0, sizeof(friendly));
        if (!get_property(set, &info, SPDRP_FRIENDLYNAME, &type,
                (PBYTE)friendly, sizeof(friendly), NULL)) {
            if (!get_property(set, &info, SPDRP_DEVICEDESC, &type,
                    (PBYTE)friendly, sizeof(friendly), NULL)) continue;
        }
        friendly[sizeof(friendly) - 1u] = '\0';
        device = &devices[count];
        memset(device, 0, sizeof(*device));
        if (parse_port(friendly, device->port) != 0 ||
                already_present(devices, count, device->port)) continue;
        memcpy(device->display, friendly, strlen(friendly) + 1u);
        memset(instance, 0, sizeof(instance));
        if (get_instance(set, &info, instance, sizeof(instance), NULL)) {
            instance[sizeof(instance) - 1u] = '\0';
            memcpy(device->instance_id, instance, strlen(instance) + 1u);
        }
        memset(hardware, 0, sizeof(hardware));
        if (get_property(set, &info, SPDRP_HARDWAREID, &type,
                (PBYTE)hardware, sizeof(hardware), NULL)) {
            hardware[sizeof(hardware) - 1u] = '\0';
            memcpy(device->hardware_id, hardware, strlen(hardware) + 1u);
        }
        ++count;
    }
    (void)destroy_list(set);
    FreeLibrary(library);
    return count;
}

static size_t enumerate_fallback(struct jh_jukuwin_serial_device *devices,
                                 size_t capacity, size_t count)
{
    unsigned number;
    for (number = 1u; number <= 256u && count < capacity; ++number) {
        char port[16];
        COMMCONFIG configuration;
        DWORD size = sizeof(configuration);
        (void)sprintf(port, "COM%u", number);
        memset(&configuration, 0, sizeof(configuration));
        configuration.dwSize = sizeof(configuration);
        if (!already_present(devices, count, port) &&
                GetDefaultCommConfigA(port, &configuration, &size)) {
            struct jh_jukuwin_serial_device *device = &devices[count++];
            memset(device, 0, sizeof(*device));
            memcpy(device->port, port, strlen(port) + 1u);
            memcpy(device->display, port, strlen(port) + 1u);
        }
    }
    return count;
}

int jh_jukuwin_serial_enumerate(struct jh_jukuwin_serial_device *devices,
                                size_t capacity, size_t *count)
{
    size_t found;
    if (devices == NULL || capacity == 0u || count == NULL) {
        errno = EINVAL;
        return -1;
    }
    found = enumerate_setupapi(devices, capacity);
    found = enumerate_fallback(devices, capacity, found);
    *count = found;
    return 0;
}
