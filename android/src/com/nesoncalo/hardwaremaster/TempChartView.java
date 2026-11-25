package com.nesoncalo.hardwaremaster;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.view.View;

import java.util.ArrayDeque;
import java.util.Iterator;

/** 温度折线图：25–46℃，最多 90 个采样点。 */
public class TempChartView extends View {

    private final Paint grid = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint line = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint text = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint dot = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Path path = new Path();
    private final ArrayDeque<Float> data = new ArrayDeque<>();

    private static final float MIN = 25f;
    private static final float MAX = 46f;

    public TempChartView(Context c) {
        super(c);
        grid.setColor(0xFF1A2940);
        grid.setStrokeWidth(Ui.dp(c, 1));
        line.setColor(Ui.ORANGE);
        line.setStrokeWidth(Ui.dp(c, 2));
        text.setColor(Ui.FAINT);
        text.setTextSize(Ui.dp(c, 9));
        dot.setColor(Ui.ORANGE);
    }

    public void setData(ArrayDeque<Float> src) {
        data.clear();
        for (Iterator<Float> it = src.iterator(); it.hasNext(); ) data.addLast(it.next());
        invalidate();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        int w = getWidth();
        int h = getHeight();
        float right = w - Ui.dp(getContext(), 30);
        float top = Ui.dp(getContext(), 6);
        float bottom = h - Ui.dp(getContext(), 10);

        for (int v = 25; v <= 45; v += 5) {
            float y = bottom - (v - MIN) / (MAX - MIN) * (bottom - top);
            canvas.drawLine(0, y, right, y, grid);
            canvas.drawText(String.valueOf(v), right + Ui.dp(getContext(), 6), y + Ui.dp(getContext(), 3), text);
        }

        if (data.size() < 2) return;
        path.reset();
        float step = right / 89f;
        int i = 0;
        int offset = 90 - data.size();
        for (Float f : data) {
            float v = Math.max(MIN, Math.min(MAX, f));
            float x = (offset + i) * step;
            float y = bottom - (v - MIN) / (MAX - MIN) * (bottom - top);
            if (i == 0) path.moveTo(x, y); else path.lineTo(x, y);
            i++;
        }
        canvas.drawPath(path, line);

        Float last = data.peekLast();
        if (last != null) {
            float v = Math.max(MIN, Math.min(MAX, last));
            float x = (offset + i - 1) * step;
            float y = bottom - (v - MIN) / (MAX - MIN) * (bottom - top);
            dot.setColor(v >= 43 ? Ui.RED : (v >= 40 ? Ui.ORANGE : Ui.GREEN));
            canvas.drawCircle(x, y, Ui.dp(getContext(), 3), dot);
        }
    }
}




