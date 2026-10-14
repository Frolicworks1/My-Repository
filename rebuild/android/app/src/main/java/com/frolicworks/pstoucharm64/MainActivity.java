package com.frolicworks.pstoucharm64;

import android.app.Activity;
import android.content.ContentValues;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.MediaStore;
import android.view.Gravity;
import java.io.InputStream;
import android.view.MotionEvent;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import java.io.OutputStream;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.Locale;

public final class MainActivity extends Activity {
    private DrawingView drawingView;
    private TextView status;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.rgb(22, 25, 34));
        getWindow().setNavigationBarColor(Color.rgb(22, 25, 34));
        getWindow().getDecorView().setSystemUiVisibility(0);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(238, 240, 245));

        TextView title = new TextView(this);
        title.setText("PS TOUCH  •  ARM64 ENGINE PROTOTYPE");
        title.setTextColor(Color.WHITE);
        title.setTextSize(14);
        title.setGravity(Gravity.CENTER_VERTICAL);
        title.setPadding(dp(16), 0, dp(8), 0);
        title.setBackgroundColor(Color.rgb(22, 25, 34));
        root.addView(title, new LinearLayout.LayoutParams(-1, dp(48)));

        LinearLayout toolbar = new LinearLayout(this);
        toolbar.setOrientation(LinearLayout.HORIZONTAL);
        toolbar.setGravity(Gravity.CENTER_VERTICAL);
        toolbar.setPadding(dp(6), dp(4), dp(6), dp(4));
        toolbar.setBackgroundColor(Color.rgb(35, 39, 51));
        root.addView(toolbar, new LinearLayout.LayoutParams(-1, dp(52)));

        drawingView = new DrawingView();
        addTool(toolbar, "Import", () -> importImage());
        addTool(toolbar, "Brush", () -> drawingView.setEraser(false));
        addTool(toolbar, "Color", () -> drawingView.nextColor());
        addTool(toolbar, "Eraser", () -> drawingView.setEraser(true));
        addTool(toolbar, "Undo", () -> drawingView.undo());
        addTool(toolbar, "Clear", () -> drawingView.clear());
        addTool(toolbar, "Save PNG", () -> saveArtwork());

        status = new TextView(this);
        status.setText("ARM64 native canvas ready • Draw with your finger");
        status.setTextColor(Color.rgb(48, 54, 68));
        status.setTextSize(12);
        status.setPadding(dp(12), 0, dp(8), 0);
        status.setGravity(Gravity.CENTER_VERTICAL);
        root.addView(status, new LinearLayout.LayoutParams(-1, dp(32)));

        LinearLayout.LayoutParams canvasParams = new LinearLayout.LayoutParams(-1, 0, 1);
        canvasParams.setMargins(dp(8), dp(4), dp(8), dp(8));
        drawingView.setBackgroundColor(Color.WHITE);
        root.addView(drawingView, canvasParams);
        setContentView(root);
    }

    private void addTool(LinearLayout toolbar, String label, Runnable action) {
        Button button = new Button(this);
        button.setText(label);
        button.setTextSize(11);
        button.setAllCaps(false);
        button.setPadding(dp(2), 0, dp(2), 0);
        button.setMinWidth(0);
        button.setMinimumWidth(0);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(0, -1, 1);
        params.setMargins(dp(2), 0, dp(2), 0);
        toolbar.addView(button, params);
        button.setOnClickListener(v -> action.run());
    }

    private int dp(float value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }

    private static final int REQUEST_IMPORT_IMAGE = 7104;

    private void importImage() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("image/*");
        try {
            startActivityForResult(intent, REQUEST_IMPORT_IMAGE);
        } catch (Exception error) {
            toast("Image picker unavailable: " + error.getMessage());
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != REQUEST_IMPORT_IMAGE || resultCode != RESULT_OK || data == null || data.getData() == null) return;
        Uri uri = data.getData();
        try (InputStream stream = getContentResolver().openInputStream(uri)) {
            if (stream == null) throw new IllegalStateException("Could not open selected image");
            Bitmap bitmap = BitmapFactory.decodeStream(stream);
            if (bitmap == null) throw new IllegalArgumentException("Unsupported or unreadable image");
            drawingView.setImage(bitmap);
            status.setText("Image imported • draw over it or export PNG");
        } catch (Exception error) {
            toast("Import failed: " + error.getMessage());
        }
    }

    private void saveArtwork() {
        if (drawingView.getWidth() < 1 || drawingView.getHeight() < 1) {
            toast("Canvas is not ready yet");
            return;
        }
        Bitmap bitmap = Bitmap.createBitmap(drawingView.getWidth(), drawingView.getHeight(), Bitmap.Config.ARGB_8888);
        Canvas output = new Canvas(bitmap);
        output.drawColor(Color.WHITE);
        drawingView.drawArtwork(output);
        String stamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(new Date());
        ContentValues values = new ContentValues();
        values.put(MediaStore.Images.Media.DISPLAY_NAME, "PSTouchPrototype_" + stamp + ".png");
        values.put(MediaStore.Images.Media.MIME_TYPE, "image/png");
        if (Build.VERSION.SDK_INT >= 29) {
            values.put(MediaStore.Images.Media.RELATIVE_PATH, "Pictures/PS Touch Prototype");
            values.put(MediaStore.Images.Media.IS_PENDING, 1);
        }
        Uri uri = getContentResolver().insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values);
        if (uri == null) {
            bitmap.recycle();
            toast("Save failed: Android did not create an image entry");
            return;
        }
        try (OutputStream stream = getContentResolver().openOutputStream(uri)) {
            if (stream == null || !bitmap.compress(Bitmap.CompressFormat.PNG, 100, stream)) {
                throw new IllegalStateException("PNG encoder failed");
            }
            if (Build.VERSION.SDK_INT >= 29) {
                ContentValues done = new ContentValues();
                done.put(MediaStore.Images.Media.IS_PENDING, 0);
                getContentResolver().update(uri, done, null, null);
            }
            toast("Saved to Pictures/PS Touch Prototype");
        } catch (Exception error) {
            getContentResolver().delete(uri, null, null);
            toast("Save failed: " + error.getMessage());
        } finally {
            bitmap.recycle();
        }
    }

    private void toast(String message) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
        if (status != null) status.setText(message);
    }

    private final class DrawingView extends View {
        private static final int INK = Color.rgb(28, 35, 52);
        private final ArrayList<Stroke> strokes = new ArrayList<>();
        private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.DITHER_FLAG);
        private Stroke current;
        private boolean eraser = false;
        private int colorIndex = 0;
        private final int[] palette = new int[] { INK, Color.BLACK, Color.rgb(190, 42, 52), Color.rgb(36, 93, 180), Color.rgb(20, 135, 94) };
        private Bitmap backgroundImage;
        private float brushSize;

        DrawingView() {
            super(MainActivity.this);
            brushSize = dp(5);
            setLayerType(View.LAYER_TYPE_SOFTWARE, null);
        }

        void setImage(Bitmap bitmap) {
            if (backgroundImage != null && !backgroundImage.isRecycled()) backgroundImage.recycle();
            backgroundImage = bitmap;
            strokes.clear();
            current = null;
            invalidate();
        }

        void nextColor() {
            colorIndex = (colorIndex + 1) % palette.length;
            status.setText("Brush color changed");
        }

        void setEraser(boolean enabled) {
            eraser = enabled;
            status.setText(enabled ? "Eraser selected" : "Brush selected");
        }

        void undo() {
            if (!strokes.isEmpty()) {
                strokes.remove(strokes.size() - 1);
                invalidate();
                status.setText("Undo • " + strokes.size() + " strokes");
            }
        }

        void clear() {
            strokes.clear();
            current = null;
            invalidate();
            status.setText("Canvas cleared");
        }

        @Override
        protected void onDraw(Canvas canvas) {
            super.onDraw(canvas);
            canvas.drawColor(Color.WHITE);
            drawArtwork(canvas);
        }

        void drawArtwork(Canvas canvas) {
            if (backgroundImage != null) {
                float scale = Math.min((float) getWidth() / backgroundImage.getWidth(),
                                       (float) getHeight() / backgroundImage.getHeight());
                float width = backgroundImage.getWidth() * scale;
                float height = backgroundImage.getHeight() * scale;
                float left = (getWidth() - width) / 2f;
                float top = (getHeight() - height) / 2f;
                Paint imagePaint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
                canvas.drawBitmap(backgroundImage, null,
                        new android.graphics.RectF(left, top, left + width, top + height), imagePaint);
            }
            for (Stroke stroke : strokes) drawStroke(canvas, stroke);
            if (current != null) drawStroke(canvas, current);
        }

        private void drawStroke(Canvas canvas, Stroke stroke) {
            paint.setColor(stroke.color);
            paint.setStrokeWidth(stroke.width);
            paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeCap(Paint.Cap.ROUND);
            paint.setStrokeJoin(Paint.Join.ROUND);
            canvas.drawPath(stroke.path, paint);
        }

        @Override
        public boolean onTouchEvent(MotionEvent event) {
            float x = event.getX();
            float y = event.getY();
            switch (event.getActionMasked()) {
                case MotionEvent.ACTION_DOWN:
                    current = new Stroke(eraser ? Color.WHITE : palette[colorIndex], eraser ? brushSize * 4 : brushSize);
                    current.path.moveTo(x, y);
                    strokes.add(current);
                    invalidate();
                    return true;
                case MotionEvent.ACTION_MOVE:
                    if (current != null) {
                        for (int i = 0; i < event.getHistorySize(); i++) {
                            current.path.lineTo(event.getHistoricalX(i), event.getHistoricalY(i));
                        }
                        current.path.lineTo(x, y);
                        invalidate();
                    }
                    return true;
                case MotionEvent.ACTION_UP:
                case MotionEvent.ACTION_CANCEL:
                    if (current != null) {
                        current.path.lineTo(x, y);
                        current = null;
                        invalidate();
                        status.setText("Drawing • " + strokes.size() + " strokes");
                    }
                    performClick();
                    return true;
                default:
                    return true;
            }
        }

        @Override
        public boolean performClick() {
            super.performClick();
            return true;
        }
    }

    private static final class Stroke {
        final Path path = new Path();
        final int color;
        final float width;
        Stroke(int color, float width) {
            this.color = color;
            this.width = width;
        }
    }
}
