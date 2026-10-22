package com.frolicworks.ttpixel;

/** JNI access to the clean-room pixel core; not the original AIR TTPixel ANE API. */
public final class NativePixelCore {
    static { System.loadLibrary("ttpixel_core"); }
    private NativePixelCore() {}
    public static native long nativeCreate(int width, int height);
    public static native void nativeDestroy(long handle);
    public static native int nativeWrite(long handle, int x, int y, int argb);
    public static native int nativeRead(long handle, int x, int y);
    public static native long nativeCopy(long handle);
    public static native long nativeResampleNearest(long handle, int width, int height);
    public static native int nativeWidth(long handle);
    public static native int nativeHeight(long handle);
}
