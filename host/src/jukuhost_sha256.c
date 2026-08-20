#include "jukuhost.h"

#include <string.h>

static uint32_t rotate_right(uint32_t value, unsigned count)
{
    return (value >> count) | (value << (32u - count));
}

static uint32_t get_u32be(const uint8_t *input)
{
    return (uint32_t)input[0] << 24 | (uint32_t)input[1] << 16 |
        (uint32_t)input[2] << 8 | (uint32_t)input[3];
}

static void put_u32be(uint8_t *output, uint32_t value)
{
    output[0] = (uint8_t)(value >> 24);
    output[1] = (uint8_t)(value >> 16);
    output[2] = (uint8_t)(value >> 8);
    output[3] = (uint8_t)value;
}

static void transform(struct jh_sha256_state *context, const uint8_t block[64])
{
    static const uint32_t constants[64] = {
        UINT32_C(0x428a2f98), UINT32_C(0x71374491), UINT32_C(0xb5c0fbcf),
        UINT32_C(0xe9b5dba5), UINT32_C(0x3956c25b), UINT32_C(0x59f111f1),
        UINT32_C(0x923f82a4), UINT32_C(0xab1c5ed5), UINT32_C(0xd807aa98),
        UINT32_C(0x12835b01), UINT32_C(0x243185be), UINT32_C(0x550c7dc3),
        UINT32_C(0x72be5d74), UINT32_C(0x80deb1fe), UINT32_C(0x9bdc06a7),
        UINT32_C(0xc19bf174), UINT32_C(0xe49b69c1), UINT32_C(0xefbe4786),
        UINT32_C(0x0fc19dc6), UINT32_C(0x240ca1cc), UINT32_C(0x2de92c6f),
        UINT32_C(0x4a7484aa), UINT32_C(0x5cb0a9dc), UINT32_C(0x76f988da),
        UINT32_C(0x983e5152), UINT32_C(0xa831c66d), UINT32_C(0xb00327c8),
        UINT32_C(0xbf597fc7), UINT32_C(0xc6e00bf3), UINT32_C(0xd5a79147),
        UINT32_C(0x06ca6351), UINT32_C(0x14292967), UINT32_C(0x27b70a85),
        UINT32_C(0x2e1b2138), UINT32_C(0x4d2c6dfc), UINT32_C(0x53380d13),
        UINT32_C(0x650a7354), UINT32_C(0x766a0abb), UINT32_C(0x81c2c92e),
        UINT32_C(0x92722c85), UINT32_C(0xa2bfe8a1), UINT32_C(0xa81a664b),
        UINT32_C(0xc24b8b70), UINT32_C(0xc76c51a3), UINT32_C(0xd192e819),
        UINT32_C(0xd6990624), UINT32_C(0xf40e3585), UINT32_C(0x106aa070),
        UINT32_C(0x19a4c116), UINT32_C(0x1e376c08), UINT32_C(0x2748774c),
        UINT32_C(0x34b0bcb5), UINT32_C(0x391c0cb3), UINT32_C(0x4ed8aa4a),
        UINT32_C(0x5b9cca4f), UINT32_C(0x682e6ff3), UINT32_C(0x748f82ee),
        UINT32_C(0x78a5636f), UINT32_C(0x84c87814), UINT32_C(0x8cc70208),
        UINT32_C(0x90befffa), UINT32_C(0xa4506ceb), UINT32_C(0xbef9a3f7),
        UINT32_C(0xc67178f2)
    };
    uint32_t words[64];
    uint32_t a = context->state[0];
    uint32_t b = context->state[1];
    uint32_t c = context->state[2];
    uint32_t d = context->state[3];
    uint32_t e = context->state[4];
    uint32_t f = context->state[5];
    uint32_t g = context->state[6];
    uint32_t h = context->state[7];
    unsigned index;
    for (index = 0u; index < 16u; ++index) {
        words[index] = get_u32be(block + index * 4u);
    }
    for (; index < 64u; ++index) {
        uint32_t s0 = rotate_right(words[index - 15u], 7u) ^
            rotate_right(words[index - 15u], 18u) ^
            (words[index - 15u] >> 3);
        uint32_t s1 = rotate_right(words[index - 2u], 17u) ^
            rotate_right(words[index - 2u], 19u) ^
            (words[index - 2u] >> 10);
        words[index] = words[index - 16u] + s0 + words[index - 7u] + s1;
    }
    for (index = 0u; index < 64u; ++index) {
        uint32_t sum1 = rotate_right(e, 6u) ^ rotate_right(e, 11u) ^
            rotate_right(e, 25u);
        uint32_t choose = (e & f) ^ (~e & g);
        uint32_t temporary1 = h + sum1 + choose + constants[index] + words[index];
        uint32_t sum0 = rotate_right(a, 2u) ^ rotate_right(a, 13u) ^
            rotate_right(a, 22u);
        uint32_t majority = (a & b) ^ (a & c) ^ (b & c);
        uint32_t temporary2 = sum0 + majority;
        h = g;
        g = f;
        f = e;
        e = d + temporary1;
        d = c;
        c = b;
        b = a;
        a = temporary1 + temporary2;
    }
    context->state[0] += a;
    context->state[1] += b;
    context->state[2] += c;
    context->state[3] += d;
    context->state[4] += e;
    context->state[5] += f;
    context->state[6] += g;
    context->state[7] += h;
}

void jh_sha256_init(struct jh_sha256_state *context)
{
    static const uint32_t initial[8] = {
        UINT32_C(0x6a09e667), UINT32_C(0xbb67ae85), UINT32_C(0x3c6ef372),
        UINT32_C(0xa54ff53a), UINT32_C(0x510e527f), UINT32_C(0x9b05688c),
        UINT32_C(0x1f83d9ab), UINT32_C(0x5be0cd19)
    };
    memcpy(context->state, initial, sizeof(initial));
    context->bits = 0u;
    context->used = 0u;
}

void jh_sha256_update(struct jh_sha256_state *context,
                      const uint8_t *data, size_t length)
{
    while (length != 0u) {
        size_t available = sizeof(context->block) - context->used;
        size_t take = length < available ? length : available;
        memcpy(context->block + context->used, data, take);
        context->used += take;
        data += take;
        length -= take;
        context->bits += (uint64_t)take * 8u;
        if (context->used == sizeof(context->block)) {
            transform(context, context->block);
            context->used = 0u;
        }
    }
}

void jh_sha256_final(struct jh_sha256_state *context,
                     uint8_t output[JH_SHA256_SIZE])
{
    unsigned index;
    context->block[context->used++] = 0x80u;
    if (context->used > 56u) {
        memset(context->block + context->used, 0,
               sizeof(context->block) - context->used);
        transform(context, context->block);
        context->used = 0u;
    }
    memset(context->block + context->used, 0, 56u - context->used);
    for (index = 0u; index < 8u; ++index) {
        context->block[63u - index] = (uint8_t)(context->bits >> (index * 8u));
    }
    transform(context, context->block);
    for (index = 0u; index < 8u; ++index) {
        put_u32be(output + index * 4u, context->state[index]);
    }
}

void jh_sha256(const uint8_t *data, size_t length,
               uint8_t output[JH_SHA256_SIZE])
{
    struct jh_sha256_state context;
    jh_sha256_init(&context);
    if (length != 0u && data != NULL) jh_sha256_update(&context, data, length);
    jh_sha256_final(&context, output);
}

static int hex_value(char character)
{
    if (character >= '0' && character <= '9') return character - '0';
    if (character >= 'a' && character <= 'f') return character - 'a' + 10;
    if (character >= 'A' && character <= 'F') return character - 'A' + 10;
    return -1;
}

int jh_sha256_parse(const char *text, uint8_t output[JH_SHA256_SIZE])
{
    size_t index;
    if (text == NULL || output == NULL || strlen(text) != JH_SHA256_HEX_SIZE) {
        return JH_ERR_ARGUMENT;
    }
    for (index = 0u; index < JH_SHA256_SIZE; ++index) {
        int high = hex_value(text[index * 2u]);
        int low = hex_value(text[index * 2u + 1u]);
        if (high < 0 || low < 0) return JH_ERR_FORMAT;
        output[index] = (uint8_t)((unsigned)high << 4 | (unsigned)low);
    }
    return JH_OK;
}

void jh_sha256_format(const uint8_t digest[JH_SHA256_SIZE],
                      char output[JH_SHA256_HEX_SIZE + 1u])
{
    static const char hex[] = "0123456789abcdef";
    size_t index;
    for (index = 0u; index < JH_SHA256_SIZE; ++index) {
        output[index * 2u] = hex[digest[index] >> 4];
        output[index * 2u + 1u] = hex[digest[index] & 0x0fu];
    }
    output[JH_SHA256_HEX_SIZE] = '\0';
}
