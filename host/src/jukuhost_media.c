#include "jukuhost.h"

#include <string.h>

int jh_media_init(struct jh_media *media, uint8_t *bytes, size_t size,
                  unsigned tracks, int writable)
{
    if (media == NULL || bytes == NULL) return JH_ERR_ARGUMENT;
    if ((tracks != JH_N3_TRACKS && tracks != JH_N3_NATIVE_TRACKS) ||
            size != (size_t)tracks * JH_N3_TRACK_SIZE) {
        return JH_ERR_RANGE;
    }
    media->bytes = bytes;
    media->size = size;
    media->tracks = tracks;
    media->writable = writable != 0;
    return JH_OK;
}

int jh_media_read(const struct jh_media *media, unsigned track,
                  unsigned sector, uint8_t record[JH_N3_RECORD_SIZE])
{
    size_t offset;
    int result;
    if (media == NULL || record == NULL) return JH_ERR_ARGUMENT;
    result = jh_n3_record_offset(track, sector, media->tracks, &offset);
    if (result != JH_OK || offset + JH_N3_RECORD_SIZE > media->size) {
        return JH_ERR_RANGE;
    }
    memcpy(record, media->bytes + offset, JH_N3_RECORD_SIZE);
    return JH_OK;
}

int jh_media_write(struct jh_media *media, unsigned track, unsigned sector,
                   const uint8_t record[JH_N3_RECORD_SIZE])
{
    size_t offset;
    int result;
    if (media == NULL || record == NULL) return JH_ERR_ARGUMENT;
    if (!media->writable) return JH_ERR_READ_ONLY;
    result = jh_n3_record_offset(track, sector, media->tracks, &offset);
    if (result != JH_OK || offset + JH_N3_RECORD_SIZE > media->size) {
        return JH_ERR_RANGE;
    }
    memcpy(media->bytes + offset, record, JH_N3_RECORD_SIZE);
    return JH_OK;
}

int jh_native_image_to_volume(const uint8_t *image, size_t image_length,
                              uint8_t *volume, size_t volume_capacity)
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
            size_t source = ((size_t)cylinder * 2u + side) * JH_N3_TRACK_SIZE;
            size_t target = ((size_t)side * JH_N3_TRACKS + cylinder) *
                JH_N3_TRACK_SIZE;
            memcpy(volume + target, image + source, JH_N3_TRACK_SIZE);
        }
    }
    return JH_OK;
}
