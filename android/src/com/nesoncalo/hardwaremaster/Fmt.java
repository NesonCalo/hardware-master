package com.nesoncalo.hardwaremaster;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/** 显示格式化。 */
public final class Fmt {

    private Fmt() {}

    public static String pct(double v) {
        if (v <= 0) return "—";
        return String.format(Locale.US, "%.1f%%", v);
    }

    public static String watts(double v) {
        if (Double.isNaN(v) || Double.isInfinite(v)) return "—";
        double a = Math.abs(v);
        if (a >= 10) return String.format(Locale.US, "%.0f W", a);
        return String.format(Locale.US, "%.1f W", a);
    }

    public static String signedWatts(double v) {
        if (v == 0) return "—";
        String s = v > 0 ? "+" : "−";
        return s + watts(v);
    }

    public static String mahNum(double v) {
        if (v <= 0) return L.t("未知", "Unknown");
        return String.format(Locale.US, "%.0f", v);
    }

    public static String mah(double v) {
        if (v <= 0) return L.t("未知", "Unknown");
        return String.format(Locale.US, "%.0f mAh", v);
    }

    public static String ma(double v) {
        if (v <= 0) return "—";
        return String.format(Locale.US, "%.0f mA", v);
    }

    public static String volt(double v) {
        if (v <= 0) return "—";
        return String.format(Locale.US, "%.2f V", v);
    }

    public static String temp(double v) {
        if (v <= 0) return "—";
        return String.format(Locale.US, "%.1f ℃", v);
    }

    public static String speed(double v) {
        if (v <= 0) return "—";
        return String.format(Locale.US, "%.1f%%/h", v);
    }

    public static String minutes(int m) {
        if (m < 0) return "—";
        if (m < 60) return m + " " + L.t("分钟", "min");
        int h = m / 60;
        int mm = m % 60;
        return h + " " + L.t("小时", "h") + " " + mm + " " + L.t("分", "m");
    }

    public static String duration(long ms) {
        if (ms <= 0) return "—";
        long m = ms / 60000;
        if (m < 60) return m + " " + L.t("分钟", "min");
        return (m / 60) + " " + L.t("小时", "h") + " " + (m % 60) + " " + L.t("分", "m");
    }

    public static String clock(long ms) {
        return new SimpleDateFormat("HH:mm", Locale.US).format(new Date(ms));
    }

    public static String dayClock(long ms) {
        return new SimpleDateFormat("MM-dd HH:mm", Locale.US).format(new Date(ms));
    }

    public static String wh(double v) {
        if (v <= 0) return "0 Wh";
        if (v < 1) return String.format(Locale.US, "%.0f mWh", v * 1000);
        return String.format(Locale.US, "%.2f Wh", v);
    }

    public static String gb(long bytes) {
        return String.format(Locale.US, "%.1f GB", bytes / 1073741824.0);
    }

    public static String cycles(int c) {
        return c < 0 ? L.t("未知", "Unknown") : (c + " " + L.t("次", ""));
    }
}





