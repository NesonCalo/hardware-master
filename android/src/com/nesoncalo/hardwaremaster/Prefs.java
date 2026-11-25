package com.nesoncalo.hardwaremaster;

import android.content.Context;
import android.content.SharedPreferences;

/** 设置与会话记录的轻量存储，全部留在本机。 */
public final class Prefs {

    private static final String NAME = "hardwaremaster";
    private static SharedPreferences sp(Context ctx) {
        return ctx.getSharedPreferences(NAME, Context.MODE_PRIVATE);
    }

    private Prefs() {}

    public static String getLang(Context ctx) {
        return sp(ctx).getString("lang", "auto");
    }

    public static void setLang(Context ctx, String v) {
        sp(ctx).edit().putString("lang", v).apply();
    }

    public static int getDesignMah(Context ctx) {
        return sp(ctx).getInt("design_mah", 0);
    }

    public static void setDesignMah(Context ctx, int v) {
        sp(ctx).edit().putInt("design_mah", v).apply();
    }

    public static boolean bgMonitor(Context ctx) {
        return sp(ctx).getBoolean("bg_monitor", false);
    }

    public static void setBgMonitor(Context ctx, boolean v) {
        sp(ctx).edit().putBoolean("bg_monitor", v).apply();
    }

    public static boolean alert80(Context ctx) {
        return sp(ctx).getBoolean("alert80", true);
    }

    public static void setAlert80(Context ctx, boolean v) {
        sp(ctx).edit().putBoolean("alert80", v).apply();
    }

    public static boolean alertTemp(Context ctx) {
        return sp(ctx).getBoolean("alertTemp", true);
    }

    public static void setAlertTemp(Context ctx, boolean v) {
        sp(ctx).edit().putBoolean("alertTemp", v).apply();
    }

    public static boolean alertSlow(Context ctx) {
        return sp(ctx).getBoolean("alertSlow", false);
    }

    public static void setAlertSlow(Context ctx, boolean v) {
        sp(ctx).edit().putBoolean("alertSlow", v).apply();
    }

    public static int tempLimit(Context ctx) {
        return sp(ctx).getInt("tempLimit", 43);
    }

    public static void setTempLimit(Context ctx, int v) {
        sp(ctx).edit().putInt("tempLimit", v).apply();
    }

    public static String sessions(Context ctx) {
        return sp(ctx).getString("sessions", "[]");
    }

    public static void setSessions(Context ctx, String json) {
        sp(ctx).edit().putString("sessions", json).apply();
    }
}




