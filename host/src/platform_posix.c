#define _POSIX_C_SOURCE 200809L

#include "platform.h"

#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <string.h>
#include <termios.h>
#include <time.h>
#include <unistd.h>

static volatile sig_atomic_t stop_requested;

static void stop_handler(int signal_number)
{
    (void)signal_number;
    stop_requested = 1;
}

void jh_platform_install_signals(void)
{
    struct sigaction action;
    memset(&action, 0, sizeof(action));
    action.sa_handler = stop_handler;
    sigemptyset(&action.sa_mask);
    (void)sigaction(SIGINT, &action, NULL);
    (void)sigaction(SIGTERM, &action, NULL);
}

int jh_platform_stop_requested(void)
{
    return stop_requested != 0;
}

uint64_t jh_platform_milliseconds(void)
{
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) return 0u;
    return (uint64_t)now.tv_sec * 1000u + (uint64_t)now.tv_nsec / 1000000u;
}

void jh_platform_sleep(unsigned milliseconds)
{
    struct timespec requested;
    struct timespec remaining;
    requested.tv_sec = (time_t)(milliseconds / 1000u);
    requested.tv_nsec = (long)(milliseconds % 1000u) * 1000000L;
    while (nanosleep(&requested, &remaining) != 0 && errno == EINTR &&
            !stop_requested) {
        requested = remaining;
    }
}

const char *jh_platform_timer_name(void)
{
    return "CLOCK_MONOTONIC";
}

unsigned jh_platform_timer_resolution_ms(void)
{
    struct timespec resolution;
    uint64_t nanoseconds;
    if (clock_getres(CLOCK_MONOTONIC, &resolution) != 0) return 0u;
    nanoseconds = (uint64_t)resolution.tv_sec * UINT64_C(1000000000) +
        (uint64_t)resolution.tv_nsec;
    return (unsigned)((nanoseconds + UINT64_C(999999)) / UINT64_C(1000000));
}

uint32_t jh_platform_available_memory(void)
{
    return 0u;
}

static speed_t baud_value(unsigned baud)
{
    switch (baud) {
    case 2400u: return B2400;
    case 4800u: return B4800;
    case 9600u: return B9600;
    case 19200u: return B19200;
    case 38400u: return B38400;
    default: return (speed_t)0;
    }
}

int jh_platform_serial_configure(struct jh_platform_serial *serial, unsigned baud,
                              char parity)
{
    struct termios attributes;
    struct termios applied;
    speed_t speed;
    tcflag_t required;
    int pseudo_terminal;
    if (serial == NULL || serial->fd < 0 ||
            (parity != 'N' && parity != 'O')) return -1;
    speed = baud_value(baud);
    pseudo_terminal = serial->pseudo_terminal;
    if (speed == (speed_t)0 || tcgetattr(serial->fd, &attributes) != 0) return -1;
    attributes.c_iflag = IGNPAR;
    attributes.c_oflag = 0;
    attributes.c_lflag = 0;
    attributes.c_cflag &= (tcflag_t)~(CSIZE | CSTOPB | PARENB | PARODD
#ifdef CRTSCTS
        | CRTSCTS
#endif
    );
    attributes.c_cflag |= CS8 | CLOCAL | CREAD;
    /* Linux PTYs neither generate nor validate parity.  Some kernels accept
     * the first PARENB request, silently clear it, and reject an identical
     * request when the same PTY is adopted by a replacement process.  Keep
     * PTY framing logical for simulator tests; physical ports remain strict. */
    if (parity == 'O' && !pseudo_terminal) {
        attributes.c_cflag |= PARENB | PARODD;
    }
    attributes.c_cc[VMIN] = 0;
    attributes.c_cc[VTIME] = 0;
    if (cfsetispeed(&attributes, speed) != 0 ||
            cfsetospeed(&attributes, speed) != 0 ||
            tcsetattr(serial->fd, TCSANOW, &attributes) != 0) {
        return -1;
    }
    if (tcflush(serial->fd, TCIOFLUSH) != 0 &&
            !(pseudo_terminal && errno == EINVAL)) {
        return -1;
    }
    if (tcgetattr(serial->fd, &applied) != 0) {
        return -1;
    }
    required = CS8 | CLOCAL | CREAD;
    if (parity == 'O' && !pseudo_terminal) required |= PARENB | PARODD;
    if (cfgetispeed(&applied) != speed || cfgetospeed(&applied) != speed ||
            (applied.c_cflag & required) != required ||
            (!pseudo_terminal && parity == 'N' &&
             (applied.c_cflag & (PARENB | PARODD)) != 0u) ||
            (applied.c_cflag & CSTOPB) != 0u) {
        errno = EINVAL;
        return -1;
    }
    serial->baud = baud;
    serial->parity = parity;
    return 0;
}

int jh_platform_serial_open(struct jh_platform_serial *serial, const char *path,
                         unsigned baud, char parity)
{
    char actual[512];
    size_t length;
    if (serial == NULL || path == NULL) return -1;
    memset(serial, 0, sizeof(*serial));
    serial->fd = -1;
    length = strlen(path);
    if (length == 0u || length >= sizeof(serial->path)) {
        errno = ENAMETOOLONG;
        return -1;
    }
    serial->fd = open(path, O_RDWR | O_NOCTTY | O_NONBLOCK);
    if (serial->fd < 0) return -1;
    memcpy(serial->path, path, length + 1u);
    serial->pseudo_terminal =
        (ttyname_r(serial->fd, actual, sizeof(actual)) == 0 &&
         strncmp(actual, "/dev/pts/", 9u) == 0) ||
        strncmp(path, "/dev/pts/", 9u) == 0;
    if (jh_platform_serial_configure(serial, baud, parity) != 0) {
        int saved = errno;
        close(serial->fd);
        serial->fd = -1;
        errno = saved;
        return -1;
    }
    return 0;
}

int jh_platform_serial_adopt(struct jh_platform_serial *serial, int fd,
                          const char *description, unsigned baud, char parity)
{
    int flags;
    size_t length;
    if (serial == NULL || fd < 0 || description == NULL) return -1;
    memset(serial, 0, sizeof(*serial));
    serial->fd = fd;
    length = strlen(description);
    if (length == 0u || length >= sizeof(serial->path)) {
        errno = ENAMETOOLONG;
        return -1;
    }
    memcpy(serial->path, description, length + 1u);
    /* Descriptor adoption is deliberately an integration-test-only PTY path;
     * production devices are always opened by name and remain strict. */
    serial->pseudo_terminal = 1;
    flags = fcntl(fd, F_GETFL);
    if (flags < 0 || fcntl(fd, F_SETFL, flags | O_NONBLOCK) != 0 ||
            jh_platform_serial_configure(serial, baud, parity) != 0) {
        serial->fd = -1;
        return -1;
    }
    return 0;
}

void jh_platform_serial_close(struct jh_platform_serial *serial)
{
    if (serial != NULL && serial->fd >= 0) {
        (void)close(serial->fd);
        serial->fd = -1;
    }
}

int jh_platform_serial_read(struct jh_platform_serial *serial, uint8_t *output,
                         size_t capacity, unsigned timeout_ms)
{
    struct pollfd descriptor;
    int ready;
    ssize_t received;
    if (serial == NULL || serial->fd < 0 || output == NULL || capacity == 0u) {
        errno = EINVAL;
        return -1;
    }
    descriptor.fd = serial->fd;
    descriptor.events = POLLIN;
    descriptor.revents = 0;
    do {
        ready = poll(&descriptor, 1u, (int)timeout_ms);
    } while (ready < 0 && errno == EINTR && !stop_requested);
    if (ready < 0 && errno == EINTR && stop_requested) return 0;
    if (ready <= 0) return ready;
    if ((descriptor.revents & (POLLERR | POLLHUP | POLLNVAL)) != 0 &&
            (descriptor.revents & POLLIN) == 0) {
        errno = EIO;
        return -1;
    }
    received = read(serial->fd, output, capacity);
    if (received < 0 && (errno == EAGAIN || errno == EWOULDBLOCK)) return 0;
    if (received == 0 &&
            (descriptor.revents & (POLLERR | POLLHUP | POLLNVAL)) != 0) {
        errno = EIO;
        return -1;
    }
    if (received > INT32_MAX) {
        errno = EOVERFLOW;
        return -1;
    }
    return (int)received;
}

int jh_platform_serial_write(struct jh_platform_serial *serial, const uint8_t *data,
                          size_t length, unsigned timeout_ms)
{
    uint64_t deadline = jh_platform_milliseconds() + timeout_ms;
    size_t written_total = 0u;
    if (serial == NULL || serial->fd < 0 ||
            (data == NULL && length != 0u)) {
        errno = EINVAL;
        return -1;
    }
    while (written_total < length && !stop_requested) {
        ssize_t written = write(serial->fd, data + written_total,
                                length - written_total);
        if (written > 0) {
            written_total += (size_t)written;
            continue;
        }
        if (written < 0 && errno != EAGAIN && errno != EWOULDBLOCK &&
                errno != EINTR) return -1;
        {
            struct pollfd descriptor;
            uint64_t now = jh_platform_milliseconds();
            int wait;
            if (now >= deadline) {
                errno = ETIMEDOUT;
                return -1;
            }
            wait = (int)(deadline - now > INT32_MAX ? INT32_MAX :
                         deadline - now);
            descriptor.fd = serial->fd;
            descriptor.events = POLLOUT;
            descriptor.revents = 0;
            if (poll(&descriptor, 1u, wait) <= 0) {
                if (errno == EINTR) continue;
                errno = ETIMEDOUT;
                return -1;
            }
        }
    }
    return written_total == length ? 0 : -1;
}

int jh_platform_serial_drain(struct jh_platform_serial *serial)
{
    return serial == NULL || serial->fd < 0 ? -1 : tcdrain(serial->fd);
}

static int set_raw(int fd)
{
    struct termios attributes;
    if (tcgetattr(fd, &attributes) != 0) return -1;
    cfmakeraw(&attributes);
    return tcsetattr(fd, TCSANOW, &attributes);
}

int jh_platform_console_open(struct jh_platform_console *console,
                             const char *path)
{
    int fd;
    if (console == NULL || path == NULL) return -1;
    console->fd = -1;
    console->file = NULL;
    console->ready_ms = 0u;
    fd = open(path, O_RDWR | O_NOCTTY | O_NONBLOCK);
    if (fd >= 0 && set_raw(fd) != 0) {
        int saved = errno;
        close(fd);
        errno = saved;
        return -1;
    }
    console->fd = fd;
    return fd < 0 ? -1 : 0;
}

int jh_platform_console_read(struct jh_platform_console *console,
                             uint8_t *output, size_t capacity)
{
    ssize_t received;
    if (console == NULL || console->fd < 0 || output == NULL) return -1;
    received = read(console->fd, output, capacity);
    if (received < 0 && (errno == EAGAIN || errno == EWOULDBLOCK)) return 0;
    return received < 0 ? -1 : (int)received;
}

int jh_platform_console_write(struct jh_platform_console *console,
                              const uint8_t *data, size_t length)
{
    ssize_t written;
    if (console == NULL || console->fd < 0 ||
            (data == NULL && length != 0u)) return -1;
    written = write(console->fd, data, length);
    return written == (ssize_t)length ? 0 : -1;
}

void jh_platform_console_close(struct jh_platform_console *console)
{
    if (console != NULL && console->fd >= 0) {
        (void)close(console->fd);
        console->fd = -1;
        console->file = NULL;
        console->ready_ms = 0u;
    }
}

void jh_platform_idle(void)
{
}
