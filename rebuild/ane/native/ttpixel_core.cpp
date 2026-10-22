#include "ttpixel_core.h"

#include <cstdlib>
#include <cstring>
#include <limits>

namespace {
bool valid_buffer(const TTPixelBuffer *buffer) {
    if (buffer == nullptr || buffer->pixels == nullptr ||
        buffer->width == 0 || buffer->height == 0 ||
        buffer->width > TTPIXEL_MAX_DIMENSION ||
        buffer->height > TTPIXEL_MAX_DIMENSION) {
        return false;
    }
    const uint64_t count = static_cast<uint64_t>(buffer->width) * buffer->height;
    return count <= TTPIXEL_MAX_PIXELS;
}

TTPixelStatus checked_count(uint32_t width, uint32_t height, size_t *out_count) {
    if (out_count == nullptr || width == 0 || height == 0 ||
        width > TTPIXEL_MAX_DIMENSION || height > TTPIXEL_MAX_DIMENSION) {
        return TTPIXEL_INVALID_DIMENSIONS;
    }
    const uint64_t count = static_cast<uint64_t>(width) * height;
    if (count > TTPIXEL_MAX_PIXELS ||
        count > std::numeric_limits<size_t>::max() / sizeof(uint32_t)) {
        return TTPIXEL_SIZE_OVERFLOW;
    }
    *out_count = static_cast<size_t>(count);
    return TTPIXEL_OK;
}
}  // namespace

extern "C" TTPixelStatus ttPixelBufferCreate(uint32_t width, uint32_t height,
                                             TTPixelBuffer *out_buffer) {
    if (out_buffer == nullptr) return TTPIXEL_INVALID_ARGUMENT;
    out_buffer->width = 0;
    out_buffer->height = 0;
    out_buffer->pixels = nullptr;

    size_t count = 0;
    const TTPixelStatus status = checked_count(width, height, &count);
    if (status != TTPIXEL_OK) return status;

    auto *pixels = static_cast<uint32_t *>(std::calloc(count, sizeof(uint32_t)));
    if (pixels == nullptr) return TTPIXEL_OUT_OF_MEMORY;
    out_buffer->width = width;
    out_buffer->height = height;
    out_buffer->pixels = pixels;
    return TTPIXEL_OK;
}

extern "C" void ttPixelBufferDestroy(TTPixelBuffer *buffer) {
    if (buffer == nullptr) return;
    std::free(buffer->pixels);
    buffer->pixels = nullptr;
    buffer->width = 0;
    buffer->height = 0;
}

extern "C" TTPixelStatus ttPixelBufferCopy(const TTPixelBuffer *source,
                                            TTPixelBuffer *out_buffer) {
    if (out_buffer == nullptr || !valid_buffer(source))
        return TTPIXEL_INVALID_ARGUMENT;
    TTPixelStatus status = ttPixelBufferCreate(source->width, source->height, out_buffer);
    if (status != TTPIXEL_OK) return status;
    const size_t bytes = static_cast<size_t>(source->width) * source->height *
                         sizeof(uint32_t);
    std::memcpy(out_buffer->pixels, source->pixels, bytes);
    return TTPIXEL_OK;
}

extern "C" TTPixelStatus ttPixelBufferResampleNearest(
    const TTPixelBuffer *source, uint32_t width, uint32_t height,
    TTPixelBuffer *out_buffer) {
    if (out_buffer == nullptr || !valid_buffer(source))
        return TTPIXEL_INVALID_ARGUMENT;
    TTPixelStatus status = ttPixelBufferCreate(width, height, out_buffer);
    if (status != TTPIXEL_OK) return status;

    for (uint32_t y = 0; y < height; ++y) {
        const uint32_t sy = static_cast<uint32_t>(
            (static_cast<uint64_t>(y) * source->height) / height);
        for (uint32_t x = 0; x < width; ++x) {
            const uint32_t sx = static_cast<uint32_t>(
                (static_cast<uint64_t>(x) * source->width) / width);
            out_buffer->pixels[static_cast<size_t>(y) * width + x] =
                source->pixels[static_cast<size_t>(sy) * source->width + sx];
        }
    }
    return TTPIXEL_OK;
}

extern "C" TTPixelStatus ttPixelBufferRead(const TTPixelBuffer *buffer,
                                             uint32_t x, uint32_t y,
                                             uint32_t *out_argb) {
    if (!valid_buffer(buffer) || out_argb == nullptr)
        return TTPIXEL_INVALID_ARGUMENT;
    if (x >= buffer->width || y >= buffer->height)
        return TTPIXEL_INVALID_ARGUMENT;
    *out_argb = buffer->pixels[static_cast<size_t>(y) * buffer->width + x];
    return TTPIXEL_OK;
}

extern "C" TTPixelStatus ttPixelBufferWrite(TTPixelBuffer *buffer,
                                              uint32_t x, uint32_t y,
                                              uint32_t argb) {
    if (!valid_buffer(buffer)) return TTPIXEL_INVALID_ARGUMENT;
    if (x >= buffer->width || y >= buffer->height)
        return TTPIXEL_INVALID_ARGUMENT;
    buffer->pixels[static_cast<size_t>(y) * buffer->width + x] = argb;
    return TTPIXEL_OK;
}
