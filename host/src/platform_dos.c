#include "platform.h"

#include <conio.h>
#include <dos.h>
#include <errno.h>
#include <i86.h>
#include <malloc.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>

#define UART_RBR 0u
#define UART_THR 0u
#define UART_DLL 0u
#define UART_IER 1u
#define UART_DLM 1u
#define UART_IIR 2u
#define UART_FCR 2u
#define UART_LCR 3u
#define UART_MCR 4u
#define UART_LSR 5u
#define UART_LSR_DR 0x01u
#define UART_LSR_ERRORS 0x1eu
#define UART_LSR_THRE 0x20u
#define UART_LSR_TEMT 0x40u
#define BIOS_TICKS_PER_DAY UINT32_C(0x1800b0)
#define PIT_FREQUENCY UINT32_C(1193182)

static volatile int stop_requested;
static uint32_t day_ticks;
static uint32_t previous_bios_ticks;
static uint64_t previous_milliseconds;

static void stop_handler(int signal_number)
{
    (void)signal_number;
    stop_requested = 1;
}

void jh_platform_install_signals(void)
{
    (void)signal(SIGINT, stop_handler);
    (void)signal(SIGTERM, stop_handler);
}

int jh_platform_stop_requested(void)
{
    return stop_requested != 0;
}

static uint64_t pit_ticks(void)
{
    volatile uint32_t __far *bios_ticks =
        (volatile uint32_t __far *)MK_FP(0x0040u, 0x006cu);
    uint32_t ticks;
    unsigned counter;
    uint64_t result;
    _disable();
    ticks = *bios_ticks;
    outp(0x43u, 0x00u);
    counter = inp(0x40u);
    counter |= inp(0x40u) << 8;
    _enable();
    if (ticks < previous_bios_ticks) day_ticks += BIOS_TICKS_PER_DAY;
    previous_bios_ticks = ticks;
    result = ((uint64_t)day_ticks + ticks) * UINT32_C(65536) +
        (uint16_t)(0u - counter);
    return result;
}

uint64_t jh_platform_milliseconds(void)
{
    uint64_t milliseconds = pit_ticks() * 1000u / PIT_FREQUENCY;
    if (milliseconds < previous_milliseconds) {
        milliseconds = previous_milliseconds;
    }
    previous_milliseconds = milliseconds;
    return milliseconds;
}

void jh_platform_sleep(unsigned milliseconds)
{
    uint64_t deadline = jh_platform_milliseconds() + milliseconds;
    while (!stop_requested && jh_platform_milliseconds() < deadline) {
    }
}

const char *jh_platform_timer_name(void)
{
    return "8253-PIT0+BIOS-tick";
}

const char *jh_platform_name(void)
{
    return "DOS";
}

unsigned jh_platform_timer_resolution_ms(void)
{
    return 1u;
}

uint32_t jh_platform_available_memory(void)
{
    return (uint32_t)_memavl();
}

static unsigned uart_in(const struct jh_platform_serial *serial,
                        unsigned reg)
{
    return inp(serial->base_port + reg);
}

static void uart_out(const struct jh_platform_serial *serial, unsigned reg,
                     unsigned value)
{
    outp(serial->base_port + reg, value);
}

static int parse_port(const char *path, unsigned *base)
{
    if (path == NULL || base == NULL) return -1;
    if (stricmp(path, "COM1") == 0 || strcmp(path, "1") == 0) {
        *base = 0x3f8u;
        return 0;
    }
    if (stricmp(path, "COM2") == 0 || strcmp(path, "2") == 0) {
        *base = 0x2f8u;
        return 0;
    }
    errno = EINVAL;
    return -1;
}

int jh_platform_serial_configure(struct jh_platform_serial *serial,
                                 unsigned baud, char parity)
{
    unsigned divisor;
    unsigned lcr;
    unsigned guard;
    if (serial == NULL || !serial->opened ||
            (parity != 'N' && parity != 'O') ||
            (baud != 2400u && baud != 4800u && baud != 9600u &&
             baud != 19200u && baud != 38400u)) {
        errno = EINVAL;
        return -1;
    }
    divisor = 115200u / baud;
    if (divisor == 0u || (uint32_t)divisor * baud != UINT32_C(115200)) {
        errno = EINVAL;
        return -1;
    }
    lcr = parity == 'O' ? 0x0bu : 0x03u;
    uart_out(serial, UART_IER, 0u);
    uart_out(serial, UART_LCR, 0x80u);
    uart_out(serial, UART_DLL, divisor & 0xffu);
    uart_out(serial, UART_DLM, divisor >> 8);
    uart_out(serial, UART_LCR, lcr);
    uart_out(serial, UART_MCR, 0x0bu);
    uart_out(serial, UART_FCR, serial->fifo_depth != 0u ? 0x07u : 0u);
    for (guard = 0u; guard < 256u &&
            (uart_in(serial, UART_LSR) & UART_LSR_DR) != 0u; ++guard) {
        (void)uart_in(serial, UART_RBR);
    }
    serial->baud = baud;
    serial->parity = parity;
    return 0;
}

int jh_platform_serial_open(struct jh_platform_serial *serial, const char *path,
                            unsigned baud, char parity)
{
    unsigned base;
    unsigned lcr;
    if (serial == NULL || parse_port(path, &base) != 0) return -1;
    memset(serial, 0, sizeof(*serial));
    serial->fd = 1;
    serial->base_port = base;
    serial->opened = 1;
    serial->saved_ier = uart_in(serial, UART_IER);
    serial->saved_lcr = uart_in(serial, UART_LCR);
    serial->saved_mcr = uart_in(serial, UART_MCR);
    lcr = serial->saved_lcr;
    uart_out(serial, UART_LCR, lcr | 0x80u);
    serial->saved_divisor = uart_in(serial, UART_DLL) |
        uart_in(serial, UART_DLM) << 8;
    uart_out(serial, UART_LCR, lcr);
    uart_out(serial, UART_FCR, 0x01u);
    serial->fifo_depth = (uart_in(serial, UART_IIR) & 0xc0u) == 0xc0u ?
        16u : 0u;
    if (jh_platform_serial_configure(serial, baud, parity) != 0) {
        jh_platform_serial_close(serial);
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
    if (serial == NULL || !serial->opened) return;
    uart_out(serial, UART_IER, 0u);
    uart_out(serial, UART_LCR, 0x80u);
    uart_out(serial, UART_DLL, serial->saved_divisor & 0xffu);
    uart_out(serial, UART_DLM, serial->saved_divisor >> 8);
    uart_out(serial, UART_LCR, serial->saved_lcr);
    uart_out(serial, UART_MCR, serial->saved_mcr);
    uart_out(serial, UART_IER, serial->saved_ier);
    serial->opened = 0;
    serial->fd = -1;
}

int jh_platform_serial_read(struct jh_platform_serial *serial, uint8_t *output,
                            size_t capacity, unsigned timeout_ms)
{
    uint64_t deadline;
    size_t received = 0u;
    if (serial == NULL || !serial->opened || output == NULL || capacity == 0u) {
        errno = EINVAL;
        return -1;
    }
    deadline = jh_platform_milliseconds() + timeout_ms;
    while (!stop_requested) {
        unsigned lsr = uart_in(serial, UART_LSR);
        if ((lsr & UART_LSR_ERRORS) != 0u) {
            ++serial->line_errors;
            if ((lsr & UART_LSR_DR) != 0u) (void)uart_in(serial, UART_RBR);
            errno = EIO;
            return -1;
        }
        if ((lsr & UART_LSR_DR) != 0u) {
            output[received++] = (uint8_t)uart_in(serial, UART_RBR);
            if (received == capacity) break;
            continue;
        }
        if (received != 0u || jh_platform_milliseconds() >= deadline) break;
    }
    return (int)received;
}

int jh_platform_serial_write(struct jh_platform_serial *serial,
                             const uint8_t *data, size_t length,
                             unsigned timeout_ms)
{
    uint64_t deadline;
    size_t written = 0u;
    if (serial == NULL || !serial->opened ||
            (data == NULL && length != 0u)) {
        errno = EINVAL;
        return -1;
    }
    deadline = jh_platform_milliseconds() + timeout_ms;
    while (written < length && !stop_requested) {
        if ((uart_in(serial, UART_LSR) & UART_LSR_THRE) != 0u) {
            uart_out(serial, UART_THR, data[written++]);
        } else if (jh_platform_milliseconds() >= deadline) {
            errno = EIO;
            return -1;
        }
    }
    return written == length ? 0 : -1;
}

int jh_platform_serial_drain(struct jh_platform_serial *serial)
{
    uint64_t deadline;
    if (serial == NULL || !serial->opened) return -1;
    deadline = jh_platform_milliseconds() + 10000u;
    while ((uart_in(serial, UART_LSR) & UART_LSR_TEMT) == 0u) {
        if (jh_platform_milliseconds() >= deadline) return -1;
    }
    return 0;
}

int jh_platform_console_open(struct jh_platform_console *console,
                             const char *path)
{
    const char *file_path = path;
    if (console == NULL || path == NULL) {
        errno = EINVAL;
        return -1;
    }
    console->file = NULL;
    console->ready_ms = 0u;
    if (stricmp(path, "CON") == 0 || stricmp(path, "LOCAL") == 0) {
        console->fd = 1;
    } else {
        if (path[0] == '@') {
            char *end;
            unsigned long delay = strtoul(path + 1, &end, 10);
            if (end == path + 1 || *end != ':' || end[1] == '\0') {
                errno = EINVAL;
                return -1;
            }
            file_path = end + 1;
            console->ready_ms = jh_platform_milliseconds() + delay;
        }
        console->file = fopen(file_path, "rb");
        if (console->file == NULL) return -1;
        console->fd = 2;
    }
    return 0;
}

int jh_platform_console_read(struct jh_platform_console *console,
                             uint8_t *output, size_t capacity)
{
    size_t length = 0u;
    if (console == NULL || console->fd < 0 || output == NULL) return -1;
    if (console->file != NULL) {
        if (jh_platform_milliseconds() < console->ready_ms) return 0;
        length = fread(output, 1u, capacity, console->file);
        return ferror(console->file) ? -1 : (int)length;
    }
    while (length < capacity && kbhit()) {
        int character = getch();
        if (character == 0 || character == 0xe0) {
            int scan = getch();
            if (scan == 0x44) stop_requested = 1; /* F10: idle-only exit. */
            continue;
        }
        output[length++] = (uint8_t)character;
    }
    return (int)length;
}

int jh_platform_console_write(struct jh_platform_console *console,
                              const uint8_t *data, size_t length)
{
    if (console == NULL || console->fd < 0 ||
            (data == NULL && length != 0u)) return -1;
    if (length != 0u && fwrite(data, 1u, length, stdout) != length) return -1;
    return fflush(stdout);
}

void jh_platform_console_close(struct jh_platform_console *console)
{
    if (console != NULL) {
        if (console->file != NULL) (void)fclose(console->file);
        console->file = NULL;
        console->fd = -1;
        console->ready_ms = 0u;
    }
}

void jh_platform_idle(void)
{
}
