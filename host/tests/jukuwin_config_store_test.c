#include <windows.h>

#include "jukuwin_config_store.h"

#include <stdio.h>
#include <string.h>

static DWORD last_error;
static int modern_available;
static int modern_succeeds;
static int fail_new_install;
static int original_exists;
static int temporary_exists;
static int backup_exists;
static unsigned modern_calls;

static BOOL WINAPI fake_move_file_ex(LPCSTR source, LPCSTR target, DWORD flags)
{
    ++modern_calls;
    if (strcmp(source, "JUKUWIN.tmp") != 0 ||
            strcmp(target, "JUKUWIN.INI") != 0 ||
            flags != (MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)) {
        last_error = ERROR_INVALID_PARAMETER;
        return FALSE;
    }
    if (!modern_succeeds) {
        last_error = ERROR_ACCESS_DENIED;
        return FALSE;
    }
    temporary_exists = 0;
    original_exists = 1;
    return TRUE;
}

HMODULE GetModuleHandleA(LPCSTR module)
{
    return strcmp(module, "KERNEL32.DLL") == 0 ? (HMODULE)1 : NULL;
}

FARPROC GetProcAddress(HMODULE module, LPCSTR name)
{
    if (module != NULL && modern_available &&
            strcmp(name, "MoveFileExA") == 0) {
        return (FARPROC)fake_move_file_ex;
    }
    return NULL;
}

BOOL DeleteFileA(LPCSTR path)
{
    if (strcmp(path, "JUKUWIN.bak") == 0 && backup_exists) {
        backup_exists = 0;
        return TRUE;
    }
    last_error = ERROR_FILE_NOT_FOUND;
    return FALSE;
}

BOOL MoveFileA(LPCSTR source, LPCSTR target)
{
    if (strcmp(source, "JUKUWIN.INI") == 0 &&
            strcmp(target, "JUKUWIN.bak") == 0 && original_exists) {
        original_exists = 0;
        backup_exists = 1;
        return TRUE;
    }
    if (strcmp(source, "JUKUWIN.tmp") == 0 &&
            strcmp(target, "JUKUWIN.INI") == 0 && temporary_exists) {
        if (fail_new_install) {
            last_error = ERROR_ACCESS_DENIED;
            return FALSE;
        }
        temporary_exists = 0;
        original_exists = 1;
        return TRUE;
    }
    if (strcmp(source, "JUKUWIN.bak") == 0 &&
            strcmp(target, "JUKUWIN.INI") == 0 && backup_exists) {
        backup_exists = 0;
        original_exists = 1;
        return TRUE;
    }
    last_error = ERROR_FILE_NOT_FOUND;
    return FALSE;
}

DWORD GetLastError(void)
{
    return last_error;
}

static void reset(int modern)
{
    last_error = ERROR_SUCCESS;
    modern_available = modern;
    modern_succeeds = 1;
    fail_new_install = 0;
    original_exists = 1;
    temporary_exists = 1;
    backup_exists = 0;
    modern_calls = 0u;
}

static int check(int condition, const char *message)
{
    if (condition) return 0;
    fprintf(stderr, "JUKUWIN-CONFIG-STORE-TEST: %s\n", message);
    return 1;
}

int main(void)
{
    unsigned long error = 0u;
    reset(1);
    if (check(jh_jukuwin_config_replace("JUKUWIN.tmp", "JUKUWIN.INI",
            "JUKUWIN.bak", &error) == 0 && modern_calls == 1u &&
            original_exists && !temporary_exists,
            "modern atomic replacement differs")) return 1;

    reset(0);
    if (check(jh_jukuwin_config_replace("JUKUWIN.tmp", "JUKUWIN.INI",
            "JUKUWIN.bak", &error) == 0 && original_exists &&
            !temporary_exists && !backup_exists,
            "legacy backup/install/cleanup differs")) return 1;

    reset(0);
    fail_new_install = 1;
    if (check(jh_jukuwin_config_replace("JUKUWIN.tmp", "JUKUWIN.INI",
            "JUKUWIN.bak", &error) != 0 && error == ERROR_ACCESS_DENIED &&
            original_exists && temporary_exists && !backup_exists,
            "legacy failure did not restore original")) return 1;

    puts("JUKUWIN-CONFIG-STORE-TEST: PASS "
         "(dynamic atomic path + legacy backup/restore)");
    return 0;
}
