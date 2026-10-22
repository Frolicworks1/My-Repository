#include "ttpixel_core.h"

#include <cassert>
#include <cstdint>

int main() {
    TTPixelBuffer source{};
    assert(ttPixelBufferCreate(2, 2, &source) == TTPIXEL_OK);
    assert(ttPixelBufferWrite(&source, 0, 0, 0xFFFF0000u) == TTPIXEL_OK);
    assert(ttPixelBufferWrite(&source, 1, 0, 0xFF00FF00u) == TTPIXEL_OK);
    assert(ttPixelBufferWrite(&source, 0, 1, 0xFF0000FFu) == TTPIXEL_OK);
    assert(ttPixelBufferWrite(&source, 1, 1, 0x00000000u) == TTPIXEL_OK);

    TTPixelBuffer copy{};
    assert(ttPixelBufferCopy(&source, &copy) == TTPIXEL_OK);
    uint32_t pixel = 0;
    assert(ttPixelBufferRead(&copy, 1, 1, &pixel) == TTPIXEL_OK);
    assert(pixel == 0x00000000u);

    TTPixelBuffer scaled{};
    assert(ttPixelBufferResampleNearest(&source, 4, 4, &scaled) == TTPIXEL_OK);
    assert(ttPixelBufferRead(&scaled, 0, 0, &pixel) == TTPIXEL_OK);
    assert(pixel == 0xFFFF0000u);
    assert(ttPixelBufferRead(&scaled, 3, 3, &pixel) == TTPIXEL_OK);
    assert(pixel == 0x00000000u);

    TTPixelBuffer invalid{};
    assert(ttPixelBufferCreate(0, 2, &invalid) == TTPIXEL_INVALID_DIMENSIONS);
    assert(ttPixelBufferCreate(TTPIXEL_MAX_DIMENSION + 1, 1, &invalid) ==
           TTPIXEL_INVALID_DIMENSIONS);
    assert(ttPixelBufferRead(&source, 2, 0, &pixel) == TTPIXEL_INVALID_ARGUMENT);

    ttPixelBufferDestroy(&scaled);
    ttPixelBufferDestroy(&copy);
    ttPixelBufferDestroy(&source);
    ttPixelBufferDestroy(nullptr);
    return 0;
}
