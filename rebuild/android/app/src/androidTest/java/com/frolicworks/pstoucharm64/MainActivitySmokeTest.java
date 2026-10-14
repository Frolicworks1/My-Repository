package com.frolicworks.pstoucharm64;

import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.test.core.app.ActivityScenario;
import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.Test;
import org.junit.runner.RunWith;

@RunWith(AndroidJUnit4.class)
public final class MainActivitySmokeTest {
    @Test
    public void activityLaunchesAndShowsCoreTools() {
        try (ActivityScenario<MainActivity> scenario = ActivityScenario.launch(MainActivity.class)) {
            scenario.onActivity(activity -> {
                View content = activity.findViewById(android.R.id.content);
                assertNotNull("Activity content root must exist", content);
                assertTrue("Content must contain a view hierarchy", content instanceof ViewGroup);
                assertTrue("Root must have children", ((ViewGroup) content).getChildCount() > 0);
                assertTrue("App title must be visible", containsText(content, "PS TOUCH"));
                assertTrue("Image import tool must be visible", containsText(content, "Import"));
                assertTrue("PNG export tool must be visible", containsText(content, "Save PNG"));
                assertTrue("Eraser tool must be visible", containsText(content, "Eraser"));
            });
        }
    }

    private static boolean containsText(View view, String expected) {
        if (view instanceof TextView) {
            CharSequence text = ((TextView) view).getText();
            if (text != null && text.toString().contains(expected)) return true;
        }
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int i = 0; i < group.getChildCount(); i++) {
                if (containsText(group.getChildAt(i), expected)) return true;
            }
        }
        return false;
    }
}
