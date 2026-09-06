#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include "platform.h"

#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>

#ifndef ETIMEDOUT
#define ETIMEDOUT EIO
#endif

static volatile LONG stop_requested;
static DWORD previous_tick;
static uint64_t tick_high;

static void set_errno_from_win32(DWORD error)
{
    switch (error) {
    case ERROR_ACCESS_DENIED:
    case ERROR_SHARING_VIOLATION:
        errno = EACCES;
        break;
    case ERROR_FILE_NOT_FOUND:
    case ERROR_PATH_NOT_FOUND:
    case ERROR_DEVICE_NOT_CONNECTED:
        errno = ENOENT;
        break;
    case ERROR_INVALID_NAME:
    case ERROR_INVALID_PARAMETER:
        errno = EINVAL;
        break;
    case ERROR_NOT_ENOUGH_MEMORY:
    case ERROR_OUTOFMEMORY:
        errno = ENOMEM;
        break;
    case ERROR_SEM_TIMEOUT:
    case ERROR_TIMEOUT:
        errno = ETIMEDOUT;
        break;
    default:
        errno = EIO;
        break;
    }
}

static int serial_win32_failure(const char *operation, DWORD error)
{
    fprintf(stderr, "jukuhost: Win32 serial %s failed (error %lu)\n",
            operation, (unsigned long)error);
    set_errno_from_win32(error);
    return -1;
}

static int running_under_wine(void)
{
    HMODULE ntdll = GetModuleHandleA("NTDLL.DLL");
    return ntdll != NULL &&
           GetProcAddress(ntdll, "wine_get_version") != NULL;
}

static BOOL WINAPI console_control(DWORD control)
{
    switch (control) {
    case CTRL_C_EVENT:
    case CTRL_BREAK_EVENT:
    case CTRL_CLOSE_EVENT:
    case CTRL_LOGOFF_EVENT:
    case CTRL_SHUTDOWN_EVENT:
        InterlockedExchange((LONG *)&stop_requested, 1L);
        return TRUE;
    default:
        return FALSE;
    }
}

void jh_platform_install_signals(void)
{
    (void)SetConsoleCtrlHandler(console_control, TRUE);
}

int jh_platform_stop_requested(void)
{
    /* An aligned volatile LONG read is atomic on our Win32/x86 target.
     * This flag publishes no other data; Win95 lacks InterlockedExchangeAdd. */
    return stop_requested != 0L;
}

uint64_t jh_platform_milliseconds(void)
{
    DWORD current = GetTickCount();
    if (current < previous_tick) tick_high += UINT64_C(0x100000000);
    previous_tick = current;
    return tick_high + (uint64_t)current;
}

void jh_platform_sleep(unsigned milliseconds)
{
    Sleep((DWORD)milliseconds);
}

const char *jh_platform_name(void)
{
    return "Win32";
}

const char *jh_platform_timer_name(void)
{
    return "GetTickCount-wrap-extended";
}

unsigned jh_platform_timer_resolution_ms(void)
{
    /* Conservative scheduler granularity on legacy Windows. */
    return 16u;
}

uint32_t jh_platform_available_memory(void)
{
    MEMORYSTATUS status;
    memset(&status, 0, sizeof(status));
    status.dwLength = sizeof(status);
    GlobalMemoryStatus(&status);
    return (uint32_t)status.dwAvailPhys;
}

static HANDLE serial_handle(const struct jh_platform_serial *serial)
{
    return (HANDLE)serial->native_handle;
}

static int configure_timeouts(HANDLE handle, unsigned read_timeout,
                              unsigned write_timeout)
{
    COMMTIMEOUTS timeouts;
    memset(&timeouts, 0, sizeof(timeouts));
    timeouts.ReadIntervalTimeout = MAXDWORD;
    timeouts.ReadTotalTimeoutConstant = (DWORD)read_timeout;
    timeouts.WriteTotalTimeoutConstant = (DWORD)write_timeout;
    if (!SetCommTimeouts(handle, &timeouts)) {
        return serial_win32_failure("SetCommTimeouts", GetLastError());
    }
    return 0;
}

int jh_platform_serial_configure(struct jh_platform_serial *serial,
                                 unsigned baud, char parity)
{
    DCB dcb;
    DCB applied;
    HANDLE handle;
    int wine_parity_emulation;
    if (serial == NULL || !serial->opened ||
            (parity != 'N' && parity != 'O') ||
            (baud != 2400u && baud != 4800u && baud != 9600u &&
             baud != 19200u && baud != 38400u)) {
        errno = EINVAL;
        return -1;
    }
    handle = serial_handle(serial);
    memset(&dcb, 0, sizeof(dcb));
    dcb.DCBlength = sizeof(dcb);
    if (!GetCommState(handle, &dcb)) {
        return serial_win32_failure("GetCommState", GetLastError());
    }
    dcb.BaudRate = (DWORD)baud;
    dcb.fBinary = TRUE;
    dcb.fParity = parity == 'O';
    dcb.fOutxCtsFlow = FALSE;
    dcb.fOutxDsrFlow = FALSE;
    dcb.fDtrControl = DTR_CONTROL_ENABLE;
    dcb.fDsrSensitivity = FALSE;
    dcb.fTXContinueOnXoff = TRUE;
    dcb.fOutX = FALSE;
    dcb.fInX = FALSE;
    dcb.fErrorChar = FALSE;
    dcb.fNull = FALSE;
    dcb.fRtsControl = RTS_CONTROL_ENABLE;
    dcb.fAbortOnError = FALSE;
    dcb.ByteSize = 8;
    dcb.Parity = parity == 'O' ? ODDPARITY : NOPARITY;
    dcb.StopBits = ONESTOPBIT;
    if (!SetCommState(handle, &dcb)) {
        return serial_win32_failure("SetCommState", GetLastError());
    }
    if (configure_timeouts(handle, 50u, 10000u) != 0) {
        return -1;
    }
    if (!PurgeComm(handle, PURGE_RXABORT | PURGE_RXCLEAR |
                   PURGE_TXABORT | PURGE_TXCLEAR)) {
        return serial_win32_failure("PurgeComm", GetLastError());
    }
    memset(&applied, 0, sizeof(applied));
    applied.DCBlength = sizeof(applied);
    if (!GetCommState(handle, &applied)) {
        return serial_win32_failure("GetCommState verification",
                                    GetLastError());
    }
    wine_parity_emulation = parity == 'O' &&
                            applied.Parity == NOPARITY && !applied.fParity &&
                            running_under_wine();
    if (applied.BaudRate != (DWORD)baud || applied.ByteSize != 8 ||
            applied.StopBits != ONESTOPBIT ||
            (!wine_parity_emulation &&
             (applied.Parity !=
                  (parity == 'O' ? ODDPARITY : NOPARITY) ||
              applied.fParity != (unsigned)(parity == 'O'))) ||
            applied.fOutxCtsFlow || applied.fOutxDsrFlow || applied.fOutX ||
            applied.fInX || applied.fAbortOnError) {
        fprintf(stderr,
                "jukuhost: Win32 serial settings verification failed "
                "(requested %lu 8%c1, applied %lu %u/%u/%u)\n",
                (unsigned long)baud, parity,
                (unsigned long)applied.BaudRate,
                (unsigned)applied.ByteSize, (unsigned)applied.Parity,
                (unsigned)applied.StopBits);
        errno = EINVAL;
        return -1;
    }
    if (wine_parity_emulation) {
        fprintf(stderr,
                "jukuhost: Wine PTY does not retain odd parity; "
                "continuing for byte-level emulation only\n");
    }
    serial->baud = baud;
    serial->parity = parity;
    return 0;
}

int jh_platform_serial_open(struct jh_platform_serial *serial, const char *path,
                            unsigned baud, char parity)
{
    char device[520];
    size_t length;
    HANDLE handle;
    if (serial == NULL || path == NULL) {
        errno = EINVAL;
        return -1;
    }
    memset(serial, 0, sizeof(*serial));
    serial->fd = -1;
    length = strlen(path);
    if (length == 0u || length >= sizeof(serial->path)) {
        errno = ENAMETOOLONG;
        return -1;
    }
    if (length >= 4u && (path[0] == 'C' || path[0] == 'c') &&
            (path[1] == 'O' || path[1] == 'o') &&
            (path[2] == 'M' || path[2] == 'm')) {
        if (length + 4u >= sizeof(device)) {
            errno = ENAMETOOLONG;
            return -1;
        }
        memcpy(device, "\\\\.\\", 4u);
        memcpy(device + 4u, path, length + 1u);
    } else {
        if (length >= sizeof(device)) {
            errno = ENAMETOOLONG;
            return -1;
        }
        memcpy(device, path, length + 1u);
    }
    handle = CreateFileA(device, GENERIC_READ | GENERIC_WRITE, 0u, NULL,
                         OPEN_EXISTING, 0u, NULL);
    if (handle == INVALID_HANDLE_VALUE) {
        set_errno_from_win32(GetLastError());
        return -1;
    }
    serial->native_handle = handle;
    serial->opened = 1;
    memcpy(serial->path, path, length + 1u);
    if (!SetupComm(handle, 4096u, 4096u)) {
        DWORD error = GetLastError();
        (void)serial_win32_failure("SetupComm", error);
        CloseHandle(handle);
        memset(serial, 0, sizeof(*serial));
        serial->fd = -1;
        return -1;
    }
    if (jh_platform_serial_configure(serial, baud, parity) != 0) {
        CloseHandle(handle);
        memset(serial, 0, sizeof(*serial));
        serial->fd = -1;
        return -1;
    }
    return 0;
}

int jh_platform_serial_adopt(struct jh_platform_serial *serial, int fd,
                             const char *description, unsigned baud,
                             char parity)
{
    (void)serial;
    (void)fd;
    (void)description;
    (void)baud;
    (void)parity;
    errno = EINVAL;
    return -1;
}

void jh_platform_serial_close(struct jh_platform_serial *serial)
{
    if (serial != NULL && serial->opened) {
        (void)CloseHandle(serial_handle(serial));
        memset(serial, 0, sizeof(*serial));
        serial->fd = -1;
    }
}

static int account_serial_errors(struct jh_platform_serial *serial)
{
    DWORD errors = 0u;
    COMSTAT status;
    memset(&status, 0, sizeof(status));
    if (!ClearCommError(serial_handle(serial), &errors, &status)) {
        set_errno_from_win32(GetLastError());
        return -1;
    }
    if ((errors & (CE_FRAME | CE_OVERRUN | CE_RXOVER | CE_RXPARITY)) != 0u) {
        ++serial->line_errors;
        errno = EIO;
        return -1;
    }
    return 0;
}

int jh_platform_serial_read(struct jh_platform_serial *serial, uint8_t *output,
                            size_t capacity, unsigned timeout_ms)
{
    DWORD received = 0u;
    DWORD amount;
    if (serial == NULL || !serial->opened || output == NULL || capacity == 0u) {
        errno = EINVAL;
        return -1;
    }
    if (account_serial_errors(serial) != 0 ||
            configure_timeouts(serial_handle(serial), timeout_ms, 10000u) != 0) {
        return -1;
    }
    amount = capacity > (size_t)INT_MAX ? (DWORD)INT_MAX : (DWORD)capacity;
    if (!ReadFile(serial_handle(serial), output, amount, &received, NULL)) {
        set_errno_from_win32(GetLastError());
        return -1;
    }
    if (account_serial_errors(serial) != 0) return -1;
    return (int)received;
}

int jh_platform_serial_write(struct jh_platform_serial *serial,
                             const uint8_t *data, size_t length,
                             unsigned timeout_ms)
{
    size_t total = 0u;
    if (serial == NULL || !serial->opened ||
            (data == NULL && length != 0u)) {
        errno = EINVAL;
        return -1;
    }
    if (configure_timeouts(serial_handle(serial), 50u, timeout_ms) != 0) {
        return -1;
    }
    while (total < length) {
        DWORD written = 0u;
        /* Original Win95's serial driver rejects writes larger than the
         * configured 4096-byte transmit queue, even for synchronous I/O. */
        DWORD amount = length - total > 4096u ? 4096u :
            (DWORD)(length - total);
        if (!WriteFile(serial_handle(serial), data + total, amount, &written,
                       NULL) || written == 0u) {
            set_errno_from_win32(GetLastError());
            return -1;
        }
        total += (size_t)written;
    }
    return account_serial_errors(serial);
}

int jh_platform_serial_drain(struct jh_platform_serial *serial)
{
    uint64_t deadline;
    if (serial == NULL || !serial->opened) {
        errno = EINVAL;
        return -1;
    }
    deadline = jh_platform_milliseconds() + 10000u;
    for (;;) {
        DWORD errors = 0u;
        COMSTAT status;
        memset(&status, 0, sizeof(status));
        if (!ClearCommError(serial_handle(serial), &errors, &status)) {
            set_errno_from_win32(GetLastError());
            return -1;
        }
        if ((errors & (CE_FRAME | CE_OVERRUN | CE_RXOVER | CE_RXPARITY)) != 0u) {
            ++serial->line_errors;
            errno = EIO;
            return -1;
        }
        if (status.cbOutQue == 0u) return 0;
        if (jh_platform_milliseconds() >= deadline) {
            errno = ETIMEDOUT;
            return -1;
        }
        Sleep(1u);
    }
}

int jh_platform_console_open(struct jh_platform_console *console,
                             const char *path)
{
    (void)console;
    (void)path;
    errno = EINVAL;
    return -1;
}

int jh_platform_console_read(struct jh_platform_console *console,
                             uint8_t *output, size_t capacity)
{
    (void)console;
    (void)output;
    (void)capacity;
    errno = EINVAL;
    return -1;
}

int jh_platform_console_write(struct jh_platform_console *console,
                              const uint8_t *data, size_t length)
{
    (void)console;
    (void)data;
    (void)length;
    errno = EINVAL;
    return -1;
}

void jh_platform_console_close(struct jh_platform_console *console)
{
    (void)console;
}

void jh_platform_idle(void)
{
    Sleep(0u);
}
