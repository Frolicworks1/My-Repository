#ifndef TTPIXEL_CORE_H
#define TTPIXEL_CORE_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Clean-room pixel-buffer primitives for the TTPixel ARM64 migration.
 * This is NOT the AIR FRE/ANE bridge and does not claim SWF compatibility.
 * Pixels are tightly packed 0xAARRGGBB uint32_t values, row-major.
 */
typedef struct TTPixelBuffer {
    uint32_t width;
    uint32_t height;
    uint32_t *pixels;
} TTPixelBuffer;

typedef enum TTPixelStatus {
    TTPIXEL_OK = 0,
    TTPIXEL_INVALID_ARGUMENT = 1,
    TTPIXEL_INVALID_DIMENSIONS = 2,
    TTPIXEL_SIZE_OVERFLOW = 3,
    TTPIXEL_OUT_OF_MEMORY = 4
} TTPixelStatus;

#define TTPIXEL_MAX_DIMENSION 16384u
#define TTPIXEL_MAX_PIXELS 67108864u

TTPixelStatus ttPixelBufferCreate(uint32_t width, uint32_t height,
                                  TTPixelBuffer *out_buffer);
void ttPixelBufferDestroy(TTPixelBuffer *buffer);
TTPixelStatus ttPixelBufferCopy(const TTPixelBuffer *source,
                                TTPixelBuffer *out_buffer);
TTPixelStatus ttPixelBufferResampleNearest(const TTPixelBuffer *source,
                                           uint32_t width, uint32_t height,
                                           TTPixelBuffer *out_buffer);
TTPixelStatus ttPixelBufferRead(const TTPixelBuffer *buffer,
                                uint32_t x, uint32_t y, uint32_t *out_argb);
TTPixelStatus ttPixelBufferWrite(TTPixelBuffer *buffer,
                                 uint32_t x, uint32_t y, uint32_t argb);

#ifdef __cplusplus
}
#endif
#endif
