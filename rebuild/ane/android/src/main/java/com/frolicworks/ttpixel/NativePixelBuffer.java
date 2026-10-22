package com.frolicworks.ttpixel;

/**
 * Small ownership-safe Java wrapper for the clean-room JNI pixel core.
 *
 * This is a development primitive, not the original Photoshop Touch AIR ANE.
 * Instances own one native handle and must be closed; use try-with-resources.
 */
public final class NativePixelBuffer implements AutoCloseable {
    private long handle;

    private NativePixelBuffer(long handle) {
        if (handle == 0) {
            throw new OutOfMemoryError("Could not allocate native pixel buffer");
        }
        this.handle = handle;
    }

    public static NativePixelBuffer create(int width, int height) {
        return new NativePixelBuffer(NativePixelCore.nativeCreate(width, height));
    }

    public int width() {
        return NativePixelCore.nativeWidth(requireHandle());
    }

    public int height() {
        return NativePixelCore.nativeHeight(requireHandle());
    }

    /** Writes an ARGB pixel. Returns the native status code (0 means success). */
    public int write(int x, int y, int argb) {
        return NativePixelCore.nativeWrite(requireHandle(), x, y, argb);
    }

    /** Reads an ARGB pixel. A returned zero may also indicate an invalid read. */
    public int read(int x, int y) {
        return NativePixelCore.nativeRead(requireHandle(), x, y);
    }

    public NativePixelBuffer copy() {
        return new NativePixelBuffer(NativePixelCore.nativeCopy(requireHandle()));
    }

    public NativePixelBuffer resampleNearest(int width, int height) {
        return new NativePixelBuffer(
                NativePixelCore.nativeResampleNearest(requireHandle(), width, height));
    }

    private long requireHandle() {
        if (handle == 0) {
            throw new IllegalStateException("Native pixel buffer is closed");
        }
        return handle;
    }

    @Override
    public void close() {
        long owned = handle;
        handle = 0;
        if (owned != 0) {
            NativePixelCore.nativeDestroy(owned);
        }
    }
}
