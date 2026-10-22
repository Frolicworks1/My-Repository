package com.frolicworks.pstoucharm64;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Rect;
import android.graphics.RectF;

import java.io.ByteArrayOutputStream;

/**
 * Clean-room image primitives for compatibility experiments.
 *
 * This class is NOT an ANE implementation and does not claim to match the
 * proprietary TTPixel ABI. Exact ActionScript/native signatures must be
 * established from runtime traces before this core can be wired to the SWF.
 */
public final class TTPixelImageCore {
    private static final int MAX_DIMENSION = 16_384;
    private static final long MAX_PIXELS = 64L * 1024L * 1024L;

    private TTPixelImageCore() {}

    public static Bitmap copy(Bitmap source) {
        requireBitmap(source);
        Bitmap.Config config = source.getConfig() == null ? Bitmap.Config.ARGB_8888 : source.getConfig();
        Bitmap out = source.copy(config, true);
        if (out == null) throw new IllegalArgumentException("Bitmap copy failed");
        return out;
    }

    /** Encodes a bitmap as lossless PNG bytes. Caller owns returned array. */
    public static byte[] encodePng(Bitmap source) {
        requireBitmap(source);
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        if (!source.compress(Bitmap.CompressFormat.PNG, 100, out)) {
            throw new IllegalStateException("PNG encoder failed");
        }
        return out.toByteArray();
    }

    /**
     * Decodes supported image bytes after checking encoded dimensions first.
     * This avoids allocating a huge bitmap from a small, highly-compressed input.
     */
    public static Bitmap decode(byte[] bytes) {
        if (bytes == null || bytes.length == 0) {
            throw new IllegalArgumentException("Image bytes are empty");
        }

        BitmapFactory.Options bounds = new BitmapFactory.Options();
        bounds.inJustDecodeBounds = true;
        BitmapFactory.decodeByteArray(bytes, 0, bytes.length, bounds);
        validateDimensions(bounds.outWidth, bounds.outHeight);

        Bitmap bitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.length);
        if (bitmap == null) {
            throw new IllegalArgumentException("Unsupported or malformed image data");
        }
        // Re-check the decoded object rather than relying solely on decoder metadata.
        try {
            validateDimensions(bitmap.getWidth(), bitmap.getHeight());
            return bitmap;
        } catch (RuntimeException ex) {
            bitmap.recycle();
            throw ex;
        }
    }

    /** Lossless PNG round trip; pixel values should remain identical for ARGB_8888 fixtures. */
    public static Bitmap pngRoundTrip(Bitmap source) {
        return decode(encodePng(source));
    }

    public static Bitmap resample(Bitmap source, int width, int height, boolean filtered) {
        requireBitmap(source);
        validateDimensions(width, height);
        Bitmap out = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
        Canvas canvas = new Canvas(out);
        Paint paint = new Paint();
        paint.setFilterBitmap(filtered);
        paint.setAntiAlias(filtered);
        canvas.drawBitmap(source, new Rect(0, 0, source.getWidth(), source.getHeight()),
                new RectF(0, 0, width, height), paint);
        return out;
    }

    public static int[] readArgbPixels(Bitmap source) {
        requireBitmap(source);
        int width = source.getWidth(), height = source.getHeight();
        int[] pixels = new int[Math.multiplyExact(width, height)];
        source.getPixels(pixels, 0, width, 0, 0, width, height);
        return pixels;
    }

    public static Bitmap fromArgbPixels(int width, int height, int[] pixels) {
        validateDimensions(width, height);
        if (pixels == null || pixels.length != (long) width * height) {
            throw new IllegalArgumentException("Pixel count mismatch");
        }
        Bitmap out = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
        out.setPixels(pixels, 0, width, 0, 0, width, height);
        return out;
    }

    private static void validateDimensions(int width, int height) {
        if (width <= 0 || height <= 0) {
            throw new IllegalArgumentException("Image dimensions must be positive");
        }
        if (width > MAX_DIMENSION || height > MAX_DIMENSION
                || (long) width * height > MAX_PIXELS) {
            throw new IllegalArgumentException("Image exceeds safety limit");
        }
    }

    private static void requireBitmap(Bitmap bitmap) {
        if (bitmap == null || bitmap.isRecycled()) {
            throw new IllegalArgumentException("Bitmap is null or recycled");
        }
    }
}
