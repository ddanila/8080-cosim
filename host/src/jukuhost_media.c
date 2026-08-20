#include "jukuhost.h"

#include <string.h>

int jh_media_init(struct jh_media *media, uint8_t *bytes, uint32_t size,
                  unsigned tracks, int writable)
{
    if (media == NULL || bytes == NULL) return JH_ERR_ARGUMENT;
    if ((tracks != JH_N3_TRACKS && tracks != JH_N3_NATIVE_TRACKS) ||
            size != (uint32_t)tracks * JH_N3_TRACK_SIZE) {
        return JH_ERR_RANGE;
    }
    media->bytes = bytes;
    media->context = NULL;
    media->read_offset = NULL;
    media->write_offset = NULL;
    media->size = size;
    media->tracks = tracks;
    media->writable = writable != 0;
    return JH_OK;
}

int jh_media_init_backend(struct jh_media *media, void *context,
                          uint32_t size, unsigned tracks, int writable,
                          int (*read_offset)(void *, uint32_t, uint8_t *),
                          int (*write_offset)(void *, uint32_t,
                                              const uint8_t *))
{
    if (media == NULL || context == NULL || read_offset == NULL ||
            (writable && write_offset == NULL)) return JH_ERR_ARGUMENT;
    if ((tracks != JH_N3_TRACKS && tracks != JH_N3_NATIVE_TRACKS) ||
            size != (uint32_t)tracks * JH_N3_TRACK_SIZE) {
        return JH_ERR_RANGE;
    }
    media->bytes = NULL;
    media->context = context;
    media->read_offset = read_offset;
    media->write_offset = write_offset;
    media->size = size;
    media->tracks = tracks;
    media->writable = writable != 0;
    return JH_OK;
}

int jh_media_read_offset(const struct jh_media *media, uint32_t offset,
                         uint8_t record[JH_N3_RECORD_SIZE])
{
    if (media == NULL || record == NULL || offset > media->size ||
            media->size - offset < JH_N3_RECORD_SIZE) return JH_ERR_RANGE;
    if (media->read_offset != NULL) {
        return media->read_offset(media->context, offset, record);
    }
    if (media->bytes == NULL) return JH_ERR_ARGUMENT;
    memcpy(record, media->bytes + (size_t)offset, JH_N3_RECORD_SIZE);
    return JH_OK;
}

int jh_media_write_offset(struct jh_media *media, uint32_t offset,
                          const uint8_t record[JH_N3_RECORD_SIZE])
{
    if (media == NULL || record == NULL) return JH_ERR_ARGUMENT;
    if (!media->writable) return JH_ERR_READ_ONLY;
    if (offset > media->size || media->size - offset < JH_N3_RECORD_SIZE) {
        return JH_ERR_RANGE;
    }
    if (media->write_offset != NULL) {
        return media->write_offset(media->context, offset, record);
    }
    if (media->bytes == NULL) return JH_ERR_ARGUMENT;
    memcpy(media->bytes + (size_t)offset, record, JH_N3_RECORD_SIZE);
    return JH_OK;
}

int jh_media_read(const struct jh_media *media, unsigned track,
                  unsigned sector, uint8_t record[JH_N3_RECORD_SIZE])
{
    uint32_t offset;
    int result;
    if (media == NULL || record == NULL) return JH_ERR_ARGUMENT;
    result = jh_n3_record_offset(track, sector, media->tracks, &offset);
    if (result != JH_OK || offset + JH_N3_RECORD_SIZE > media->size) {
        return JH_ERR_RANGE;
    }
    return jh_media_read_offset(media, offset, record);
}

int jh_media_write(struct jh_media *media, unsigned track, unsigned sector,
                   const uint8_t record[JH_N3_RECORD_SIZE])
{
    uint32_t offset;
    int result;
    if (media == NULL || record == NULL) return JH_ERR_ARGUMENT;
    if (!media->writable) return JH_ERR_READ_ONLY;
    result = jh_n3_record_offset(track, sector, media->tracks, &offset);
    if (result != JH_OK || offset + JH_N3_RECORD_SIZE > media->size) {
        return JH_ERR_RANGE;
    }
    return jh_media_write_offset(media, offset, record);
}

int jh_native_image_to_volume(const uint8_t *image, uint32_t image_length,
                              uint8_t *volume, uint32_t volume_capacity)
{
    unsigned cylinder;
    unsigned side;
    if (image == NULL || volume == NULL) return JH_ERR_ARGUMENT;
    if (image_length != JH_N3_NATIVE_VOLUME_SIZE ||
            volume_capacity < JH_N3_NATIVE_VOLUME_SIZE) {
        return JH_ERR_RANGE;
    }
    for (cylinder = 0u; cylinder < JH_N3_TRACKS; ++cylinder) {
        for (side = 0u; side < 2u; ++side) {
            uint32_t source = ((uint32_t)cylinder * 2u + side) * JH_N3_TRACK_SIZE;
            uint32_t target = ((uint32_t)side * JH_N3_TRACKS + cylinder) *
                JH_N3_TRACK_SIZE;
            memcpy(volume + (size_t)target, image + (size_t)source,
                   (size_t)JH_N3_TRACK_SIZE);
        }
    }
    return JH_OK;
}
