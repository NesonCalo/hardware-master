package com.nesoncalo.hardwaremaster;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.view.View;

/** 容量占比条：满充容量 / 设计容量。 */
public class CapacityBarView extends View {

    private final Paint track = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint fill = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF rect = new RectF();
    private float ratio = 0;

    public CapacityBarView(Context c) {
        super(c);
        track.setColor(0xFF1A2940);
        fill.setColor(Ui.ACCENT);
    }

    public void setRatio(float r) {
        ratio = Math.max(0, Math.min(1, r));
        invalidate();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        float h = getHeight();
        float radius = h / 2f;
        rect.set(0, 0, getWidth(), h);
        canvas.drawRoundRect(rect, radius, radius, track);
        if (ratio <= 0) return;
        rect.set(0, 0, Math.max(h, getWidth() * ratio), h);
        fill.setColor(ratio >= 0.8 ? Ui.GREEN : (ratio >= 0.5 ? Ui.ORANGE : Ui.RED));
        canvas.drawRoundRect(rect, radius, radius, fill);
    }
}




