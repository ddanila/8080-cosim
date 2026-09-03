#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <commdlg.h>

#include "jukuhost_runner.h"
#include "jukuwin_config.h"
#include "jukuwin_payloads.h"
#include "jukuwin_serial.h"
#include "platform.h"

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define APP_CLASS "JukuWinHostWindow"
#define APP_TITLE "Juku Host"
#define WM_APP_HOST_EVENT (WM_APP + 1u)
#define WM_APP_AUTOSTART (WM_APP + 2u)

#define ID_MODE 100u
#define ID_SERIAL 101u
#define ID_REFRESH 102u
#define ID_DRIVE_A 103u
#define ID_BROWSE_A 104u
#define ID_A_MODE 105u
#define ID_DRIVE_B 106u
#define ID_BROWSE_B 107u
#define ID_EJECT_B 108u
#define ID_AUTOLISTEN 109u
#define ID_LISTEN 110u
#define ID_CONSOLE 111u
#define ID_INPUT 112u
#define ID_SEND 113u
#define ID_LOG 114u

enum event_kind {
    EVENT_LOG = 1,
    EVENT_STATE,
    EVENT_CONSOLE,
    EVENT_PROGRESS,
    EVENT_ACTIVITY,
    EVENT_DONE
};

struct host_event {
    enum event_kind kind;
    unsigned first;
    unsigned second;
    size_t length;
    char text[1024];
};

struct app_state {
    HINSTANCE instance;
    HWND window;
    HWND mode;
    HWND serial;
    HWND refresh;
    HWND drive_a;
    HWND browse_a;
    HWND a_mode;
    HWND drive_b;
    HWND browse_b;
    HWND eject_b;
    HWND auto_listen;
    HWND listen;
    HWND status;
    HWND counters;
    HWND console;
    HWND input;
    HWND send;
    HWND log;
    HFONT font;
    HANDLE worker;
    CRITICAL_SECTION input_lock;
    volatile LONG stop_requested;
    int running;
    int closing;
    struct jh_jukuwin_config config;
    struct jh_jukuwin_config run_config;
    char config_path[JH_CONFIG_PATH_MAX];
    char drive_a_base[JH_CONFIG_PATH_MAX];
    char drive_a_working[JH_CONFIG_PATH_MAX];
    char drive_b_path[JH_CONFIG_PATH_MAX];
    char log_path[JH_CONFIG_PATH_MAX];
    char capture_path[JH_CONFIG_PATH_MAX];
    struct jh_config_disk drive_a_identity;
    struct jh_config_disk drive_b_identity;
    struct jh_jukuwin_serial_device devices[JH_JUKUWIN_MAX_SERIAL_DEVICES];
    size_t device_count;
    uint8_t console_input[JH_SERVICE_CONSOLE_QUEUE];
    size_t console_input_length;
    DWORD last_activity_ms;
};

static struct app_state application;

static int copy_text(char *target, size_t capacity, const char *source)
{
    size_t length = strlen(source);
    if (length >= capacity) return -1;
    memcpy(target, source, length + 1u);
    return 0;
}

static void set_control_font(HWND control, HFONT font)
{
    SendMessage(control, WM_SETFONT, (WPARAM)font, TRUE);
}

static HWND make_control(struct app_state *app, const char *class_name,
                         const char *text, DWORD style, unsigned id)
{
    HWND control = CreateWindowExA(0u, class_name, text,
        WS_CHILD | WS_VISIBLE | style, 0, 0, 10, 10, app->window,
        (HMENU)(UINT_PTR)id, app->instance, NULL);
    if (control != NULL) set_control_font(control, app->font);
    return control;
}

static void append_edit(HWND edit, const char *text, size_t length)
{
    LRESULT existing;
    if (edit == NULL || text == NULL || length == 0u) return;
    existing = GetWindowTextLengthA(edit);
    if (existing > 262144L) SetWindowTextA(edit, "");
    SendMessage(edit, EM_SETSEL, (WPARAM)-1, (LPARAM)-1);
    SendMessage(edit, EM_REPLACESEL, FALSE, (LPARAM)text);
}

static int post_host_event(struct app_state *app, enum event_kind kind,
                           const char *text, size_t length,
                           unsigned first, unsigned second)
{
    struct host_event *event;
    if (length >= sizeof(event->text)) length = sizeof(event->text) - 1u;
    event = (struct host_event *)malloc(sizeof(*event));
    if (event == NULL) return -1;
    event->kind = kind;
    event->first = first;
    event->second = second;
    event->length = length;
    if (length != 0u && text != NULL) memcpy(event->text, text, length);
    event->text[length] = '\0';
    if (!PostMessageA(app->window, WM_APP_HOST_EVENT, 0u, (LPARAM)event)) {
        free(event);
        return -1;
    }
    return 0;
}

static int stop_hook(void *opaque)
{
    struct app_state *app = (struct app_state *)opaque;
    return InterlockedExchangeAdd((LONG *)&app->stop_requested, 0L) != 0L;
}

static void log_hook(void *opaque, unsigned long elapsed,
                     const char *level, const char *message)
{
    struct app_state *app = (struct app_state *)opaque;
    char line[1024];
    int length = snprintf(line, sizeof(line), "%08lu %-5s %s\r\n",
                          elapsed, level, message);
    if (length > 0) {
        size_t used = (size_t)length < sizeof(line) ? (size_t)length :
            sizeof(line) - 1u;
        (void)post_host_event(app, EVENT_LOG, line, used, 0u, 0u);
    }
}

static void state_hook(void *opaque, const char *state)
{
    struct app_state *app = (struct app_state *)opaque;
    (void)post_host_event(app, EVENT_STATE, state, strlen(state), 0u, 0u);
}

static void progress_hook(void *opaque, unsigned completed, unsigned total)
{
    struct app_state *app = (struct app_state *)opaque;
    (void)post_host_event(app, EVENT_PROGRESS, NULL, 0u, completed, total);
}

static void activity_hook(void *opaque, const struct jh_host_summary *summary)
{
    struct app_state *app = (struct app_state *)opaque;
    DWORD now = GetTickCount();
    char text[192];
    int length;
    if (now - app->last_activity_ms < 200u) return;
    app->last_activity_ms = now;
    length = snprintf(text, sizeof(text),
        "RX %lu  TX %lu  requests %lu  reads %lu  writes %lu  "
        "retries %lu  reconnects %lu",
        summary->rx_bytes, summary->tx_bytes, summary->requests,
        summary->reads, summary->writes, summary->retries,
        summary->reconnects);
    if (length > 0) {
        size_t used = (size_t)length < sizeof(text) ? (size_t)length :
            sizeof(text) - 1u;
        (void)post_host_event(app, EVENT_ACTIVITY, text, used, 0u, 0u);
    }
}

static int console_read_hook(void *opaque, uint8_t *output, size_t capacity)
{
    struct app_state *app = (struct app_state *)opaque;
    size_t taken;
    EnterCriticalSection(&app->input_lock);
    taken = app->console_input_length < capacity ?
        app->console_input_length : capacity;
    if (taken != 0u) {
        memcpy(output, app->console_input, taken);
        memmove(app->console_input, app->console_input + taken,
                app->console_input_length - taken);
        app->console_input_length -= taken;
    }
    LeaveCriticalSection(&app->input_lock);
    return (int)taken;
}

static int console_write_hook(void *opaque, const uint8_t *data, size_t length)
{
    struct app_state *app = (struct app_state *)opaque;
    char text[1024];
    size_t index;
    if (length >= sizeof(text)) length = sizeof(text) - 1u;
    for (index = 0u; index < length; ++index) {
        uint8_t value = data[index];
        text[index] = value == 0u ? ' ' : (char)value;
    }
    text[length] = '\0';
    return post_host_event(app, EVENT_CONSOLE, text, length, 0u, 0u);
}

static int resolve_serial_hook(void *opaque, const char *configured,
                               char *output, size_t capacity)
{
    struct app_state *app = (struct app_state *)opaque;
    struct jh_jukuwin_serial_device devices[JH_JUKUWIN_MAX_SERIAL_DEVICES];
    size_t count = 0u;
    if (_stricmp(configured, "auto") != 0) {
        return copy_text(output, capacity, configured);
    }
    if (jh_jukuwin_serial_enumerate(devices,
            JH_JUKUWIN_MAX_SERIAL_DEVICES, &count) != 0) return -1;
    return jh_jukuwin_serial_select(devices, count, configured,
        app->run_config.serial_id, output, capacity, NULL);
}

static int make_config_path(char output[JH_CONFIG_PATH_MAX],
                            const char *command_line)
{
    DWORD length;
    char *separator;
    const char *config = strstr(command_line, "--config");
    if (config != NULL) {
        const char *start = config + 8;
        const char *end;
        while (*start == ' ' || *start == '\t') ++start;
        if (*start == '"') {
            ++start;
            end = strchr(start, '"');
        } else {
            end = start;
            while (*end != '\0' && *end != ' ' && *end != '\t') ++end;
        }
        if (end == NULL || end == start ||
                (size_t)(end - start) >= JH_CONFIG_PATH_MAX) return -1;
        memcpy(output, start, (size_t)(end - start));
        output[end - start] = '\0';
        return 0;
    }
    length = GetModuleFileNameA(NULL, output, JH_CONFIG_PATH_MAX);
    if (length == 0u || length >= JH_CONFIG_PATH_MAX) return -1;
    separator = strrchr(output, '\\');
    if (separator == NULL) separator = strrchr(output, '/');
    if (separator == NULL) separator = output;
    else ++separator;
    if ((size_t)(separator - output) + sizeof("JUKUWIN.INI") >
            JH_CONFIG_PATH_MAX) return -1;
    memcpy(separator, "JUKUWIN.INI", sizeof("JUKUWIN.INI"));
    return 0;
}

static int load_configuration(struct app_state *app, char *message,
                              size_t capacity)
{
    uint8_t *data = NULL;
    size_t length = 0u;
    struct jh_jukuwin_config_error error;
    if (jh_platform_load_file(app->config_path, &data, &length) != 0) {
        if (errno == ENOENT) {
            jh_jukuwin_config_init(&app->config);
            (void)snprintf(message, capacity,
                           "New configuration; select drive A and save by listening");
            return 0;
        }
        (void)snprintf(message, capacity, "Cannot read %s: %s",
                       app->config_path, strerror(errno));
        return -1;
    }
    if (jh_jukuwin_config_parse((const char *)data, length, &app->config,
                                &error) != JH_OK) {
        free(data);
        (void)snprintf(message, capacity, "%s:%lu: %s", app->config_path,
                       (unsigned long)error.line, error.message);
        return -1;
    }
    free(data);
    (void)snprintf(message, capacity, "Configuration: %s", app->config_path);
    return 0;
}

static int save_configuration(struct app_state *app, char *message,
                              size_t capacity)
{
    char text[4096];
    char temporary[JH_CONFIG_PATH_MAX];
    size_t length;
    if (jh_jukuwin_config_format(&app->config, text, sizeof(text), &length) !=
            JH_OK || snprintf(temporary, sizeof(temporary), "%s.tmp",
                              app->config_path) >= (int)sizeof(temporary)) {
        (void)snprintf(message, capacity, "Configuration is too large");
        return -1;
    }
    if (jh_platform_write_file(temporary, (const uint8_t *)text, length, 1) !=
            0 || !MoveFileExA(temporary, app->config_path,
                MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)) {
        DWORD error = GetLastError();
        (void)jh_platform_remove_file(temporary);
        (void)snprintf(message, capacity, "Cannot save %s (Windows error %lu)",
                       app->config_path, (unsigned long)error);
        return -1;
    }
    return 0;
}

static void refresh_serial_devices(struct app_state *app)
{
    size_t index;
    int selection = 0;
    SendMessage(app->serial, CB_RESETCONTENT, 0u, 0u);
    SendMessageA(app->serial, CB_ADDSTRING, 0u,
                 (LPARAM)"Automatic (only when unambiguous)");
    app->device_count = 0u;
    (void)jh_jukuwin_serial_enumerate(app->devices,
        JH_JUKUWIN_MAX_SERIAL_DEVICES, &app->device_count);
    for (index = 0u; index < app->device_count; ++index) {
        LRESULT item = SendMessageA(app->serial, CB_ADDSTRING, 0u,
                                    (LPARAM)app->devices[index].display);
        SendMessage(app->serial, CB_SETITEMDATA, (WPARAM)item,
                    (LPARAM)(index + 1u));
        if (_stricmp(app->config.serial, "auto") == 0 &&
                app->config.serial_id[0] != '\0' &&
                _stricmp(app->devices[index].instance_id,
                         app->config.serial_id) == 0) {
            selection = (int)item;
        } else if (_stricmp(app->config.serial,
                            app->devices[index].port) == 0) {
            selection = (int)item;
        }
    }
    if (_stricmp(app->config.serial, "auto") != 0 && selection == 0) {
        char text[96];
        LRESULT item;
        (void)snprintf(text, sizeof(text), "%s (configured, not present)",
                       app->config.serial);
        item = SendMessageA(app->serial, CB_ADDSTRING, 0u, (LPARAM)text);
        SendMessage(app->serial, CB_SETITEMDATA, (WPARAM)item, (LPARAM)-1);
        selection = (int)item;
    }
    SendMessage(app->serial, CB_SETCURSEL, (WPARAM)selection, 0u);
}

static void controls_from_config(struct app_state *app)
{
    SendMessage(app->mode, CB_SETCURSEL,
        app->config.mode == JH_JUKUWIN_MODE_STOCK ? 1u : 0u, 0u);
    SetWindowTextA(app->drive_a, app->config.drive_a_image);
    SendMessage(app->a_mode, CB_SETCURSEL,
        app->config.drive_a_mode == JH_JUKUWIN_DRIVE_A_READ_ONLY ? 1u : 0u,
        0u);
    SetWindowTextA(app->drive_b, app->config.drive_b_image);
    SendMessage(app->auto_listen, BM_SETCHECK,
        app->config.auto_listen ? BST_CHECKED : BST_UNCHECKED, 0u);
    refresh_serial_devices(app);
}

static int controls_to_config(struct app_state *app, char *message,
                              size_t capacity)
{
    int selection;
    LRESULT data;
    char previous_drive_a[JH_CONFIG_PATH_MAX];
    struct jh_jukuwin_config_error error;
    memcpy(previous_drive_a, app->config.drive_a_image,
           sizeof(previous_drive_a));
    app->config.mode = SendMessage(app->mode, CB_GETCURSEL, 0u, 0u) == 1 ?
        JH_JUKUWIN_MODE_STOCK : JH_JUKUWIN_MODE_C11;
    if (GetWindowTextA(app->drive_a, app->config.drive_a_image,
            sizeof(app->config.drive_a_image)) == 0) {
        app->config.drive_a_image[0] = '\0';
    }
    if (strcmp(previous_drive_a, app->config.drive_a_image) != 0) {
        app->config.drive_a_working[0] = '\0';
    }
    app->config.drive_a_mode =
        SendMessage(app->a_mode, CB_GETCURSEL, 0u, 0u) == 1 ?
        JH_JUKUWIN_DRIVE_A_READ_ONLY : JH_JUKUWIN_DRIVE_A_SNAPSHOT;
    if (GetWindowTextA(app->drive_b, app->config.drive_b_image,
            sizeof(app->config.drive_b_image)) == 0) {
        app->config.drive_b_image[0] = '\0';
    }
    app->config.auto_listen = SendMessage(app->auto_listen, BM_GETCHECK,
                                          0u, 0u) == BST_CHECKED;
    selection = (int)SendMessage(app->serial, CB_GETCURSEL, 0u, 0u);
    data = selection < 0 ? 0 : SendMessage(app->serial, CB_GETITEMDATA,
                                           (WPARAM)selection, 0u);
    if (selection <= 0) {
        memcpy(app->config.serial, "auto", 5u);
        app->config.serial_id[0] = '\0';
    } else if (data == (LRESULT)-1) {
        /* Preserve an explicit configured port which is currently absent. */
    } else if ((size_t)data >= 1u && (size_t)data <= app->device_count) {
        const struct jh_jukuwin_serial_device *device =
            &app->devices[(size_t)data - 1u];
        if (device->instance_id[0] != '\0') {
            memcpy(app->config.serial, "auto", 5u);
            if (copy_text(app->config.serial_id,
                    sizeof(app->config.serial_id), device->instance_id) != 0) {
                (void)snprintf(message, capacity, "Serial identity is too long");
                return -1;
            }
        } else {
            if (copy_text(app->config.serial, sizeof(app->config.serial),
                    device->port) != 0) return -1;
            app->config.serial_id[0] = '\0';
        }
    }
    if (jh_jukuwin_config_validate(&app->config, &error) != JH_OK) {
        (void)snprintf(message, capacity, "%s", error.message);
        return -1;
    }
    return 0;
}

static int ensure_directory(const char *path)
{
    if (CreateDirectoryA(path, NULL)) return 0;
    if (GetLastError() == ERROR_ALREADY_EXISTS) return 0;
    errno = EIO;
    return -1;
}

static int make_evidence_paths(struct app_state *app, char *message,
                               size_t capacity)
{
    char directory[JH_CONFIG_PATH_MAX];
    char session[JH_CONFIG_PATH_MAX];
    SYSTEMTIME now;
    unsigned attempt;
    if (jh_jukuwin_resolve_path(app->config_path,
            app->run_config.evidence_directory, directory,
            sizeof(directory)) != JH_OK || ensure_directory(directory) != 0) {
        (void)snprintf(message, capacity, "Cannot create evidence directory");
        return -1;
    }
    GetLocalTime(&now);
    for (attempt = 0u; attempt < 100u; ++attempt) {
        int written = snprintf(session, sizeof(session),
            "%s\\%04u%02u%02u-%02u%02u%02u-%lu-%02u", directory,
            (unsigned)now.wYear, (unsigned)now.wMonth, (unsigned)now.wDay,
            (unsigned)now.wHour, (unsigned)now.wMinute, (unsigned)now.wSecond,
            (unsigned long)GetCurrentProcessId(), attempt);
        if (written < 0 || written >= (int)sizeof(session)) break;
        if (CreateDirectoryA(session, NULL)) {
            if (snprintf(app->log_path, sizeof(app->log_path),
                    "%s\\JUKUHOST.LOG", session) >=
                    (int)sizeof(app->log_path) ||
                    snprintf(app->capture_path, sizeof(app->capture_path),
                    "%s\\JUKUHOST.CAP", session) >=
                    (int)sizeof(app->capture_path)) break;
            return 0;
        }
        if (GetLastError() != ERROR_ALREADY_EXISTS) break;
    }
    (void)snprintf(message, capacity, "Cannot create a session evidence folder");
    return -1;
}

static int session_name_valid(const char *name)
{
    size_t index;
    size_t length = strlen(name);
    if (length < 19u || name[8] != '-' || name[15] != '-') return 0;
    for (index = 0u; index < 8u; ++index) {
        if (name[index] < '0' || name[index] > '9') return 0;
    }
    for (index = 9u; index < 15u; ++index) {
        if (name[index] < '0' || name[index] > '9') return 0;
    }
    index = 16u;
    if (name[index] < '0' || name[index] > '9') return 0;
    while (index < length && name[index] >= '0' && name[index] <= '9') ++index;
    if (index + 3u != length || name[index] != '-' ||
            name[index + 1u] < '0' || name[index + 1u] > '9' ||
            name[index + 2u] < '0' || name[index + 2u] > '9') return 0;
    return 1;
}

static int compare_session_names(const void *left, const void *right)
{
    return strcmp((const char *)left, (const char *)right);
}

static void remove_known_session(const char *directory, const char *name)
{
    char session[JH_CONFIG_PATH_MAX];
    char file[JH_CONFIG_PATH_MAX];
    int length = snprintf(session, sizeof(session), "%s\\%s", directory,
                          name);
    if (length < 0 || length >= (int)sizeof(session)) return;
    length = snprintf(file, sizeof(file), "%s\\JUKUHOST.LOG", session);
    if (length > 0 && length < (int)sizeof(file)) (void)DeleteFileA(file);
    length = snprintf(file, sizeof(file), "%s\\JUKUHOST.CAP", session);
    if (length > 0 && length < (int)sizeof(file)) (void)DeleteFileA(file);
    /* Removal succeeds only if no unrecognized file is present. */
    (void)RemoveDirectoryA(session);
}

static void cleanup_old_sessions(struct app_state *app)
{
    char directory[JH_CONFIG_PATH_MAX];
    char pattern[JH_CONFIG_PATH_MAX];
    char (*names)[128] = NULL;
    size_t count = 0u;
    size_t allocated = 0u;
    WIN32_FIND_DATAA found;
    HANDLE search;
    size_t index;
    if (app->run_config.keep_sessions == 0u ||
            jh_jukuwin_resolve_path(app->config_path,
                app->run_config.evidence_directory, directory,
                sizeof(directory)) != JH_OK ||
            snprintf(pattern, sizeof(pattern), "%s\\*", directory) >=
                (int)sizeof(pattern)) return;
    search = FindFirstFileA(pattern, &found);
    if (search == INVALID_HANDLE_VALUE) return;
    do {
        if ((found.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) != 0u &&
                session_name_valid(found.cFileName)) {
            if (count == allocated) {
                size_t next = allocated == 0u ? 32u : allocated * 2u;
                char (*replacement)[128];
                if (next > 10000u) next = 10000u;
                if (next == allocated) break;
                replacement = (char (*)[128])realloc(names, next * 128u);
                if (replacement == NULL) break;
                names = replacement;
                allocated = next;
            }
            if (strlen(found.cFileName) < 128u) {
                memcpy(names[count], found.cFileName,
                       strlen(found.cFileName) + 1u);
                ++count;
            }
        }
    } while (FindNextFileA(search, &found));
    FindClose(search);
    if (count > app->run_config.keep_sessions) {
        qsort(names, count, 128u, compare_session_names);
        for (index = 0u;
                index < count - app->run_config.keep_sessions; ++index) {
            remove_known_session(directory, names[index]);
        }
    }
    free(names);
}

static int set_disk_identity(struct app_state *app, char *message,
                             size_t capacity)
{
    uint32_t size;
    uint8_t digest[JH_SHA256_SIZE];
    const char *working = app->run_config.drive_a_working;
    if (jh_jukuwin_resolve_path(app->config_path,
            app->run_config.drive_a_image, app->drive_a_base,
            sizeof(app->drive_a_base)) != JH_OK ||
            jh_platform_file_identity(app->drive_a_base, &size, digest) != 0 ||
            size != JH_N3_VOLUME_SIZE) {
        (void)snprintf(message, capacity,
            "Drive A must be a readable %lu-byte image",
            (unsigned long)JH_N3_VOLUME_SIZE);
        return -1;
    }
    memset(&app->drive_a_identity, 0, sizeof(app->drive_a_identity));
    app->drive_a_identity.present = 1;
    app->drive_a_identity.size = size;
    memcpy(app->drive_a_identity.sha256, digest, sizeof(digest));
    memcpy(app->drive_a_identity.geometry, "juku-cpm3", 10u);
    if (app->run_config.drive_a_mode == JH_JUKUWIN_DRIVE_A_SNAPSHOT) {
        char generated[JH_CONFIG_PATH_MAX];
        if (working[0] == '\0') {
            if (jh_jukuwin_default_working_path(
                    app->run_config.drive_a_image, generated,
                    sizeof(generated)) != JH_OK) return -1;
            working = generated;
        }
        if (jh_jukuwin_resolve_path(app->config_path, working,
                app->drive_a_working, sizeof(app->drive_a_working)) != JH_OK ||
                copy_text(app->drive_a_identity.base,
                    sizeof(app->drive_a_identity.base),
                    app->drive_a_base) != 0 ||
                copy_text(app->drive_a_identity.file,
                    sizeof(app->drive_a_identity.file),
                    app->drive_a_working) != 0) return -1;
        app->drive_a_identity.mode = JH_CONFIG_MEDIA_SNAPSHOT;
    } else {
        if (copy_text(app->drive_a_identity.file,
                sizeof(app->drive_a_identity.file), app->drive_a_base) != 0) {
            return -1;
        }
        app->drive_a_identity.mode = JH_CONFIG_MEDIA_READ_ONLY;
    }
    memset(&app->drive_b_identity, 0, sizeof(app->drive_b_identity));
    app->drive_b_path[0] = '\0';
    if (app->run_config.drive_b_image[0] != '\0') {
        if (jh_jukuwin_resolve_path(app->config_path,
                app->run_config.drive_b_image, app->drive_b_path,
                sizeof(app->drive_b_path)) != JH_OK ||
                jh_platform_file_identity(app->drive_b_path, &size, digest) !=
                    0 || size != JH_N3_NATIVE_VOLUME_SIZE) {
            (void)snprintf(message, capacity,
                "Drive B must be a readable native %lu-byte image",
                (unsigned long)JH_N3_NATIVE_VOLUME_SIZE);
            return -1;
        }
        app->drive_b_identity.present = 1;
        app->drive_b_identity.size = size;
        memcpy(app->drive_b_identity.sha256, digest, sizeof(digest));
        memcpy(app->drive_b_identity.geometry, "juku-native", 12u);
        app->drive_b_identity.mode = JH_CONFIG_MEDIA_READ_ONLY;
        if (copy_text(app->drive_b_identity.file,
                sizeof(app->drive_b_identity.file), app->drive_b_path) != 0) {
            return -1;
        }
    }
    return 0;
}

static DWORD WINAPI host_worker(LPVOID opaque)
{
    struct app_state *app = (struct app_state *)opaque;
    struct jh_host_options options;
    struct jh_host_hooks hooks;
    struct jh_host_summary summary;
    char message[256];
    char resolved[16];
    int result;
    if (set_disk_identity(app, message, sizeof(message)) != 0 ||
            make_evidence_paths(app, message, sizeof(message)) != 0) {
        (void)post_host_event(app, EVENT_STATE, message, strlen(message), 0u, 0u);
        (void)post_host_event(app, EVENT_DONE, NULL, 0u,
                              JH_HOST_EXIT_ARTIFACT, 0u);
        return JH_HOST_EXIT_ARTIFACT;
    }
    memset(&hooks, 0, sizeof(hooks));
    hooks.context = app;
    hooks.stop_requested = stop_hook;
    hooks.log = log_hook;
    hooks.state = state_hook;
    hooks.progress = progress_hook;
    hooks.activity = activity_hook;
    hooks.console_read = console_read_hook;
    hooks.console_write = console_write_hook;
    hooks.resolve_serial = resolve_serial_hook;
    while (_stricmp(app->run_config.serial, "auto") == 0 &&
            resolve_serial_hook(app, app->run_config.serial, resolved,
                                sizeof(resolved)) != 0) {
        if (errno == EBUSY) {
            memcpy(message, "Select serial device: multiple adapters match",
                   sizeof("Select serial device: multiple adapters match"));
            (void)post_host_event(app, EVENT_STATE, message, strlen(message),
                                  0u, 0u);
            (void)post_host_event(app, EVENT_DONE, NULL, 0u,
                                  JH_HOST_EXIT_SERIAL, 0u);
            return JH_HOST_EXIT_SERIAL;
        }
        if (stop_hook(app)) {
            (void)post_host_event(app, EVENT_DONE, NULL, 0u,
                                  JH_HOST_EXIT_CLEAN, 0u);
            return JH_HOST_EXIT_CLEAN;
        }
        (void)post_host_event(app, EVENT_STATE,
            "Waiting for configured serial device",
            sizeof("Waiting for configured serial device") - 1u, 0u, 0u);
        Sleep(250u);
    }
    jh_host_options_init(&options);
    if (jh_jukuwin_apply_payloads(
            app->run_config.mode == JH_JUKUWIN_MODE_STOCK ? "stock" : "c11",
            &options) != JH_OK) {
        (void)post_host_event(app, EVENT_DONE, NULL, 0u,
                              JH_HOST_EXIT_ARTIFACT, 0u);
        return JH_HOST_EXIT_ARTIFACT;
    }
    options.serial = app->run_config.serial;
    options.volume = app->drive_a_identity.file;
    options.volume_identity = &app->drive_a_identity;
    options.drive_b = app->drive_b_identity.present ?
        app->drive_b_identity.file : NULL;
    options.drive_b_identity = app->drive_b_identity.present ?
        &app->drive_b_identity : NULL;
    options.writable = app->drive_a_identity.mode == JH_CONFIG_MEDIA_SNAPSHOT;
    options.console_enabled = 1;
    options.log = app->log_path;
    options.capture = app->run_config.capture ? app->capture_path : NULL;
    options.verbose = app->run_config.verbose;
    options.disk_timeout_seconds = 0u;
    options.reconnect_timeout_seconds = 30u;
    memset(&summary, 0, sizeof(summary));
    result = jh_host_run(&options, &hooks, &summary);
    (void)post_host_event(app, EVENT_DONE, NULL, 0u, (unsigned)result,
                          (unsigned)summary.requests);
    return (DWORD)result;
}

static void enable_session_controls(struct app_state *app, int enabled)
{
    EnableWindow(app->mode, enabled);
    EnableWindow(app->serial, enabled);
    EnableWindow(app->refresh, enabled);
    EnableWindow(app->drive_a, enabled);
    EnableWindow(app->browse_a, enabled);
    EnableWindow(app->a_mode, enabled);
    EnableWindow(app->drive_b, enabled);
    EnableWindow(app->browse_b, enabled);
    EnableWindow(app->eject_b, enabled);
    EnableWindow(app->auto_listen, enabled);
}

static void start_listening(struct app_state *app)
{
    char message[256];
    if (app->running) return;
    if (controls_to_config(app, message, sizeof(message)) != 0 ||
            save_configuration(app, message, sizeof(message)) != 0) {
        SetWindowTextA(app->status, message);
        MessageBoxA(app->window, message, APP_TITLE, MB_OK | MB_ICONERROR);
        return;
    }
    app->run_config = app->config;
    app->console_input_length = 0u;
    SetWindowTextA(app->console, "");
    SetWindowTextA(app->log, "");
    InterlockedExchange((LONG *)&app->stop_requested, 0L);
    app->worker = CreateThread(NULL, 0u, host_worker, app, 0u, NULL);
    if (app->worker == NULL) {
        SetWindowTextA(app->status, "Cannot start host worker");
        return;
    }
    app->running = 1;
    enable_session_controls(app, 0);
    SetWindowTextA(app->listen, "Stop");
    SetWindowTextA(app->status, "Validating configuration and media");
}

static void stop_listening(struct app_state *app)
{
    if (!app->running) return;
    InterlockedExchange((LONG *)&app->stop_requested, 1L);
    EnableWindow(app->listen, FALSE);
    SetWindowTextA(app->status, "Stopping safely");
}

static void send_console_input(struct app_state *app)
{
    char text[256];
    int length = GetWindowTextA(app->input, text, sizeof(text) - 1);
    size_t needed;
    if (length <= 0 || !app->running) return;
    needed = (size_t)length + 1u;
    EnterCriticalSection(&app->input_lock);
    if (app->console_input_length + needed <= sizeof(app->console_input)) {
        memcpy(app->console_input + app->console_input_length, text,
               (size_t)length);
        app->console_input_length += (size_t)length;
        app->console_input[app->console_input_length++] = '\r';
        SetWindowTextA(app->input, "");
    } else {
        MessageBeep(MB_ICONEXCLAMATION);
    }
    LeaveCriticalSection(&app->input_lock);
}

static void browse_for_image(struct app_state *app, HWND edit)
{
    OPENFILENAMEA dialog;
    char path[JH_CONFIG_PATH_MAX];
    memset(path, 0, sizeof(path));
    GetWindowTextA(edit, path, sizeof(path));
    memset(&dialog, 0, sizeof(dialog));
    dialog.lStructSize = sizeof(dialog);
    dialog.hwndOwner = app->window;
    dialog.lpstrFilter = "Juku disk images\0*.IMG;*.JUK;*.CPM\0All files\0*.*\0";
    dialog.lpstrFile = path;
    dialog.nMaxFile = sizeof(path);
    dialog.Flags = OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST |
                   OFN_HIDEREADONLY;
    if (GetOpenFileNameA(&dialog)) SetWindowTextA(edit, path);
}

static void layout_controls(struct app_state *app, int width, int height)
{
    int margin = 10;
    int label = 70;
    int button = 80;
    int row = 26;
    int field = width - margin * 2 - label - button - 8;
    int top = 10;
    int lower;
    if (field < 120) field = 120;
    MoveWindow(GetDlgItem(app->window, 200u), margin, top + 4, label, 20, TRUE);
    MoveWindow(app->mode, margin + label, top, 150, 200, TRUE);
    MoveWindow(GetDlgItem(app->window, 201u), margin + label + 160, top + 4,
               45, 20, TRUE);
    MoveWindow(app->serial, margin + label + 205, top, field - 205, 220, TRUE);
    MoveWindow(app->refresh, width - margin - button, top, button, 24, TRUE);
    top += row;
    MoveWindow(GetDlgItem(app->window, 202u), margin, top + 4, label, 20, TRUE);
    MoveWindow(app->drive_a, margin + label, top, field - 125, 24, TRUE);
    MoveWindow(app->a_mode, margin + label + field - 120, top, 120, 180, TRUE);
    MoveWindow(app->browse_a, width - margin - button, top, button, 24, TRUE);
    top += row;
    MoveWindow(GetDlgItem(app->window, 203u), margin, top + 4, label, 20, TRUE);
    MoveWindow(app->drive_b, margin + label, top, field - 55, 24, TRUE);
    MoveWindow(app->eject_b, margin + label + field - 50, top, 50, 24, TRUE);
    MoveWindow(app->browse_b, width - margin - button, top, button, 24, TRUE);
    top += row + 2;
    MoveWindow(app->auto_listen, margin + label, top, 160, 22, TRUE);
    MoveWindow(app->listen, width - margin - button, top - 2, button, 26, TRUE);
    top += row;
    MoveWindow(app->status, margin, top, width - margin * 2, 20, TRUE);
    top += 20;
    MoveWindow(app->counters, margin, top, width - margin * 2, 18, TRUE);
    top += 22;
    lower = height - top - 42;
    if (lower < 100) lower = 100;
    MoveWindow(app->console, margin, top, (width - margin * 3) / 2, lower,
               TRUE);
    MoveWindow(app->log, margin * 2 + (width - margin * 3) / 2, top,
               (width - margin * 3) / 2, lower, TRUE);
    top += lower + 6;
    MoveWindow(app->input, margin, top, width - margin * 2 - button - 8, 24,
               TRUE);
    MoveWindow(app->send, width - margin - button, top, button, 24, TRUE);
}

static void create_controls(struct app_state *app)
{
    app->font = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
    (void)make_control(app, "STATIC", "Mode:", 0u, 200u);
    app->mode = make_control(app, "COMBOBOX", "",
        CBS_DROPDOWNLIST | WS_TABSTOP, ID_MODE);
    SendMessageA(app->mode, CB_ADDSTRING, 0u, (LPARAM)"C11");
    SendMessageA(app->mode, CB_ADDSTRING, 0u, (LPARAM)"Stock ROM");
    (void)make_control(app, "STATIC", "Port:", 0u, 201u);
    app->serial = make_control(app, "COMBOBOX", "",
        CBS_DROPDOWNLIST | WS_TABSTOP | WS_VSCROLL, ID_SERIAL);
    app->refresh = make_control(app, "BUTTON", "Refresh", WS_TABSTOP,
                                ID_REFRESH);
    (void)make_control(app, "STATIC", "Drive A:", 0u, 202u);
    app->drive_a = make_control(app, "EDIT", "",
        WS_BORDER | WS_TABSTOP | ES_AUTOHSCROLL, ID_DRIVE_A);
    app->a_mode = make_control(app, "COMBOBOX", "",
        CBS_DROPDOWNLIST | WS_TABSTOP, ID_A_MODE);
    SendMessageA(app->a_mode, CB_ADDSTRING, 0u, (LPARAM)"Snapshot");
    SendMessageA(app->a_mode, CB_ADDSTRING, 0u, (LPARAM)"Read-only");
    app->browse_a = make_control(app, "BUTTON", "Browse...", WS_TABSTOP,
                                 ID_BROWSE_A);
    (void)make_control(app, "STATIC", "Drive B:", 0u, 203u);
    app->drive_b = make_control(app, "EDIT", "",
        WS_BORDER | WS_TABSTOP | ES_AUTOHSCROLL, ID_DRIVE_B);
    app->eject_b = make_control(app, "BUTTON", "Eject", WS_TABSTOP,
                                ID_EJECT_B);
    app->browse_b = make_control(app, "BUTTON", "Browse...", WS_TABSTOP,
                                 ID_BROWSE_B);
    app->auto_listen = make_control(app, "BUTTON", "Listen on startup",
        BS_AUTOCHECKBOX | WS_TABSTOP, ID_AUTOLISTEN);
    app->listen = make_control(app, "BUTTON", "Listen",
        BS_DEFPUSHBUTTON | WS_TABSTOP, ID_LISTEN);
    app->status = make_control(app, "STATIC", "Stopped",
                               SS_LEFTNOWORDWRAP, 204u);
    app->counters = make_control(app, "STATIC",
        "No active session", SS_LEFTNOWORDWRAP, 205u);
    app->console = make_control(app, "EDIT", "",
        WS_BORDER | WS_VSCROLL | ES_MULTILINE | ES_AUTOVSCROLL |
        ES_READONLY, ID_CONSOLE);
    app->log = make_control(app, "EDIT", "",
        WS_BORDER | WS_VSCROLL | ES_MULTILINE | ES_AUTOVSCROLL |
        ES_READONLY, ID_LOG);
    app->input = make_control(app, "EDIT", "",
        WS_BORDER | WS_TABSTOP | ES_AUTOHSCROLL, ID_INPUT);
    app->send = make_control(app, "BUTTON", "Send", WS_TABSTOP, ID_SEND);
}

static void handle_host_event(struct app_state *app, struct host_event *event)
{
    char text[160];
    switch (event->kind) {
    case EVENT_LOG:
        append_edit(app->log, event->text, event->length);
        break;
    case EVENT_STATE:
        SetWindowTextA(app->status, event->text);
        break;
    case EVENT_CONSOLE:
        append_edit(app->console, event->text, event->length);
        break;
    case EVENT_PROGRESS:
        if (event->second != 0u) {
            (void)snprintf(text, sizeof(text), "Boot progress: %u/%u (%u%%)",
                event->first, event->second,
                event->first * 100u / event->second);
            SetWindowTextA(app->counters, text);
        }
        break;
    case EVENT_ACTIVITY:
        SetWindowTextA(app->counters, event->text);
        break;
    case EVENT_DONE:
        if (app->worker != NULL) {
            CloseHandle(app->worker);
            app->worker = NULL;
        }
        app->running = 0;
        enable_session_controls(app, 1);
        EnableWindow(app->listen, TRUE);
        SetWindowTextA(app->listen, "Listen");
        (void)snprintf(text, sizeof(text), "Stopped: result %u, requests %u",
                       event->first, event->second);
        SetWindowTextA(app->counters, text);
        if (event->first == JH_HOST_EXIT_CLEAN) {
            SetWindowTextA(app->status, "Stopped cleanly");
            cleanup_old_sessions(app);
        }
        if (app->closing) DestroyWindow(app->window);
        break;
    default:
        break;
    }
}

static LRESULT CALLBACK window_proc(HWND window, UINT message,
                                    WPARAM wparam, LPARAM lparam)
{
    struct app_state *app = &application;
    switch (message) {
    case WM_CREATE:
        app->window = window;
        create_controls(app);
        controls_from_config(app);
        return 0;
    case WM_SIZE:
        layout_controls(app, LOWORD(lparam), HIWORD(lparam));
        return 0;
    case WM_COMMAND:
        switch (LOWORD(wparam)) {
        case ID_LISTEN:
            if (app->running) stop_listening(app);
            else start_listening(app);
            return 0;
        case ID_REFRESH:
            refresh_serial_devices(app);
            return 0;
        case ID_BROWSE_A:
            browse_for_image(app, app->drive_a);
            return 0;
        case ID_BROWSE_B:
            browse_for_image(app, app->drive_b);
            return 0;
        case ID_EJECT_B:
            SetWindowTextA(app->drive_b, "");
            return 0;
        case ID_SEND:
            send_console_input(app);
            return 0;
        default:
            break;
        }
        break;
    case WM_APP_HOST_EVENT:
        if (lparam != 0) {
            struct host_event *event = (struct host_event *)lparam;
            handle_host_event(app, event);
            free(event);
        }
        return 0;
    case WM_APP_AUTOSTART:
        start_listening(app);
        return 0;
    case WM_QUERYENDSESSION:
        if (app->running) {
            stop_listening(app);
            return FALSE;
        }
        return TRUE;
    case WM_CLOSE:
        if (app->running) {
            app->closing = 1;
            stop_listening(app);
            return 0;
        }
        DestroyWindow(window);
        return 0;
    case WM_DESTROY:
        PostQuitMessage(0);
        return 0;
    default:
        break;
    }
    return DefWindowProcA(window, message, wparam, lparam);
}

static int application_selftest(void)
{
    struct jh_jukuwin_config config;
    struct jh_jukuwin_config parsed;
    struct jh_jukuwin_config_error error;
    char payload_message[128];
    char text[4096];
    size_t length;
    if (jh_host_selftest() != JH_HOST_EXIT_CLEAN ||
            jh_jukuwin_payloads_selftest(payload_message,
                                         sizeof(payload_message)) != JH_OK) {
        return JH_HOST_EXIT_ARTIFACT;
    }
    jh_jukuwin_config_init(&config);
    memcpy(config.drive_a_image, "SELFTEST.IMG", 13u);
    if (jh_jukuwin_config_format(&config, text, sizeof(text), &length) !=
            JH_OK || jh_jukuwin_config_parse(text, length, &parsed, &error) !=
            JH_OK || memcmp(&config, &parsed, sizeof(config)) != 0) {
        return JH_HOST_EXIT_COMMAND;
    }
    return JH_HOST_EXIT_CLEAN;
}

static int run_headless(struct app_state *app)
{
    struct jh_jukuwin_config_error config_error;
    struct jh_host_options options;
    struct jh_host_hooks hooks;
    struct jh_host_summary summary;
    char message[256];
    char resolved[16];
    if (jh_jukuwin_config_validate(&app->config, &config_error) != JH_OK) {
        fprintf(stderr, "JUKUWIN: %s\n", config_error.message);
        return JH_HOST_EXIT_COMMAND;
    }
    app->run_config = app->config;
    if (set_disk_identity(app, message, sizeof(message)) != 0 ||
            make_evidence_paths(app, message, sizeof(message)) != 0) {
        fprintf(stderr, "JUKUWIN: %s\n", message);
        return JH_HOST_EXIT_ARTIFACT;
    }
    jh_platform_install_signals();
    while (_stricmp(app->run_config.serial, "auto") == 0 &&
            resolve_serial_hook(app, app->run_config.serial, resolved,
                                sizeof(resolved)) != 0) {
        if (errno == EBUSY) {
            fputs("JUKUWIN: multiple serial adapters match\n", stderr);
            return JH_HOST_EXIT_SERIAL;
        }
        if (jh_platform_stop_requested()) return JH_HOST_EXIT_CLEAN;
        Sleep(250u);
    }
    memset(&hooks, 0, sizeof(hooks));
    hooks.context = app;
    hooks.resolve_serial = resolve_serial_hook;
    jh_host_options_init(&options);
    if (jh_jukuwin_apply_payloads(
            app->run_config.mode == JH_JUKUWIN_MODE_STOCK ? "stock" : "c11",
            &options) != JH_OK) return JH_HOST_EXIT_ARTIFACT;
    options.serial = app->run_config.serial;
    options.volume = app->drive_a_identity.file;
    options.volume_identity = &app->drive_a_identity;
    options.drive_b = app->drive_b_identity.present ?
        app->drive_b_identity.file : NULL;
    options.drive_b_identity = app->drive_b_identity.present ?
        &app->drive_b_identity : NULL;
    options.writable = app->drive_a_identity.mode == JH_CONFIG_MEDIA_SNAPSHOT;
    options.log = app->log_path;
    options.capture = app->run_config.capture ? app->capture_path : NULL;
    options.verbose = app->run_config.verbose;
    options.disk_timeout_seconds = 0u;
    memset(&summary, 0, sizeof(summary));
    return jh_host_run(&options, &hooks, &summary);
}

int WINAPI WinMain(HINSTANCE instance, HINSTANCE previous, LPSTR command_line,
                   int show)
{
    WNDCLASSA window_class;
    MSG message;
    char status[512];
    HWND window;
    (void)previous;
    memset(&application, 0, sizeof(application));
    application.instance = instance;
    InitializeCriticalSection(&application.input_lock);
    if (strstr(command_line, "--selftest") != NULL) {
        int result = application_selftest();
        DeleteCriticalSection(&application.input_lock);
        return result;
    }
    if (make_config_path(application.config_path, command_line) != 0) {
        MessageBoxA(NULL, "Cannot determine JUKUWIN.INI path", APP_TITLE,
                    MB_OK | MB_ICONERROR);
        DeleteCriticalSection(&application.input_lock);
        return JH_HOST_EXIT_COMMAND;
    }
    if (load_configuration(&application, status, sizeof(status)) != 0) {
        MessageBoxA(NULL, status, APP_TITLE, MB_OK | MB_ICONERROR);
        DeleteCriticalSection(&application.input_lock);
        return JH_HOST_EXIT_COMMAND;
    }
    if (strstr(command_line, "--headless") != NULL) {
        int result = run_headless(&application);
        DeleteCriticalSection(&application.input_lock);
        return result;
    }
    memset(&window_class, 0, sizeof(window_class));
    window_class.style = CS_HREDRAW | CS_VREDRAW;
    window_class.lpfnWndProc = window_proc;
    window_class.hInstance = instance;
    window_class.hIcon = LoadIconA(instance, MAKEINTRESOURCEA(1));
    if (window_class.hIcon == NULL) {
        window_class.hIcon = LoadIcon(NULL, IDI_APPLICATION);
    }
    window_class.hCursor = LoadCursor(NULL, IDC_ARROW);
    window_class.hbrBackground = (HBRUSH)(COLOR_BTNFACE + 1);
    window_class.lpszClassName = APP_CLASS;
    if (!RegisterClassA(&window_class)) {
        DeleteCriticalSection(&application.input_lock);
        return JH_HOST_EXIT_COMMAND;
    }
    window = CreateWindowExA(0u, APP_CLASS, APP_TITLE,
        WS_OVERLAPPEDWINDOW | WS_CLIPCHILDREN, CW_USEDEFAULT, CW_USEDEFAULT,
        900, 650, NULL, NULL, instance, NULL);
    if (window == NULL) {
        DeleteCriticalSection(&application.input_lock);
        return JH_HOST_EXIT_COMMAND;
    }
    SetWindowTextA(application.status, status);
    ShowWindow(window, show);
    UpdateWindow(window);
    if (application.config.auto_listen &&
            application.config.drive_a_image[0] != '\0') {
        PostMessageA(window, WM_APP_AUTOSTART, 0u, 0u);
    }
    while (GetMessageA(&message, NULL, 0u, 0u) > 0) {
        if (!IsDialogMessageA(window, &message)) {
            TranslateMessage(&message);
            DispatchMessageA(&message);
        }
    }
    DeleteCriticalSection(&application.input_lock);
    return (int)message.wParam;
}
