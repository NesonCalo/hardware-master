package com.nesoncalo.hardwaremaster;

import android.content.Context;

import org.json.JSONArray;
import org.json.JSONObject;

/** 充电会话记录：采样时累计电量，拔线时落一条记录，最多保留 60 条。 */
public final class SessionStore {

    public static boolean active;
    public static long startMs;
    public static int startLevel;
    public static double wh;
    public static double peakW;
    public static long lastMs;
    public static int endLevel;

    private SessionStore() {}

    public static void tick(Context ctx, BatteryReader b) {
        long now = System.currentTimeMillis();
        if (b.charging) {
            if (!active) {
                active = true;
                startMs = now;
                startLevel = b.level;
                endLevel = b.level;
                wh = 0;
                peakW = 0;
                lastMs = now;
                return;
            }
            double dtSec = (now - lastMs) / 1000.0;
            if (dtSec > 0 && dtSec < 180) {
                double p = Math.max(0, b.powerW);
                wh += p * dtSec / 3600.0;
                peakW = Math.max(peakW, p);
            }
            endLevel = b.level;
            lastMs = now;
        } else if (active) {
            finish(ctx, b);
        }
    }

    private static void finish(Context ctx, BatteryReader b) {
        long dur = System.currentTimeMillis() - startMs;
        if (dur >= 60000 && wh > 0.005) {
            try {
                JSONArray arr = new JSONArray(Prefs.sessions(ctx));
                JSONObject o = new JSONObject();
                o.put("start", startMs);
                o.put("end", System.currentTimeMillis());
                o.put("startLevel", startLevel);
                o.put("endLevel", b.level);
                o.put("wh", Math.round(wh * 1000.0) / 1000.0);
                o.put("peakW", Math.round(peakW * 10.0) / 10.0);
                arr.put(o);
                while (arr.length() > 60) arr.remove(0);
                Prefs.setSessions(ctx, arr.toString());
            } catch (Throwable ignored) {}
        }
        active = false;
        wh = 0;
        peakW = 0;
        startMs = 0;
        lastMs = 0;
    }

    public static double avgW() {
        if (!active || startMs <= 0) return 0;
        long dur = System.currentTimeMillis() - startMs;
        if (dur < 1000) return 0;
        return wh / (dur / 3600000.0);
    }

    public static int minutes() {
        if (!active) return 0;
        return (int) ((System.currentTimeMillis() - startMs) / 60000);
    }
}




