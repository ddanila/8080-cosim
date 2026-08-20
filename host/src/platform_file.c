#include "platform.h"

#include <errno.h>
#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#if defined(__WATCOMC__) && defined(__DOS__)
#include <io.h>
#define JH_OPEN _open
#define JH_READ _read
#define JH_WRITE _write
#define JH_CLOSE _close
#define JH_SYNC _commit
#else
#include <unistd.h>
#define JH_OPEN open
#define JH_READ read
#define JH_WRITE write
#define JH_CLOSE close
#define JH_SYNC fsync
#endif

#ifndef O_BINARY
#define O_BINARY 0
#endif

static int sync_file(FILE *file)
{
    if (fflush(file) != 0) return -1;
#if defined(__WATCOMC__) && defined(__DOS__)
    /* DOSBox-X's mounted-directory backend returns ENOENT for DOS 3.3
       commit (INT 21h/AH=68h) even after it has written the complete file.
       A close immediately follows for short-lived journal/artifact files;
       the long-lived disk image remains fflush'ed. A physical DOS runtime
       that implements commit still gets the stronger flush. */
    if (_commit(fileno(file)) != 0) {
        if (errno != ENOENT) return -1;
        errno = 0;
    }
    return 0;
#else
    return fsync(fileno(file));
#endif
}

int jh_platform_file_identity(const char *path, uint32_t *size,
                              uint8_t digest[JH_SHA256_SIZE])
{
    struct jh_sha256_state state;
    uint8_t buffer[4096];
    uint32_t total = 0u;
    FILE *file;
    size_t got;
    if (path == NULL || size == NULL || digest == NULL) {
        errno = EINVAL;
        return -1;
    }
    file = fopen(path, "rb");
    if (file == NULL) return -1;
    jh_sha256_init(&state);
    while ((got = fread(buffer, 1u, sizeof(buffer), file)) != 0u) {
        if (UINT32_MAX - total < (uint32_t)got) {
            fclose(file);
            errno = EFBIG;
            return -1;
        }
        jh_sha256_update(&state, buffer, got);
        total += (uint32_t)got;
    }
    if (ferror(file) || fclose(file) != 0) return -1;
    jh_sha256_final(&state, digest);
    *size = total;
    return 0;
}

int jh_platform_copy_file(const char *source, const char *target)
{
    uint8_t buffer[4096];
    int input;
    int output;
    int result = -1;
    long got;
    input = JH_OPEN(source, O_RDONLY | O_BINARY);
    if (input < 0) return -1;
    output = JH_OPEN(target, O_WRONLY | O_CREAT | O_TRUNC | O_BINARY,
                     S_IREAD | S_IWRITE);
    if (output < 0) {
        (void)JH_CLOSE(input);
        return -1;
    }
    while ((got = JH_READ(input, buffer, sizeof(buffer))) > 0) {
        long position = 0;
        while (position < got) {
            long written = JH_WRITE(output, buffer + (size_t)position,
                                    (size_t)(got - position));
            if (written <= 0) goto done;
            position += written;
        }
    }
    if (got == 0 && (JH_SYNC(output) == 0
#if defined(__WATCOMC__) && defined(__DOS__)
            || errno == ENOENT
#endif
            )) result = 0;
done:
    if (JH_CLOSE(output) != 0) result = -1;
    if (JH_CLOSE(input) != 0) result = -1;
    return result;
}

int jh_platform_load_file(const char *path, uint8_t **data, size_t *length)
{
    FILE *file;
    long file_length;
    uint8_t *buffer;
    if (path == NULL || data == NULL || length == NULL) {
        errno = EINVAL;
        return -1;
    }
    file = fopen(path, "rb");
    if (file == NULL) return -1;
    if (fseek(file, 0L, SEEK_END) != 0 ||
            (file_length = ftell(file)) < 0L ||
            (uint32_t)file_length > (uint32_t)SIZE_MAX ||
            fseek(file, 0L, SEEK_SET) != 0) {
        fclose(file);
        errno = EFBIG;
        return -1;
    }
    buffer = (uint8_t *)malloc(file_length == 0L ? 1u : (size_t)file_length);
    if (buffer == NULL) {
        fclose(file);
        return -1;
    }
    if (file_length != 0L && fread(buffer, 1u, (size_t)file_length, file) !=
            (size_t)file_length) {
        free(buffer);
        fclose(file);
        errno = EIO;
        return -1;
    }
    if (fclose(file) != 0) {
        free(buffer);
        return -1;
    }
    *data = buffer;
    *length = (size_t)file_length;
    return 0;
}

int jh_platform_write_file(const char *path, const uint8_t *data,
                           size_t length, int sync_data)
{
    FILE *file;
    int result = 0;
    if (path == NULL || (data == NULL && length != 0u)) {
        errno = EINVAL;
        return -1;
    }
    file = fopen(path, "wb");
    if (file == NULL) return -1;
    if (length != 0u && fwrite(data, 1u, length, file) != length) result = -1;
    if (result == 0 && sync_data && sync_file(file) != 0) result = -1;
    if (fclose(file) != 0) result = -1;
    return result;
}

int jh_platform_remove_file(const char *path)
{
    return remove(path) == 0 || errno == ENOENT ? 0 : -1;
}

int jh_platform_media_open(struct jh_platform_media *media, const char *path,
                           uint32_t expected_size, int writable,
                           int native_order)
{
    long size;
    if (media == NULL || path == NULL) {
        errno = EINVAL;
        return -1;
    }
    memset(media, 0, sizeof(*media));
    media->file = fopen(path, writable ? "r+b" : "rb");
    if (media->file == NULL) return -1;
    if (fseek(media->file, 0L, SEEK_END) != 0 ||
            (size = ftell(media->file)) < 0L ||
            (uint32_t)size != expected_size ||
            fseek(media->file, 0L, SEEK_SET) != 0) {
        fclose(media->file);
        media->file = NULL;
        errno = EINVAL;
        return -1;
    }
    media->size = expected_size;
    media->writable = writable != 0;
    media->native_order = native_order != 0;
    return 0;
}

void jh_platform_media_close(struct jh_platform_media *media)
{
    if (media != NULL && media->file != NULL) {
        (void)fclose(media->file);
        media->file = NULL;
    }
}

static uint32_t physical_offset(const struct jh_platform_media *media,
                                uint32_t logical)
{
    uint32_t track;
    uint32_t within;
    uint32_t cylinder;
    uint32_t side;
    if (!media->native_order) return logical;
    track = logical / JH_N3_TRACK_SIZE;
    within = logical % JH_N3_TRACK_SIZE;
    cylinder = track % JH_N3_TRACKS;
    side = track / JH_N3_TRACKS;
    return (cylinder * 2u + side) * JH_N3_TRACK_SIZE + within;
}

int jh_platform_media_read(void *context, uint32_t offset,
                           uint8_t record[JH_N3_RECORD_SIZE])
{
    struct jh_platform_media *media = (struct jh_platform_media *)context;
    uint32_t position;
    if (media == NULL || media->file == NULL || record == NULL ||
            offset > media->size ||
            media->size - offset < JH_N3_RECORD_SIZE) return JH_ERR_RANGE;
    position = physical_offset(media, offset);
    if (fseek(media->file, (long)position, SEEK_SET) != 0 ||
            fread(record, 1u, JH_N3_RECORD_SIZE, media->file) !=
                JH_N3_RECORD_SIZE) return JH_ERR_FORMAT;
    return JH_OK;
}

int jh_platform_media_write(void *context, uint32_t offset,
                            const uint8_t record[JH_N3_RECORD_SIZE])
{
    struct jh_platform_media *media = (struct jh_platform_media *)context;
    uint32_t position;
    if (media == NULL || media->file == NULL || record == NULL) {
        return JH_ERR_ARGUMENT;
    }
    if (!media->writable) return JH_ERR_READ_ONLY;
    if (offset > media->size ||
            media->size - offset < JH_N3_RECORD_SIZE) return JH_ERR_RANGE;
    position = physical_offset(media, offset);
    if (fseek(media->file, (long)position, SEEK_SET) != 0 ||
            fwrite(record, 1u, JH_N3_RECORD_SIZE, media->file) !=
                JH_N3_RECORD_SIZE || sync_file(media->file) != 0) {
        return JH_ERR_FORMAT;
    }
    return JH_OK;
}
