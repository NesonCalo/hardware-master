package com.nesoncalo.hardwaremaster;

import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.BatteryManager;
import android.os.Build;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.util.Locale;

/**
 * 电池 / 充电数据采集。
 * 优先用 BatteryManager 与 ACTION_BATTERY_CHANGED，容量类数据回退到 sysfs。
 * 所有读取都做了权限与异常兜底，读不到时返回 0 / -1，由界面显示“未知”。
 */
public class BatteryReader {

    public int level;               // 0-100
    public int status;              // BatteryManager.BATTERY_STATUS_*
    public int plugged;             // BATTERY_PLUGGED_*
    public int health;              // BATTERY_HEALTH_*
    public int temperatureTenths;   // 0.1 ℃
    public int voltageMv;
    public String technology = "";

    public long chargeCounterUah;   // 剩余电荷 µAh
    public long currentNowUa;       // 瞬时电流 µA（负数放电）
    public long energyCounterNh;

    public double fullCapacityMah;  // 满充容量 mAh，0=未知
    public double designCapacityMah;// 设计容量 mAh，0=未知
    public int cycleCount = -1;     // 循环次数，-1=未知

    public double currentMa;        // 绝对值
    public double voltageV;
    public double powerW;
    public double tempC;
    public double speedPctPerHour;  // 充电速度 %/h
    public int minutesToFull = -1;  // 充满剩余分钟

    public boolean charging;
    public boolean full;
    public boolean pluggedIn;

    public String capacitySource = "";
    public String currentSource = "";
    public String designSource = "";

    private String sysChargeFullPath;
    private String sysChargeFullDesignPath;
    private String sysCyclePath;
    private String sysCurrentPath;
    private String sysVoltagePath;
    private String sysTempPath;
    private boolean sysProbed;

    public String statusText() {
        if (status == BatteryManager.BATTERY_STATUS_CHARGING) return L.t("充电中", "Charging");
        if (status == BatteryManager.BATTERY_STATUS_FULL) return L.t("已充满", "Full");
        if (status == BatteryManager.BATTERY_STATUS_DISCHARGING) return L.t("放电中", "Discharging");
        if (status == BatteryManager.BATTERY_STATUS_NOT_CHARGING) return L.t("未充电", "Not charging");
        return L.t("未知", "Unknown");
    }

    public String healthText() {
        switch (health) {
            case BatteryManager.BATTERY_HEALTH_GOOD: return L.t("良好", "Good");
            case BatteryManager.BATTERY_HEALTH_OVERHEAT: return L.t("过热", "Overheat");
            case BatteryManager.BATTERY_HEALTH_DEAD: return L.t("损坏", "Dead");
            case BatteryManager.BATTERY_HEALTH_OVER_VOLTAGE: return L.t("电压过高", "Over voltage");
            case BatteryManager.BATTERY_HEALTH_COLD: return L.t("温度过低", "Cold");
            case BatteryManager.BATTERY_HEALTH_UNSPECIFIED_FAILURE: return L.t("异常", "Failure");
            default: return L.t("未知", "Unknown");
        }
    }

    public String plugText() {
        if ((plugged & BatteryManager.BATTERY_PLUGGED_AC) != 0) return L.t("有线充电", "AC");
        if ((plugged & BatteryManager.BATTERY_PLUGGED_USB) != 0) return L.t("USB 充电", "USB");
        if ((plugged & BatteryManager.BATTERY_PLUGGED_WIRELESS) != 0) return L.t("无线充电", "Wireless");
        if ((plugged & 0x20) != 0) return L.t(" dock 充电", "Dock");
        return plugged == 0 ? L.t("未连接", "Unplugged") : L.t("外部供电", "External");
    }

    public double wearPercent() {
        if (fullCapacityMah <= 0 || designCapacityMah <= 0) return -1;
        double w = (1.0 - fullCapacityMah / designCapacityMah) * 100.0;
        if (w < 0) w = 0;
        if (w > 100) w = 100;
        return w;
    }

    public void read(Context ctx) {
        Intent it = ctx.registerReceiver(null, new IntentFilter(Intent.ACTION_BATTERY_CHANGED));
        if (it != null) {
            int l = it.getIntExtra(BatteryManager.EXTRA_LEVEL, 0);
            int s = it.getIntExtra(BatteryManager.EXTRA_SCALE, 100);
            level = s > 0 ? Math.round(l * 100f / s) : l;
            status = it.getIntExtra(BatteryManager.EXTRA_STATUS, BatteryManager.BATTERY_STATUS_UNKNOWN);
            plugged = it.getIntExtra(BatteryManager.EXTRA_PLUGGED, 0);
            health = it.getIntExtra(BatteryManager.EXTRA_HEALTH, BatteryManager.BATTERY_HEALTH_UNKNOWN);
            temperatureTenths = it.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, 0);
            voltageMv = it.getIntExtra(BatteryManager.EXTRA_VOLTAGE, 0);
            technology = it.getStringExtra(BatteryManager.EXTRA_TECHNOLOGY);
            if (technology == null) technology = "";
            cycleCount = it.getIntExtra("android.os.extra.CYCLE_COUNT", -1);
        }
        charging = status == BatteryManager.BATTERY_STATUS_CHARGING
                || status == BatteryManager.BATTERY_STATUS_FULL;
        full = status == BatteryManager.BATTERY_STATUS_FULL;
        pluggedIn = plugged != 0;

        BatteryManager bm = (BatteryManager) ctx.getSystemService(Context.BATTERY_SERVICE);
        if (bm != null) {
            chargeCounterUah = readProp(bm, BatteryManager.BATTERY_PROPERTY_CHARGE_COUNTER);
            currentNowUa = readProp(bm, BatteryManager.BATTERY_PROPERTY_CURRENT_NOW);
            energyCounterNh = readProp(bm, BatteryManager.BATTERY_PROPERTY_ENERGY_COUNTER);
        }

        probeSysfs();

        // 满充容量：sysfs 优先，其次用剩余电荷 / 电量反推
        fullCapacityMah = 0;
        capacitySource = "";
        double sysFull = readLong(sysChargeFullPath) / 1000.0; // µAh -> mAh
        if (sysFull > 500) {
            fullCapacityMah = sysFull;
            capacitySource = L.t("系统电池节点", "sysfs");
        } else if (chargeCounterUah > 0 && level > 0) {
            double est = (chargeCounterUah / 1000.0) / level * 100.0;
            if (est > 500) {
                fullCapacityMah = est;
                capacitySource = L.t("电荷计数反推", "charge counter");
            }
        }

        // 设计容量：sysfs -> 用户手填
        designCapacityMah = 0;
        designSource = "";
        double sysDesign = readLong(sysChargeFullDesignPath) / 1000.0;
        if (sysDesign > 500) {
            designCapacityMah = sysDesign;
            designSource = L.t("系统电池节点", "sysfs");
        } else {
            double pref = Prefs.getDesignMah(ctx);
            if (pref > 500) {
                designCapacityMah = pref;
                designSource = L.t("手动填写", "manual");
            }
        }

        if (sysCyclePath != null && cycleCount < 0) {
            long c = readLong(sysCyclePath);
            if (c > 0) cycleCount = (int) c;
        }

        // 电流：BatteryManager 优先，其次 sysfs
        long ua = Math.abs(currentNowUa);
        currentSource = L.t("系统电量属性", "BatteryManager");
        if (ua == 0 || ua >= 2147483000L) {
            ua = Math.abs(readLong(sysCurrentPath));
            currentSource = L.t("系统电池节点", "sysfs");
        }
        currentMa = ua / 1000.0;

        long uv = readLong(sysVoltagePath);
        voltageV = voltageMv > 0 ? voltageMv / 1000.0 : (uv > 0 ? uv / 1e6 : 0);
        if (voltageV <= 0 && voltageMv > 0) voltageV = voltageMv / 1000.0;

        tempC = temperatureTenths > 0 ? temperatureTenths / 10.0 : 0;
        if (tempC <= 0) {
            long st = readLong(sysTempPath);
            if (st > 0) tempC = st / 10.0;
        }

        powerW = currentMa / 1000.0 * voltageV;
        if (!charging) powerW = -powerW;

        speedPctPerHour = 0;
        minutesToFull = -1;
        if (charging && fullCapacityMah > 0 && currentMa > 0) {
            speedPctPerHour = currentMa / fullCapacityMah * 100.0;
            if (level < 100 && speedPctPerHour > 0.01) {
                minutesToFull = (int) Math.round((100 - level) / speedPctPerHour * 60.0);
            }
        }
    }

    private long readProp(BatteryManager bm, int prop) {
        try {
            long v = bm.getLongProperty(prop);
            if (v == Long.MIN_VALUE || v == Integer.MIN_VALUE) return 0;
            return v;
        } catch (Throwable t) {
            return 0;
        }
    }

    private void probeSysfs() {
        if (sysProbed) return;
        sysProbed = true;
        String base = "/sys/class/power_supply/battery/";
        sysChargeFullPath = firstExisting(base, "charge_full", "energy_full");
        sysChargeFullDesignPath = firstExisting(base, "charge_full_design", "energy_full_design");
        sysCyclePath = firstExisting(base, "cycle_count");
        sysCurrentPath = firstExisting(base, "current_now", "current_avg");
        sysVoltagePath = firstExisting(base, "voltage_now");
        sysTempPath = firstExisting(base, "temp");
    }

    private String firstExisting(String base, String... names) {
        for (String n : names) {
            File f = new File(base + n);
            if (f.exists() && f.canRead()) return f.getAbsolutePath();
        }
        return null;
    }

    private long readLong(String path) {
        if (path == null) return 0;
        try (BufferedReader r = new BufferedReader(new FileReader(path))) {
            String line = r.readLine();
            if (line == null) return 0;
            line = line.trim();
            if (line.isEmpty()) return 0;
            return Long.parseLong(line);
        } catch (Throwable t) {
            return 0;
        }
    }

    public static String deviceSummary() {
        String m = Build.MANUFACTURER == null ? "" : Build.MANUFACTURER;
        String model = Build.MODEL == null ? "" : Build.MODEL;
        if (model.toLowerCase(Locale.ROOT).startsWith(m.toLowerCase(Locale.ROOT))) return model;
        return (m + " " + model).trim();
    }
}




