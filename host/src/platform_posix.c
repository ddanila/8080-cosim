#define _POSIX_C_SOURCE 200809L

#include "platform_posix.h"

#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <termios.h>
#include <time.h>
#include <unistd.h>

static volatile sig_atomic_t stop_requested;

static void stop_handler(int signal_number)
{
    (void)signal_number;
    stop_requested = 1;
}

void jh_posix_install_signals(void)
{
    struct sigaction action;
    memset(&action, 0, sizeof(action));
    action.sa_handler = stop_handler;
    sigemptyset(&action.sa_mask);
    (void)sigaction(SIGINT, &action, NULL);
    (void)sigaction(SIGTERM, &action, NULL);
}

int jh_posix_stop_requested(void)
{
    return stop_requested != 0;
}

uint64_t jh_posix_milliseconds(void)
{
    struct timespec now;
    if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) return 0u;
    return (uint64_t)now.tv_sec * 1000u + (uint64_t)now.tv_nsec / 1000000u;
}

void jh_posix_sleep(unsigned milliseconds)
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

int jh_posix_serial_configure(struct jh_posix_serial *serial, unsigned baud,
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
    pseudo_terminal = strncmp(serial->path, "/dev/pts/", 9u) == 0;
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
    if (parity == 'O') attributes.c_cflag |= PARENB | PARODD;
    attributes.c_cc[VMIN] = 0;
    attributes.c_cc[VTIME] = 0;
    if (cfsetispeed(&attributes, speed) != 0 ||
            cfsetospeed(&attributes, speed) != 0 ||
            tcsetattr(serial->fd, TCSANOW, &attributes) != 0 ||
            tcflush(serial->fd, TCIOFLUSH) != 0 ||
            tcgetattr(serial->fd, &applied) != 0) {
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

int jh_posix_serial_open(struct jh_posix_serial *serial, const char *path,
                         unsigned baud, char parity)
{
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
    if (jh_posix_serial_configure(serial, baud, parity) != 0) {
        int saved = errno;
        close(serial->fd);
        serial->fd = -1;
        errno = saved;
        return -1;
    }
    return 0;
}

void jh_posix_serial_close(struct jh_posix_serial *serial)
{
    if (serial != NULL && serial->fd >= 0) {
        (void)close(serial->fd);
        serial->fd = -1;
    }
}

int jh_posix_serial_read(struct jh_posix_serial *serial, uint8_t *output,
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
    if (received > INT32_MAX) {
        errno = EOVERFLOW;
        return -1;
    }
    return (int)received;
}

int jh_posix_serial_write(struct jh_posix_serial *serial, const uint8_t *data,
                          size_t length, unsigned timeout_ms)
{
    uint64_t deadline = jh_posix_milliseconds() + timeout_ms;
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
            uint64_t now = jh_posix_milliseconds();
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

int jh_posix_serial_drain(struct jh_posix_serial *serial)
{
    return serial == NULL || serial->fd < 0 ? -1 : tcdrain(serial->fd);
}

int jh_posix_set_raw(int fd)
{
    struct termios attributes;
    if (tcgetattr(fd, &attributes) != 0) return -1;
    cfmakeraw(&attributes);
    return tcsetattr(fd, TCSANOW, &attributes);
}

int jh_posix_open_console(const char *path)
{
    int fd = open(path, O_RDWR | O_NOCTTY | O_NONBLOCK);
    if (fd >= 0 && jh_posix_set_raw(fd) != 0) {
        int saved = errno;
        close(fd);
        errno = saved;
        return -1;
    }
    return fd;
}

int jh_posix_load_file(const char *path, uint8_t **data, size_t *length)
{
    struct stat status;
    uint8_t *buffer;
    size_t offset = 0u;
    int fd;
    if (path == NULL || data == NULL || length == NULL) return -1;
    fd = open(path, O_RDONLY);
    if (fd < 0) return -1;
    if (fstat(fd, &status) != 0 || status.st_size < 0 ||
            (uintmax_t)status.st_size > SIZE_MAX) {
        close(fd);
        errno = EFBIG;
        return -1;
    }
    buffer = (uint8_t *)malloc((size_t)status.st_size == 0u ? 1u :
                               (size_t)status.st_size);
    if (buffer == NULL) {
        close(fd);
        return -1;
    }
    while (offset < (size_t)status.st_size) {
        ssize_t got = read(fd, buffer + offset, (size_t)status.st_size - offset);
        if (got < 0 && errno == EINTR) continue;
        if (got <= 0) {
            free(buffer);
            close(fd);
            errno = EIO;
            return -1;
        }
        offset += (size_t)got;
    }
    if (close(fd) != 0) {
        free(buffer);
        return -1;
    }
    *data = buffer;
    *length = (size_t)status.st_size;
    return 0;
}

int jh_posix_write_file(const char *path, const uint8_t *data, size_t length,
                        int sync_data)
{
    size_t offset = 0u;
    int fd = open(path, O_WRONLY | O_CREAT | O_TRUNC, 0600);
    if (fd < 0) return -1;
    while (offset < length) {
        ssize_t wrote = write(fd, data + offset, length - offset);
        if (wrote < 0 && errno == EINTR) continue;
        if (wrote <= 0) {
            close(fd);
            errno = EIO;
            return -1;
        }
        offset += (size_t)wrote;
    }
    if (sync_data && fsync(fd) != 0) {
        close(fd);
        return -1;
    }
    return close(fd);
}

int jh_posix_pwrite_record(const char *path, uint32_t offset,
                           const uint8_t *data, size_t length)
{
    size_t done = 0u;
    int fd = open(path, O_WRONLY);
    if (fd < 0) return -1;
    while (done < length) {
        ssize_t wrote = pwrite(fd, data + done, length - done,
                               (off_t)offset + (off_t)done);
        if (wrote < 0 && errno == EINTR) continue;
        if (wrote <= 0) {
            close(fd);
            errno = EIO;
            return -1;
        }
        done += (size_t)wrote;
    }
    if (fsync(fd) != 0) {
        close(fd);
        return -1;
    }
    return close(fd);
}

int jh_posix_remove_file(const char *path)
{
    return unlink(path) == 0 || errno == ENOENT ? 0 : -1;
}
