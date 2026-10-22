package com.frolicworks.pstoucharm64;

import android.graphics.Bitmap;

import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.Test;
import org.junit.runner.RunWith;

import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class TTPixelImageCoreTest {
    private static Bitmap fixture() {
        return TTPixelImageCore.fromArgbPixels(3, 2, new int[] {
                0x00000000, 0xffff0000, 0xff00ff00,
                0xff0000ff, 0x80445566, 0xffffffff
        });
    }

    @Test public void pngRoundTripPreservesEveryArgbPixel() {
        Bitmap original = fixture();
        Bitmap decoded = TTPixelImageCore.pngRoundTrip(original);
        assertEquals(original.getWidth(), decoded.getWidth());
        assertEquals(original.getHeight(), decoded.getHeight());
        assertArrayEquals(TTPixelImageCore.readArgbPixels(original), TTPixelImageCore.readArgbPixels(decoded));
    }

    @Test public void pixelArrayRoundTripIsExact() {
        int[] expected = {0x00000000, 0xffff0000, 0xff00ff00, 0xff0000ff, 0x80445566, 0xffffffff};
        Bitmap bitmap = TTPixelImageCore.fromArgbPixels(3, 2, expected);
        assertArrayEquals(expected, TTPixelImageCore.readArgbPixels(bitmap));
    }

    @Test public void copyDoesNotShareMutablePixelStorage() {
        Bitmap source = fixture();
        Bitmap copy = TTPixelImageCore.copy(source);
        copy.setPixel(0, 0, 0xffffffff);
        assertEquals(0x00000000, source.getPixel(0, 0));
        assertEquals(0xffffffff, copy.getPixel(0, 0));
    }

    @Test public void resampleProducesRequestedDimensions() {
        Bitmap resized = TTPixelImageCore.resample(fixture(), 7, 5, false);
        assertEquals(7, resized.getWidth());
        assertEquals(5, resized.getHeight());
    }

    @Test public void malformedBytesAreRejected() {
        try {
            TTPixelImageCore.decode(new byte[] {1, 2, 3, 4});
            fail("Expected malformed image rejection");
        } catch (IllegalArgumentException expected) {
            assertTrue(expected.getMessage().contains("Unsupported")
                    || expected.getMessage().contains("dimensions"));
        }
    }

    @Test public void emptyImageBytesAreRejectedBeforeDecode() {
        try {
            TTPixelImageCore.decode(new byte[0]);
            fail("Expected empty input rejection");
        } catch (IllegalArgumentException expected) {
            assertTrue(expected.getMessage().contains("empty"));
        }
    }

    @Test public void oversizedDimensionsAreRejectedBeforeAllocation() {
        try {
            TTPixelImageCore.fromArgbPixels(16_385, 1, new int[0]);
            fail("Expected dimension safety rejection");
        } catch (IllegalArgumentException expected) {
            assertTrue(expected.getMessage().contains("safety limit"));
        }
    }

    @Test public void invalidTargetDimensionsAreRejected() {
        try {
            TTPixelImageCore.resample(fixture(), 0, 2, true);
            fail("Expected invalid dimension rejection");
        } catch (IllegalArgumentException expected) {
            assertTrue(expected.getMessage().contains("positive"));
        }
    }
}
