#include <jni.h>
#include <cstdint>
#include <new>
#include "ttpixel_core.h"

/* JNI adapter for Android-side integration testing.
 * This is NOT an Adobe AIR FRE/ANE adapter; that ABI remains separate. */
namespace {
TTPixelBuffer *from_handle(jlong handle) {
    return reinterpret_cast<TTPixelBuffer *>(static_cast<uintptr_t>(handle));
}
jlong to_handle(TTPixelBuffer *buffer) {
    return static_cast<jlong>(reinterpret_cast<uintptr_t>(buffer));
}
}

extern "C" JNIEXPORT jlong JNICALL Java_com_frolicworks_ttpixel_NativePixelCore_nativeCreate(JNIEnv *, jclass, jint width, jint height) {
    if (width <= 0 || height <= 0) return 0;
    auto *buffer = new (std::nothrow) TTPixelBuffer{};
    if (!buffer) return 0;
    if (ttPixelBufferCreate(static_cast<uint32_t>(width), static_cast<uint32_t>(height), buffer) != TTPIXEL_OK) {
        delete buffer; return 0;
    }
    return to_handle(buffer);
}
extern "C" JNIEXPORT void JNICALL Java_com_frolicworks_ttpixel_NativePixelCore_nativeDestroy(JNIEnv *, jclass, jlong handle) {
    auto *buffer = from_handle(handle);
    if (!buffer) return;
    ttPixelBufferDestroy(buffer); delete buffer;
}
extern "C" JNIEXPORT jint JNICALL Java_com_frolicworks_ttpixel_NativePixelCore_nativeWrite(JNIEnv *, jclass, jlong handle, jint x, jint y, jint argb) {
    auto *buffer = from_handle(handle);
    if (!buffer || x < 0 || y < 0) return TTPIXEL_INVALID_ARGUMENT;
    return static_cast<jint>(ttPixelBufferWrite(buffer, static_cast<uint32_t>(x), static_cast<uint32_t>(y), static_cast<uint32_t>(argb)));
}
extern "C" JNIEXPORT jint JNICALL Java_com_frolicworks_ttpixel_NativePixelCore_nativeRead(JNIEnv *, jclass, jlong handle, jint x, jint y) {
    auto *buffer = from_handle(handle);
    if (!buffer || x < 0 || y < 0) return 0;
    uint32_t pixel = 0;
    if (ttPixelBufferRead(buffer, static_cast<uint32_t>(x), static_cast<uint32_t>(y), &pixel) != TTPIXEL_OK) return 0;
    return static_cast<jint>(pixel);
}
extern "C" JNIEXPORT jlong JNICALL Java_com_frolicworks_ttpixel_NativePixelCore_nativeCopy(JNIEnv *, jclass, jlong handle) {
    auto *source = from_handle(handle);
    if (!source) return 0;
    auto *copy = new (std::nothrow) TTPixelBuffer{};
    if (!copy) return 0;
    if (ttPixelBufferCopy(source, copy) != TTPIXEL_OK) { delete copy; return 0; }
    return to_handle(copy);
}
extern "C" JNIEXPORT jlong JNICALL Java_com_frolicworks_ttpixel_NativePixelCore_nativeResampleNearest(JNIEnv *, jclass, jlong handle, jint width, jint height) {
    auto *source = from_handle(handle);
    if (!source || width <= 0 || height <= 0) return 0;
    auto *scaled = new (std::nothrow) TTPixelBuffer{};
    if (!scaled) return 0;
    if (ttPixelBufferResampleNearest(source, static_cast<uint32_t>(width), static_cast<uint32_t>(height), scaled) != TTPIXEL_OK) { delete scaled; return 0; }
    return to_handle(scaled);
}
extern "C" JNIEXPORT jint JNICALL Java_com_frolicworks_ttpixel_NativePixelCore_nativeWidth(JNIEnv *, jclass, jlong handle) {
    auto *buffer = from_handle(handle); return buffer ? static_cast<jint>(buffer->width) : 0;
}
extern "C" JNIEXPORT jint JNICALL Java_com_frolicworks_ttpixel_NativePixelCore_nativeHeight(JNIEnv *, jclass, jlong handle) {
    auto *buffer = from_handle(handle); return buffer ? static_cast<jint>(buffer->height) : 0;
}
