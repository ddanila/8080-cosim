/* MIT. POSIX profile bridge. The parent alone decides when to serve/discover.
 * A helper borrows the descriptor while the parent performs no serial I/O.
 * It returns a fixed JHR1 packet: status, parity, stops, reserved, LE baud and persistent generation.
 * status 0 = still unknown, 1 = booted, 2 = intervention required.
 */
static int profile_helper(struct host_context *host, const char *operation)
{
#if !defined(_WIN32) && !defined(JH_DOS)
    int pipes[2];
    pid_t child;
    int status = 0;
    uint8_t reply[16];
    size_t used = 0u;
    uint64_t deadline = jh_platform_milliseconds() +
        (uint64_t)host->options.timeout_seconds * 1000u;
    char serial_fd[32], result_fd[32], current_baud[32], current_parity[2], current_stops[2];
    if (pipe(pipes) != 0) return EXIT_SERIAL;
    (void)snprintf(serial_fd, sizeof(serial_fd), "%d", host->serial.fd);
    (void)snprintf(result_fd, sizeof(result_fd), "%d", pipes[1]);
    (void)snprintf(current_baud, sizeof(current_baud), "%u", host->serial.baud);
    current_parity[0] = host->serial.parity; current_parity[1] = 0;
    current_stops[0] = (char)('0' + host->serial.stop_bits); current_stops[1] = 0;
    child = fork();
    if (child == 0) {
        (void)close(pipes[0]);
        (void)fcntl(host->serial.fd, F_SETFD, 0);
        (void)fcntl(pipes[1], F_SETFD, 0);
        execl(host->options.recovery_python, host->options.recovery_python,
            host->options.recovery_helper, "--operation", operation, "--config", host->options.recovery_config,
            "--serial-fd", serial_fd, "--result-fd", result_fd,
            "--current-baud", current_baud, "--current-parity", current_parity, "--current-stops", current_stops, (char *)NULL);
        _exit(127);
    }
    (void)close(pipes[1]);
    if (child < 0) { (void)close(pipes[0]); return EXIT_SERIAL; }
    (void)fcntl(pipes[0], F_SETFL, O_NONBLOCK);
    for (;;) {
        ssize_t count;
        pid_t waited;
        if (used < sizeof(reply)) {
            count = read(pipes[0], reply + used, sizeof(reply) - used);
            if (count > 0) used += (size_t)count;
        }
        waited = waitpid(child, &status, WNOHANG);
        if (waited == child) break;
        if (waited < 0 && errno != EINTR) break;
        if (host_stop_requested(host) || jh_platform_milliseconds() >= deadline) {
            (void)kill(child, SIGKILL);
            while (waitpid(child, &status, 0) < 0 && errno == EINTR) {}
            (void)close(pipes[0]);
            host_log(host, "WARN", "helper interrupted; execution state uncertain, no replay");
            return host_stop_requested(host) ? EXIT_CLEAN : EXIT_PROTOCOL;
        }
        jh_platform_sleep(10u);
    }
    if (used < sizeof(reply)) {
        ssize_t count = read(pipes[0], reply + used, sizeof(reply) - used);
        if (count > 0) used += (size_t)count;
    }
    (void)close(pipes[0]);
    if (!WIFEXITED(status) || WEXITSTATUS(status) != 0 || used != sizeof(reply) ||
        memcmp(reply, "JHR1", 4u) != 0 || reply[4] > 1u ||
        (reply[5] != 'N' && reply[5] != 'O' && reply[5] != 'E') ||
        (reply[6] != 1u && reply[6] != 2u) || reply[7] != 0u) {
        host_log(host, "ERROR", "recovery helper failed or requires intervention; no upload replay");
        return EXIT_PROTOCOL;
    }
    {
        unsigned baud = (unsigned)reply[8] | (unsigned)reply[9] << 8 |
            (unsigned)reply[10] << 16 | (unsigned)reply[11] << 24;
        if (baud < 75u || baud > 62400u || (host->options.kaypro2 && baud > 19800u))
            return EXIT_PROTOCOL;
        /* Helper verified framing/rate; adopt without flushing the first JD. */
        struct jh_platform_serial adopted;
        if (jh_platform_serial_adopt_format(&adopted, host->serial.fd,
            host->serial.path, baud, (char)reply[5], reply[6], 2) != 0) return EXIT_SERIAL;
        host->serial = adopted;
        host->options.session_generation = (uint32_t)reply[12] | (uint32_t)reply[13] << 8 |
            (uint32_t)reply[14] << 16 | (uint32_t)reply[15] << 24;
        host->options.disk_baud = baud;
        if (host->options.kaypro2) {
            host->options.serial_parity = (char)reply[5];
            host->options.serial_stop_bits = reply[6];
        }
    }
    if (reply[4] == 1u) {
        if (host->options.console_pty) {
            struct jh_platform_console console;
            uint8_t discarded[256];
            const uint8_t kaypro_clear[] = {26u, 27u, 65u, 26u};
            const uint8_t ansi_clear[] = "\033[2J\033[H";
            if (jh_platform_console_open(&console, host->options.console_pty) != 0)
                return RUN_REOPEN_CONSOLE;
            while (jh_platform_console_read(&console, discarded, sizeof(discarded)) > 0) {}
            if (jh_platform_console_write(&console,
                    host->options.kaypro2 ? kaypro_clear : ansi_clear,
                    host->options.kaypro2 ? sizeof(kaypro_clear) : sizeof(ansi_clear)-1u) != 0) {
                jh_platform_console_close(&console); return RUN_REOPEN_CONSOLE;
            }
            jh_platform_console_close(&console);
        }
        host->profile_booted = 1;
        if (host->requests) { ++host->boot_restart_count; ++host->target_reset_count; }
        host_log(host, "INFO", "phase=runtime-link boot-complete serial=%u 8%c%u",
            host->serial.baud, host->serial.parity, host->serial.stop_bits);
        return RUN_REDISCOVER;
    }
    return RUN_REDISCOVER;
#else
    (void)host;
    return EXIT_COMMAND;
#endif
}

static int discover_profile_target(struct host_context *host)
{
    struct jh_n3_parser parser;
    struct jh_n3_request request;
    uint8_t incoming[4096];
    uint64_t deadline = jh_platform_milliseconds() + 3000u;
    int prepared = profile_helper(host, "prepare");
    if (prepared != RUN_REDISCOVER) return prepared;
    host->profile_booted = 0;
    jh_n3_parser_init(&parser);
    host_log(host, "INFO", "phase=discover serial=%u 8%c%u", host->serial.baud,
        host->serial.parity, host->serial.stop_bits);
    while (!host_stop_requested(host) && jh_platform_milliseconds() < deadline) {
        int count = host_read(host, incoming, sizeof(incoming), 50u);
        size_t i;
        if (count < 0) return EXIT_SERIAL;
        for (i = 0u; i < (size_t)count; ++i) {
            if (jh_n3_parser_push(&parser, incoming[i], &request) == JH_FRAME) {
                host_push_back(host, incoming + i + 1u, (size_t)count - i - 1u);
                host_push_back(host, parser.bytes, request_wire_length(&request));
                host_log(host, "INFO", "checked NetDisk request; target runtime confirmed");
                return RUN_DISCOVER_DISK;
            }
        }
    }
    if (host_stop_requested(host)) return EXIT_CLEAN;
    return profile_helper(host, "discover");
}
