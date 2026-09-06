#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include "jukuwin_config_store.h"

typedef BOOL (WINAPI *move_file_ex_fn)(LPCSTR, LPCSTR, DWORD);

int jh_jukuwin_config_replace(const char *temporary, const char *target,
                              const char *backup,
                              unsigned long *windows_error)
{
    move_file_ex_fn move_file_ex = NULL;
    HMODULE kernel = GetModuleHandleA("KERNEL32.DLL");
    DWORD error = ERROR_SUCCESS;
    int had_original = 0;
    if (kernel != NULL) {
        move_file_ex = (move_file_ex_fn)GetProcAddress(kernel, "MoveFileExA");
    }
    if (move_file_ex != NULL) {
        if (move_file_ex(temporary, target,
                MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)) {
            (void)DeleteFileA(backup);
            return 0;
        }
        error = GetLastError();
        /* Original Win95 exports a stub: symbol presence is not support. */
        if (error != ERROR_CALL_NOT_IMPLEMENTED) goto failed;
    }

    if (!DeleteFileA(backup)) {
        error = GetLastError();
        if (error != ERROR_FILE_NOT_FOUND &&
                error != ERROR_PATH_NOT_FOUND) goto failed;
    }
    if (MoveFileA(target, backup)) {
        had_original = 1;
    } else {
        error = GetLastError();
        if (error != ERROR_FILE_NOT_FOUND &&
                error != ERROR_PATH_NOT_FOUND) goto failed;
    }
    if (MoveFileA(temporary, target)) {
        if (had_original) (void)DeleteFileA(backup);
        return 0;
    }
    error = GetLastError();
    if (had_original) (void)MoveFileA(backup, target);

failed:
    if (windows_error != NULL) *windows_error = (unsigned long)error;
    return -1;
}
