#include <windows.h>

#include "platform.h"

#include <errno.h>
#include <stdio.h>
#include <string.h>

static const HANDLE fake_handle = (HANDLE)(uintptr_t)0x1234u;
static PHANDLER_ROUTINE control_handler;
static DWORD last_error;
static DWORD ticks;
static DWORD sleep_total;
static char opened_path[64];
static DWORD opened_access;
static DWORD opened_share;
static DCB applied_dcb;
static COMMTIMEOUTS applied_timeouts;
static DWORD purge_flags;
static DWORD pending_errors;
static DWORD output_queue;
static unsigned write_calls;
static uint8_t written_bytes[64];
static size_t written_length;
static int fail_open;
static int wine_mode;
static int drop_parity_on_read;

BOOL SetConsoleCtrlHandler(PHANDLER_ROUTINE handler, BOOL add)
{
    if (add) control_handler = handler;
    return TRUE;
}

LONG InterlockedExchange(LONG *target, LONG value)
{
    LONG previous = *target;
    *target = value;
    return previous;
}

LONG InterlockedExchangeAdd(LONG *target, LONG value)
{
    LONG previous = *target;
    *target += value;
    return previous;
}

DWORD GetTickCount(void)
{
    return ticks;
}

void Sleep(DWORD milliseconds)
{
    ticks += milliseconds;
    sleep_total += milliseconds;
    if (output_queue != 0u) --output_queue;
}

void GlobalMemoryStatus(MEMORYSTATUS *status)
{
    status->dwAvailPhys = 12345678u;
}

BOOL SetCommTimeouts(HANDLE handle, COMMTIMEOUTS *timeouts)
{
    if (handle != fake_handle) return FALSE;
    applied_timeouts = *timeouts;
    return TRUE;
}

BOOL SetCommState(HANDLE handle, DCB *state)
{
    if (handle != fake_handle) return FALSE;
    applied_dcb = *state;
    return TRUE;
}

BOOL GetCommState(HANDLE handle, DCB *state)
{
    if (handle != fake_handle) return FALSE;
    *state = applied_dcb;
    if (drop_parity_on_read && state->Parity == ODDPARITY) {
        state->Parity = NOPARITY;
        state->fParity = FALSE;
    }
    return TRUE;
}

BOOL PurgeComm(HANDLE handle, DWORD flags)
{
    if (handle != fake_handle) return FALSE;
    purge_flags = flags;
    return TRUE;
}

BOOL SetupComm(HANDLE handle, DWORD input, DWORD output)
{
    return handle == fake_handle && input == 4096u && output == 4096u;
}

HANDLE CreateFileA(LPCSTR path, DWORD access, DWORD share, LPVOID security,
                   DWORD creation, DWORD flags, HANDLE template_file)
{
    (void)security;
    (void)creation;
    (void)flags;
    (void)template_file;
    if (fail_open) {
        last_error = ERROR_ACCESS_DENIED;
        return INVALID_HANDLE_VALUE;
    }
    memcpy(opened_path, path, strlen(path) + 1u);
    opened_access = access;
    opened_share = share;
    return fake_handle;
}

BOOL CloseHandle(HANDLE handle)
{
    return handle == fake_handle;
}

BOOL ClearCommError(HANDLE handle, DWORD *errors, COMSTAT *status)
{
    if (handle != fake_handle) return FALSE;
    *errors = pending_errors;
    pending_errors = 0u;
    memset(status, 0, sizeof(*status));
    status->cbOutQue = output_queue;
    return TRUE;
}

BOOL ReadFile(HANDLE handle, LPVOID output, DWORD amount, DWORD *received,
              LPVOID overlapped)
{
    static const uint8_t input[] = {0x11u, 0x22u, 0x33u};
    DWORD length = amount < sizeof(input) ? amount : sizeof(input);
    (void)overlapped;
    if (handle != fake_handle) return FALSE;
    memcpy(output, input, length);
    *received = length;
    return TRUE;
}

BOOL WriteFile(HANDLE handle, const void *data, DWORD amount, DWORD *written,
               LPVOID overlapped)
{
    DWORD length = amount > 2u ? 2u : amount;
    (void)overlapped;
    if (handle != fake_handle) return FALSE;
    memcpy(written_bytes + written_length, data, length);
    written_length += length;
    *written = length;
    ++write_calls;
    return TRUE;
}

DWORD GetLastError(void)
{
    return last_error;
}

HMODULE GetModuleHandleA(LPCSTR module)
{
    (void)module;
    return wine_mode ? (HMODULE)(uintptr_t)0x5678u : NULL;
}

FARPROC GetProcAddress(HMODULE module, LPCSTR name)
{
    (void)name;
    return wine_mode && module != NULL ? (FARPROC)(uintptr_t)0x9abcu : NULL;
}

static int check(int condition, const char *message)
{
    if (condition) return 0;
    fprintf(stderr, "PLATFORM-WIN32-TEST: %s\n", message);
    return 1;
}

int main(void)
{
    struct jh_platform_serial serial;
    uint8_t input[8];
    static const uint8_t output[] = {1u, 2u, 3u, 4u, 5u};
    uint64_t before;
    uint64_t after;
    memset(&serial, 0, sizeof(serial));

    if (check(jh_platform_serial_open(&serial, "COM17", 9600u, 'O') == 0,
              "COM17 open failed") ||
            check(strcmp(opened_path, "\\\\.\\COM17") == 0,
                  "COM10+ namespace differs") ||
            check(opened_access == (GENERIC_READ | GENERIC_WRITE) &&
                  opened_share == 0u, "serial open is not exclusive") ||
            check(applied_dcb.BaudRate == 9600u && applied_dcb.ByteSize == 8u &&
                  applied_dcb.Parity == ODDPARITY && applied_dcb.fParity &&
                  !applied_dcb.fOutX && !applied_dcb.fInX &&
                  !applied_dcb.fOutxCtsFlow && !applied_dcb.fOutxDsrFlow,
                  "odd-parity DCB differs") ||
            check(purge_flags == (PURGE_RXABORT | PURGE_RXCLEAR |
                  PURGE_TXABORT | PURGE_TXCLEAR), "purge contract differs")) {
        return 1;
    }
    if (check(jh_platform_serial_configure(&serial, 19200u, 'N') == 0,
              "8N1 configure failed") ||
            check(applied_dcb.BaudRate == 19200u &&
                  applied_dcb.Parity == NOPARITY && !applied_dcb.fParity,
                  "8N1 DCB differs")) return 1;

    wine_mode = 1;
    drop_parity_on_read = 1;
    if (check(jh_platform_serial_configure(&serial, 9600u, 'O') == 0,
              "Wine PTY odd-parity emulation was rejected")) return 1;
    wine_mode = 0;
    errno = 0;
    if (check(jh_platform_serial_configure(&serial, 9600u, 'O') < 0 &&
              errno == EINVAL,
              "real Windows parity mismatch was accepted")) return 1;
    drop_parity_on_read = 0;

    if (check(jh_platform_serial_read(&serial, input, sizeof(input), 37u) == 3,
              "bounded read differs") ||
            check(memcmp(input, "\x11\x22\x33", 3u) == 0,
                  "read bytes differ") ||
            check(applied_timeouts.ReadIntervalTimeout == MAXDWORD &&
                  applied_timeouts.ReadTotalTimeoutConstant == 37u,
                  "read timeout differs")) return 1;

    if (check(jh_platform_serial_write(&serial, output, sizeof(output), 91u) ==
                  0, "partial write loop failed") ||
            check(write_calls == 3u && written_length == sizeof(output) &&
                  memcmp(written_bytes, output, sizeof(output)) == 0,
                  "partial writes lost data") ||
            check(applied_timeouts.WriteTotalTimeoutConstant == 91u,
                  "write timeout differs")) return 1;

    output_queue = 3u;
    if (check(jh_platform_serial_drain(&serial) == 0,
              "bounded drain failed") ||
            check(sleep_total >= 3u, "drain did not wait for queued bytes")) {
        return 1;
    }

    pending_errors = CE_RXPARITY;
    errno = 0;
    if (check(jh_platform_serial_read(&serial, input, sizeof(input), 1u) < 0 &&
              errno == EIO && serial.line_errors == 1u,
              "line error was not fatal and counted")) return 1;

    ticks = 0xfffffff0u;
    before = jh_platform_milliseconds();
    ticks = 0x00000010u;
    after = jh_platform_milliseconds();
    if (check(after > before && after - before == 32u,
              "GetTickCount wrap extension differs") ||
            check(jh_platform_available_memory() == 12345678u,
                  "available-memory report differs")) return 1;

    jh_platform_install_signals();
    if (check(control_handler != NULL && control_handler(CTRL_CLOSE_EVENT),
              "control handler was not installed") ||
            check(jh_platform_stop_requested(), "stop event was not retained")) {
        return 1;
    }
    jh_platform_serial_close(&serial);
    if (check(!serial.opened && serial.native_handle == NULL,
              "serial close did not clear state")) return 1;

    fail_open = 1;
    errno = 0;
    if (check(jh_platform_serial_open(&serial, "COM3", 9600u, 'O') < 0 &&
              errno == EACCES, "open error mapping differs")) return 1;

    puts("PLATFORM-WIN32-TEST: PASS "
         "(DCB + namespace + partial I/O + errors + drain + timer wrap)");
    return 0;
}
