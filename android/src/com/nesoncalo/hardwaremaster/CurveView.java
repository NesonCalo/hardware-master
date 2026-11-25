package com.nesoncalo.hardwaremaster;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.view.View;

import java.util.ArrayList;
import java.util.List;

/** 双线曲线：电量（左轴 0-100%）与功率（右轴 0-maxW）。 */
public class CurveView extends View {

    private final List<Float> levels = new ArrayList<>();
    private final List<Float> powers = new ArrayList<>();
    private double maxPower = 60;

    private final Paint grid = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint text = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint lineLevel = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint linePower = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Paint fillPower = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Path path = new Path();

    public CurveView(Context c) {
        super(c);
        grid.setColor(0x1FFFFFFF);
        grid.setStrokeWidth(Ui.dp(c, 1));
        text.setColor(Ui.FAINT);
        text.setTextSize(Ui.dp(c, 9));
        lineLevel.setColor(Ui.ORANGE);
        lineLevel.setStrokeWidth(Ui.dp(c, 2));
        lineLevel.setStyle(Paint.Style.STROKE);
        linePower.setColor(Ui.ACCENT);
        linePower.setStrokeWidth(Ui.dp(c, 2));
        linePower.setStyle(Paint.Style.STROKE);
        fillPower.setColor(0x2235D0FF);
        fillPower.setStyle(Paint.Style.FILL);
    }

    public void push(double level, double powerW) {
        levels.add((float) level);
        powers.add((float) Math.max(0, powerW));
        maxPower = 20;
        for (float p : powers) if (p > maxPower) maxPower = p;
        maxPower = Math.ceil(maxPower / 10.0) * 10.0;
        while (levels.size() > 90) {
            levels.remove(0);
            powers.remove(0);
        }
        invalidate();
    }

    public void reset() {
        levels.clear();
        powers.clear();
        invalidate();
    }

    public int size() {
        return levels.size();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        float left = Ui.dp(getContext(), 6);
        float right = getWidth() - Ui.dp(getContext(), 34);
        float top = Ui.dp(getContext(), 8);
        float bottom = getHeight() - Ui.dp(getContext(), 18);
        if (right <= left || bottom <= top) return;

        for (int i = 0; i <= 4; i++) {
            float y = top + (bottom - top) * i / 4f;
            canvas.drawLine(left, y, right, y, grid);
            canvas.drawText(String.valueOf(100 - i * 25), right + Ui.dp(getContext(), 6), y + Ui.dp(getContext(), 3), text);
        }

        if (levels.size() < 2) {
            text.setColor(Ui.FAINT);
            text.setTextSize(Ui.dp(getContext(), 11));
            canvas.drawText(L.t("采样中…", "Sampling…"), left + Ui.dp(getContext(), 4), top + Ui.dp(getContext(), 26), text);
            text.setTextSize(Ui.dp(getContext(), 9));
            return;
        }

        int n = levels.size();
        float dx = (right - left) / (n - 1);

        path.reset();
        for (int i = 0; i < n; i++) {
            float x = left + dx * i;
            float y = bottom - (bottom - top) * Math.min(100, levels.get(i)) / 100f;
            if (i == 0) path.moveTo(x, y);
            else path.lineTo(x, y);
        }
        canvas.drawPath(path, lineLevel);

        path.reset();
        float maxP = (float) Math.max(10, maxPower);
        for (int i = 0; i < n; i++) {
            float x = left + dx * i;
            float y = bottom - (bottom - top) * Math.min(maxP, powers.get(i)) / maxP;
            if (i == 0) path.moveTo(x, y);
            else path.lineTo(x, y);
        }
        canvas.drawPath(path, linePower);

        text.setColor(Ui.ORANGE);
        text.setTextSize(Ui.dp(getContext(), 9));
        canvas.drawText("● " + L.t("电量", "Level"), left, getHeight() - Ui.dp(getContext(), 4), text);
        text.setColor(Ui.ACCENT);
        String legend = "● " + L.t("功率", "Power") + String.format(java.util.Locale.US, " 0–%.0fW", Math.max(10, maxPower));
        canvas.drawText(legend, left + Ui.dp(getContext(), 52), getHeight() - Ui.dp(getContext(), 4), text);
    }
}




