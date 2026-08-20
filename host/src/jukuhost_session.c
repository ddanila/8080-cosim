#include "jukuhost.h"

#include <string.h>

int jh_session_init(struct jh_session *session, int direct_fastboot,
                    int fastboot_enabled)
{
    if (session == NULL) return JH_ERR_ARGUMENT;
    if (direct_fastboot && !fastboot_enabled) return JH_ERR_FORMAT;
    memset(session, 0, sizeof(*session));
    session->direct_fastboot = direct_fastboot != 0;
    session->fastboot_enabled = fastboot_enabled != 0;
    session->phase = direct_fastboot ? JH_SESSION_FASTBOOT :
        JH_SESSION_DISCOVERY;
    return JH_OK;
}

int jh_session_advance(struct jh_session *session,
                       enum jh_session_event event)
{
    if (session == NULL) return JH_ERR_ARGUMENT;
    if (session->phase == JH_SESSION_STOPPED ||
            session->phase == JH_SESSION_FAILED) {
        return JH_ERR_FORMAT;
    }
    if (event == JH_SESSION_STOP) {
        session->phase = JH_SESSION_STOPPED;
        return JH_OK;
    }
    if (event == JH_SESSION_FATAL) {
        session->phase = JH_SESSION_FAILED;
        return JH_OK;
    }
    if (event == JH_SESSION_SERIAL_LOST) {
        session->phase = JH_SESSION_RECONNECT;
        ++session->reconnect_count;
        return JH_OK;
    }
    if (event == JH_SESSION_SERIAL_REOPENED &&
            session->phase == JH_SESSION_RECONNECT) {
        session->phase = JH_SESSION_DISCOVERY;
        session->fastboot_unconfirmed = 0;
        return JH_OK;
    }
    if (event == JH_SESSION_TARGET_RESET) {
        ++session->reset_count;
        session->fastboot_unconfirmed = 0;
        session->phase = session->direct_fastboot ? JH_SESSION_FASTBOOT :
            JH_SESSION_DISCOVERY;
        return JH_OK;
    }
    switch (session->phase) {
    case JH_SESSION_DISCOVERY:
        if (event != JH_SESSION_STOCK_REQUEST) return JH_ERR_FORMAT;
        session->phase = JH_SESSION_STOCK_BOOT;
        ++session->boot_count;
        return JH_OK;
    case JH_SESSION_STOCK_BOOT:
        if (event != JH_SESSION_STOCK_COMPLETE) return JH_ERR_FORMAT;
        session->phase = session->fastboot_enabled ? JH_SESSION_FASTBOOT :
            JH_SESSION_NETDISK;
        return JH_OK;
    case JH_SESSION_FASTBOOT:
        if (event == JH_SESSION_FAST_READY) return JH_OK;
        if (event == JH_SESSION_FAST_COMPLETE) {
            session->fastboot_unconfirmed = 0;
            session->phase = JH_SESSION_NETDISK;
            if (session->direct_fastboot) ++session->boot_count;
            return JH_OK;
        }
        if (event == JH_SESSION_FAST_UNCONFIRMED) {
            session->fastboot_unconfirmed = 1;
            session->phase = JH_SESSION_NETDISK;
            if (session->direct_fastboot) ++session->boot_count;
            return JH_OK;
        }
        return JH_ERR_FORMAT;
    case JH_SESSION_NETDISK:
        if (event != JH_SESSION_DISK_REQUEST) return JH_ERR_FORMAT;
        session->fastboot_unconfirmed = 0;
        return JH_OK;
    case JH_SESSION_RECONNECT:
    case JH_SESSION_STOPPED:
    case JH_SESSION_FAILED:
        return JH_ERR_FORMAT;
    }
    return JH_ERR_FORMAT;
}

const char *jh_session_phase_name(enum jh_session_phase phase)
{
    switch (phase) {
    case JH_SESSION_DISCOVERY: return "discovery";
    case JH_SESSION_STOCK_BOOT: return "stock-boot";
    case JH_SESSION_FASTBOOT: return "fastboot";
    case JH_SESSION_NETDISK: return "netdisk";
    case JH_SESSION_RECONNECT: return "reconnect";
    case JH_SESSION_STOPPED: return "stopped";
    case JH_SESSION_FAILED: return "failed";
    }
    return "invalid";
}

const char *jh_result_name(int result)
{
    switch (result) {
    case JH_OK: return "ok";
    case JH_FRAME: return "frame";
    case JH_NEED_MORE: return "need-more";
    case JH_ERR_ARGUMENT: return "invalid-argument";
    case JH_ERR_SPACE: return "insufficient-space";
    case JH_ERR_CHECKSUM: return "checksum";
    case JH_ERR_FORMAT: return "format";
    case JH_ERR_RANGE: return "range";
    case JH_ERR_READ_ONLY: return "read-only";
    case JH_ERR_UNSUPPORTED: return "unsupported";
    default: return "unknown";
    }
}
