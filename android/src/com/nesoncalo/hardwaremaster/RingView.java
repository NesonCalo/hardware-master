package com.nesoncalo.hardwaremaster;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.view.View;

/** 电量环：中央大号百分比 + 状态 + 功率。 */
public class RingView extends View {

    private final Paint track = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint arc = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint big = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint small = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF oval = new RectF();

    private int level;
    private boolean charging;
    private String status = "";
    private String sub = "";

    public RingView(Context c) {
        super(c);
        track.setStyle(Paint.Style.STROKE);
        track.setStrokeWidth(Ui.dp(c, 14));
        track.setColor(0xFF1A2940);
        arc.setStyle(Paint.Style.STROKE);
        arc.setStrokeWidth(Ui.dp(c, 14));
        arc.setStrokeCap(Paint.Cap.ROUND);
        big.setColor(Ui.TEXT);
        big.setTextAlign(Paint.Align.CENTER);
        big.setTypeface(Typeface.create("sans-serif-medium", Typeface.NORMAL));
        big.setTextSize(Ui.dp(c, 36));
        small.setColor(Ui.SUB);
        small.setTextAlign(Paint.Align.CENTER);
        small.setTextSize(Ui.dp(c, 12));
    }

    public void setData(int level, boolean charging, String status, String sub) {
        this.level = Math.max(0, Math.min(100, level));
        this.charging = charging;
        this.status = status == null ? "" : status;
        this.sub = sub == null ? "" : sub;
        invalidate();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        float pad = Ui.dp(getContext(), 8) + arc.getStrokeWidth() / 2f;
        float cx = getWidth() / 2f;
        float cy = getHeight() / 2f;
        float r = Math.min(getWidth(), getHeight()) / 2f - pad;
        oval.set(cx - r, cy - r, cx + r, cy + r);
        canvas.drawArc(oval, -90, 360, false, track);
        arc.setColor(charging ? Ui.GREEN : Ui.ORANGE);
        canvas.drawArc(oval, -90, 360f * level / 100f, false, arc);

        canvas.drawText(level + "%", cx, cy - Ui.dp(getContext(), 2), big);
        small.setColor(Ui.SUB);
        canvas.drawText(status, cx, cy + Ui.dp(getContext(), 26), small);
        if (sub != null && !sub.isEmpty()) {
            small.setColor(charging ? Ui.GREEN : Ui.ACCENT);
            canvas.drawText(sub, cx, cy + Ui.dp(getContext(), 47), small);
        }
    }
}




