#ifndef JUKUHOST_TEST_WINDOWS_H
#define JUKUHOST_TEST_WINDOWS_H

#include <stddef.h>
#include <stdint.h>

#define WINAPI
#define TRUE 1
#define FALSE 0

typedef int BOOL;
typedef uint8_t BYTE;
typedef uint32_t DWORD;
typedef int32_t LONG;
typedef void *HANDLE;
typedef void *HMODULE;
typedef void (*FARPROC)(void);
typedef const char *LPCSTR;
typedef void *LPVOID;
typedef DWORD *LPDWORD;

#define INVALID_HANDLE_VALUE ((HANDLE)(intptr_t)-1)
#define MAXDWORD UINT32_MAX

#define CTRL_C_EVENT 0u
#define CTRL_BREAK_EVENT 1u
#define CTRL_CLOSE_EVENT 2u
#define CTRL_LOGOFF_EVENT 5u
#define CTRL_SHUTDOWN_EVENT 6u

#define ERROR_FILE_NOT_FOUND 2u
#define ERROR_SUCCESS 0u
#define ERROR_PATH_NOT_FOUND 3u
#define ERROR_ACCESS_DENIED 5u
#define ERROR_NOT_ENOUGH_MEMORY 8u
#define ERROR_INVALID_PARAMETER 87u
#define ERROR_INVALID_NAME 123u
#define ERROR_SEM_TIMEOUT 121u
#define ERROR_OUTOFMEMORY 14u
#define ERROR_SHARING_VIOLATION 32u
#define ERROR_DEVICE_NOT_CONNECTED 1167u
#define ERROR_TIMEOUT 1460u

#define GENERIC_READ 0x80000000u
#define GENERIC_WRITE 0x40000000u
#define OPEN_EXISTING 3u
#define MOVEFILE_REPLACE_EXISTING 0x00000001u
#define MOVEFILE_WRITE_THROUGH 0x00000008u

#define DTR_CONTROL_ENABLE 1u
#define RTS_CONTROL_ENABLE 1u
#define NOPARITY 0u
#define ODDPARITY 1u
#define ONESTOPBIT 0u

#define PURGE_TXABORT 0x0001u
#define PURGE_RXABORT 0x0002u
#define PURGE_TXCLEAR 0x0004u
#define PURGE_RXCLEAR 0x0008u

#define CE_RXOVER 0x0001u
#define CE_OVERRUN 0x0002u
#define CE_RXPARITY 0x0004u
#define CE_FRAME 0x0008u

typedef struct _DCB {
    DWORD DCBlength;
    DWORD BaudRate;
    unsigned fBinary;
    unsigned fParity;
    unsigned fOutxCtsFlow;
    unsigned fOutxDsrFlow;
    unsigned fDtrControl;
    unsigned fDsrSensitivity;
    unsigned fTXContinueOnXoff;
    unsigned fOutX;
    unsigned fInX;
    unsigned fErrorChar;
    unsigned fNull;
    unsigned fRtsControl;
    unsigned fAbortOnError;
    BYTE ByteSize;
    BYTE Parity;
    BYTE StopBits;
} DCB;

typedef struct _COMMTIMEOUTS {
    DWORD ReadIntervalTimeout;
    DWORD ReadTotalTimeoutMultiplier;
    DWORD ReadTotalTimeoutConstant;
    DWORD WriteTotalTimeoutMultiplier;
    DWORD WriteTotalTimeoutConstant;
} COMMTIMEOUTS;

typedef struct _COMSTAT {
    DWORD cbInQue;
    DWORD cbOutQue;
} COMSTAT;

typedef struct _MEMORYSTATUS {
    DWORD dwLength;
    DWORD dwMemoryLoad;
    DWORD dwTotalPhys;
    DWORD dwAvailPhys;
} MEMORYSTATUS;

typedef BOOL (WINAPI *PHANDLER_ROUTINE)(DWORD);

BOOL SetConsoleCtrlHandler(PHANDLER_ROUTINE handler, BOOL add);
LONG InterlockedExchange(LONG *target, LONG value);
DWORD GetTickCount(void);
void Sleep(DWORD milliseconds);
void GlobalMemoryStatus(MEMORYSTATUS *status);
BOOL SetCommTimeouts(HANDLE handle, COMMTIMEOUTS *timeouts);
BOOL SetCommState(HANDLE handle, DCB *state);
BOOL GetCommState(HANDLE handle, DCB *state);
BOOL PurgeComm(HANDLE handle, DWORD flags);
BOOL SetupComm(HANDLE handle, DWORD input, DWORD output);
HANDLE CreateFileA(LPCSTR path, DWORD access, DWORD share, LPVOID security,
                   DWORD creation, DWORD flags, HANDLE template_file);
BOOL CloseHandle(HANDLE handle);
BOOL ClearCommError(HANDLE handle, DWORD *errors, COMSTAT *status);
BOOL ReadFile(HANDLE handle, LPVOID output, DWORD amount, DWORD *received,
              LPVOID overlapped);
BOOL WriteFile(HANDLE handle, const void *data, DWORD amount, DWORD *written,
               LPVOID overlapped);
DWORD GetLastError(void);
HMODULE GetModuleHandleA(LPCSTR module);
FARPROC GetProcAddress(HMODULE module, LPCSTR name);
BOOL DeleteFileA(LPCSTR path);
#define ERROR_CALL_NOT_IMPLEMENTED 120u
BOOL MoveFileA(LPCSTR source, LPCSTR target);

#endif
