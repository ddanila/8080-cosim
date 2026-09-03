#include "jukuhost_runner.h"

#include <stdio.h>
#include <string.h>

struct test_context {
    unsigned log_count;
    unsigned state_count;
    char last_state[32];
};

static int stop_immediately(void *opaque)
{
    (void)opaque;
    return 1;
}

static void record_log(void *opaque, unsigned long elapsed_ms,
                       const char *level, const char *message)
{
    struct test_context *context = (struct test_context *)opaque;
    (void)elapsed_ms;
    if (level == NULL || message == NULL) return;
    ++context->log_count;
}

static void record_state(void *opaque, const char *state)
{
    struct test_context *context = (struct test_context *)opaque;
    size_t length = strlen(state);
    if (length >= sizeof(context->last_state)) {
        length = sizeof(context->last_state) - 1u;
    }
    memcpy(context->last_state, state, length);
    context->last_state[length] = '\0';
    ++context->state_count;
}

int main(void)
{
    struct jh_host_options options;
    struct jh_host_hooks hooks;
    struct jh_host_summary summary;
    struct test_context context;
    int result;

    memset(&hooks, 0, sizeof(hooks));
    memset(&summary, 0xa5, sizeof(summary));
    memset(&context, 0, sizeof(context));
    jh_host_options_init(&options);
    if (options.timeout_seconds != 120u || options.disk_baud != 19200u ||
            options.disk_protocol != 3u || options.read_ahead != 3u ||
            options.serial_fd != -1) {
        fprintf(stderr, "runner defaults differ\n");
        return 1;
    }
    hooks.context = &context;
    hooks.stop_requested = stop_immediately;
    hooks.log = record_log;
    hooks.state = record_state;
    result = jh_host_run(&options, &hooks, &summary);
    if (result != JH_HOST_EXIT_CLEAN || summary.result != result ||
            summary.rx_bytes != 0u || summary.tx_bytes != 0u ||
            context.log_count < 4u || context.state_count != 2u ||
            strcmp(context.last_state, "stopped") != 0) {
        fprintf(stderr, "runner callback/cancellation contract differs\n");
        return 1;
    }
    if (jh_host_run(NULL, &hooks, &summary) != JH_HOST_EXIT_COMMAND) {
        fprintf(stderr, "runner accepted null options\n");
        return 1;
    }
    puts("JUKUHOST-RUNNER-TEST: PASS");
    return 0;
}
