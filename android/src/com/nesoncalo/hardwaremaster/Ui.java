package com.nesoncalo.hardwaremaster;

import android.content.Context;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;

/** 统一的暗色卡片式界面构件。 */
public final class Ui {

    public static final int BG = 0xFF070B14;
    public static final int CARD = 0xFF101A2B;
    public static final int CARD_SOFT = 0xFF0C1526;
    public static final int STROKE = 0xFF1E2C42;
    public static final int TEXT = 0xFFE6EEF8;
    public static final int SUB = 0xFF8FA3BF;
    public static final int FAINT = 0xFF5B6C85;
    public static final int ACCENT = 0xFF35D0FF;
    public static final int ORANGE = 0xFFFFA23A;
    public static final int GREEN = 0xFF48E0A0;
    public static final int RED = 0xFFFF5C7A;
    public static final int PURPLE = 0xFFB18CFF;

    private Ui() {}

    public static int dp(Context c, float v) {
        return (int) TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, v, c.getResources().getDisplayMetrics());
    }

    public static GradientDrawable round(int color, float radiusDp, Context c) {
        GradientDrawable d = new GradientDrawable();
        d.setColor(color);
        d.setCornerRadius(dp(c, radiusDp));
        return d;
    }

    public static GradientDrawable roundStroke(int color, float radiusDp, int strokeColor, Context c) {
        GradientDrawable d = round(color, radiusDp, c);
        d.setStroke(dp(c, 1), strokeColor);
        return d;
    }

    public static LinearLayout card(Context c) {
        LinearLayout l = new LinearLayout(c);
        l.setOrientation(LinearLayout.VERTICAL);
        l.setPadding(dp(c, 16), dp(c, 14), dp(c, 16), dp(c, 14));
        l.setBackground(roundStroke(CARD, 18, STROKE, c));
        return l;
    }

    public static LinearLayout row(Context c) {
        LinearLayout l = new LinearLayout(c);
        l.setOrientation(LinearLayout.HORIZONTAL);
        l.setGravity(Gravity.CENTER_VERTICAL);
        return l;
    }

    public static LinearLayout column(Context c) {
        LinearLayout l = new LinearLayout(c);
        l.setOrientation(LinearLayout.VERTICAL);
        return l;
    }

    public static TextView text(Context c, String s, float size, int color) {
        TextView t = new TextView(c);
        t.setText(s);
        t.setTextSize(size);
        t.setTextColor(color);
        t.setIncludeFontPadding(false);
        return t;
    }

    public static TextView boldText(Context c, String s, float size, int color) {
        TextView t = text(c, s, size, color);
        t.setTypeface(Typeface.create("sans-serif-medium", Typeface.NORMAL));
        return t;
    }

    public static TextView label(Context c, String s) {
        return text(c, s, 12, SUB);
    }

    public static TextView value(Context c, String s, int color) {
        return boldText(c, s, 19, color);
    }

    public static TextView sectionTitle(Context c, String s) {
        TextView t = boldText(c, s, 13, TEXT);
        t.setPadding(0, dp(c, 4), 0, dp(c, 8));
        return t;
    }

    public static View gap(Context c, float dp) {
        View v = new View(c);
        v.setLayoutParams(new LinearLayout.LayoutParams(1, dp(c, dp)));
        return v;
    }

    public static View hgap(Context c, float dp) {
        View v = new View(c);
        v.setLayoutParams(new LinearLayout.LayoutParams(dp(c, dp), 1));
        return v;
    }

    /** 四宫格指标：上方小标签，下方大数值 + 单位。 */
    public static LinearLayout tile(Context c, String label, String value, String unit, int accent) {
        LinearLayout box = new LinearLayout(c);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(c, 12), dp(c, 12), dp(c, 12), dp(c, 12));
        box.setBackground(roundStroke(CARD_SOFT, 14, STROKE, c));

        TextView dot = text(c, "▍", 11, accent);
        TextView l = text(c, label, 11, SUB);
        LinearLayout head = row(c);
        head.addView(dot);
        head.addView(l);
        box.addView(head);
        box.addView(gap(c, 6));

        LinearLayout val = row(c);
        TextView v = boldText(c, value, 22, accent);
        val.addView(v);
        if (unit != null && !unit.isEmpty()) {
            TextView u = text(c, unit, 12, SUB);
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
            lp.leftMargin = dp(c, 4);
            lp.bottomMargin = dp(c, 2);
            u.setLayoutParams(lp);
            val.addView(u);
        }
        box.addView(val);
        return box;
    }

    /** 数值 + 副标题的纵向小块，用于卡片内两列。 */
    public static LinearLayout kv(Context c, String label, String value, int color) {
        LinearLayout l = column(c);
        l.addView(text(c, label, 11, SUB));
        l.addView(gap(c, 3));
        l.addView(boldText(c, value, 15, color));
        return l;
    }

    public static TextView pill(Context c, String s, int color) {
        TextView t = text(c, s, 11, color);
        t.setPadding(dp(c, 10), dp(c, 5), dp(c, 10), dp(c, 5));
        GradientDrawable d = new GradientDrawable();
        d.setColor(Color.argb(28, Color.red(color), Color.green(color), Color.blue(color)));
        d.setCornerRadius(dp(c, 20));
        d.setStroke(dp(c, 1), Color.argb(90, Color.red(color), Color.green(color), Color.blue(color)));
        t.setBackground(d);
        return t;
    }

    public static View divider(Context c) {
        View v = new View(c);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(c, 1));
        lp.topMargin = dp(c, 10);
        lp.bottomMargin = dp(c, 10);
        v.setLayoutParams(lp);
        v.setBackgroundColor(0x1AFFFFFF);
        return v;
    }

    public static TextView button(Context c, String s, int color, boolean filled) {
        TextView t = boldText(c, s, 13, filled ? 0xFF06121F : color);
        t.setGravity(Gravity.CENTER);
        t.setPadding(dp(c, 14), dp(c, 10), dp(c, 14), dp(c, 10));
        GradientDrawable d = round(filled ? color : Color.argb(30, Color.red(color), Color.green(color), Color.blue(color)), 12, c);
        if (!filled) d.setStroke(dp(c, 1), Color.argb(110, Color.red(color), Color.green(color), Color.blue(color)));
        t.setBackground(d);
        return t;
    }

    public static LinearLayout.LayoutParams weight(float w) {
        return new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, w);
    }

    public static LinearLayout.LayoutParams matchWrap() {
        return new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
    }
}




