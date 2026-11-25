package com.nesoncalo.hardwaremaster;

import android.app.ActivityManager;
import android.content.Context;
import android.os.Build;
import android.os.Environment;
import android.os.StatFs;
import android.os.SystemClock;
import android.view.Gravity;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;

/** 概览：电量环、关键指标、设备信息、充电建议。 */
public class OverviewPage extends Page {

    private RingView ring;
    private TextView heroStatus;
    private TextView heroHealth;
    private TextView heroCapacity;
    private TextView heroSpeed;

    private TextView powerValue;
    private TextView timeValue;
    private TextView tempValue;
    private TextView cycleValue;

    private TextView deviceLine;
    private TextView sysLine;
    private TextView memLine;
    private TextView storageLine;
    private TextView uptimeLine;
    private TextView advice;

    private TextView statusPill;

    public OverviewPage(MainActivity a) {
        super(a);
        buildHero();
        buildStats();
        buildDevice();
        buildAdvice();
    }

    private void buildHero() {
        LinearLayout card = Ui.card(c);
        LinearLayout row = Ui.row(c);

        ring = new RingView(c);
        LinearLayout.LayoutParams rp = new LinearLayout.LayoutParams(Ui.dp(c, 150), Ui.dp(c, 150));
        row.addView(ring, rp);

        LinearLayout col = Ui.column(c);
        LinearLayout.LayoutParams cp = new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f);
        cp.leftMargin = Ui.dp(c, 14);
        col.setLayoutParams(cp);

        statusPill = Ui.pill(c, L.t("读取中", "Reading"), Ui.ACCENT);
        LinearLayout pillRow = Ui.row(c);
        pillRow.addView(statusPill);
        col.addView(pillRow);
        col.addView(Ui.gap(c, 10));

        heroStatus = Ui.boldText(c, "—", 13, Ui.TEXT);
        col.addView(heroStatus);
        col.addView(Ui.gap(c, 8));

        heroHealth = Ui.text(c, "—", 12, Ui.SUB);
        col.addView(heroHealth);
        col.addView(Ui.gap(c, 4));

        heroCapacity = Ui.text(c, "—", 12, Ui.SUB);
        col.addView(heroCapacity);
        col.addView(Ui.gap(c, 4));

        heroSpeed = Ui.text(c, "—", 12, Ui.SUB);
        col.addView(heroSpeed);

        row.addView(col);
        card.addView(row);
        addWithBottom(card, 12);
    }

    private void buildStats() {
        Stat power = stat(L.t("充电功率", "Power"), Ui.GREEN, "—", "W");
        Stat time = stat(L.t("预计充满时间", "Time to full charge"), Ui.ACCENT, "—", "");
        LinearLayout first = twoCols(power.view, time.view);
        addWithBottom(first, 8);

        Stat temp = stat(L.t("电池温度", "Battery temp"), Ui.ORANGE, "—", "℃");
        Stat cycle = stat(L.t("循环次数", "Cycles"), Ui.PURPLE, "—", "");
        LinearLayout second = twoCols(temp.view, cycle.view);
        addWithBottom(second, 12);

        powerValue = power.value;
        timeValue = time.value;
        tempValue = temp.value;
        cycleValue = cycle.value;
    }

    private void buildDevice() {
        LinearLayout card = Ui.card(c);
        card.addView(Ui.sectionTitle(c, L.t("设备信息", "Device")));

        deviceLine = addKv(card, L.t("设备", "Device"));
        sysLine = addKv(card, L.t("系统", "System"));
        memLine = addKv(card, L.t("内存", "Memory"));
        storageLine = addKv(card, L.t("存储", "Storage"));
        uptimeLine = addKv(card, L.t("运行时长", "Uptime"));

        addWithBottom(card, 12);
    }

    private TextView addKv(LinearLayout card, String label) {
        LinearLayout row = Ui.row(c);
        TextView l = Ui.text(c, label, 12, Ui.SUB);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f);
        row.addView(l, lp);
        TextView v = Ui.boldText(c, "—", 12, Ui.TEXT);
        v.setGravity(Gravity.END);
        row.addView(v);
        card.addView(row);
        card.addView(Ui.gap(c, 8));
        return v;
    }

    private void buildAdvice() {
        LinearLayout card = Ui.card(c);
        card.addView(Ui.sectionTitle(c, L.t("充电建议", "Advice")));
        advice = Ui.text(c, "—", 12, Ui.SUB);
        advice.setLineSpacing(Ui.dp(c, 3), 1f);
        card.addView(advice);
        add(card);
    }

    @Override
    public void update(BatteryReader b) {
        ring.setData(b.level, b.charging, b.statusText(), b.charging ? Fmt.watts(b.powerW) : L.t("放电", "Discharging"));
        statusPill.setText(b.statusText());
        // 药丸底色随状态变化：重建背景
        int color = b.charging ? Ui.GREEN : Ui.ORANGE;
        statusPill.setTextColor(color);
        android.graphics.drawable.GradientDrawable d = new android.graphics.drawable.GradientDrawable();
        d.setColor(android.graphics.Color.argb(28, android.graphics.Color.red(color), android.graphics.Color.green(color), android.graphics.Color.blue(color)));
        d.setCornerRadius(Ui.dp(c, 20));
        d.setStroke(Ui.dp(c, 1), android.graphics.Color.argb(90, android.graphics.Color.red(color), android.graphics.Color.green(color), android.graphics.Color.blue(color)));
        statusPill.setBackground(d);

        double wear = b.wearPercent();
        heroStatus.setText(b.charging ? L.t("正在充电", "Charging now") : L.t("使用电池", "On battery"));
        heroHealth.setText(L.t("健康 ", "Health ") + (wear < 0 ? L.t("未知", "Unknown") : Fmt.pct(wear).replace("%", "") + "% "
                + L.t("损耗", "worn")));
        String fullCap = b.fullCapacityMah > 0 ? Fmt.mahNum(b.fullCapacityMah) : "—";
        String designCap = b.designCapacityMah > 0 ? Fmt.mahNum(b.designCapacityMah) : "—";
        heroCapacity.setText(L.tk("满充容量 ", "满充 ", "Full ") + fullCap + L.tk(" · 设计容量 ", " · 设计 ", " · design ") + designCap + " mAh");
        heroSpeed.setText(b.charging ? L.t("充电速度 ", "Charging rate ") + Fmt.speed(b.speedPctPerHour) : L.t("电流 ", "Current ") + Fmt.ma(b.currentMa));

        String pw = b.powerW == 0 ? "—" : Fmt.watts(Math.abs(b.powerW)).replace(" W", "");
        powerValue.setText(pw);
        timeValue.setText(b.minutesToFull > 0 ? Fmt.minutes(b.minutesToFull) : "—");
        tempValue.setText(b.tempC > 0 ? String.format(java.util.Locale.US, "%.1f", b.tempC) : "—");
        cycleValue.setText(b.cycleCount >= 0 ? String.valueOf(b.cycleCount) : "—");

        deviceLine.setText(BatteryReader.deviceSummary());
        sysLine.setText("Android " + Build.VERSION.RELEASE + " · API " + Build.VERSION.SDK_INT);
        try {
            ActivityManager am = (ActivityManager) c.getSystemService(Context.ACTIVITY_SERVICE);
            ActivityManager.MemoryInfo mi = new ActivityManager.MemoryInfo();
            am.getMemoryInfo(mi);
            memLine.setText(Fmt.gb(mi.availMem) + " / " + Fmt.gb(mi.totalMem));
        } catch (Throwable t) {
            memLine.setText("—");
        }
        try {
            StatFs fs = new StatFs(Environment.getDataDirectory().getAbsolutePath());
            long total = fs.getBlockCountLong() * fs.getBlockSizeLong();
            long free = fs.getAvailableBlocksLong() * fs.getBlockSizeLong();
            storageLine.setText(Fmt.gb(free) + " / " + Fmt.gb(total));
        } catch (Throwable t) {
            storageLine.setText("—");
        }
        uptimeLine.setText(Fmt.duration(SystemClock.elapsedRealtime()));

        advice.setText(buildAdviceText(b));
    }

    private String buildAdviceText(BatteryReader b) {
        StringBuilder sb = new StringBuilder();
        if (b.charging) {
            if (b.level >= 85) {
                sb.append(L.t("已过 85%，继续充到 100% 会加速正极老化，日常可以拔线。",
                        "Above 85%, charging to 100% speeds up cathode aging; unplug for daily use."));
            } else if (b.level >= 70) {
                sb.append(L.t("接近 80% 的日常上限，若不需要长途可以准备拔线。",
                        "Near the 80% daily cap; unplug if you don't need a full charge."));
            } else {
                sb.append(L.t("电量低于 80%，处于锂电池较舒适的区间。",
                        "Below 80%, a comfortable range for lithium batteries."));
            }
            if (b.tempC >= 40) {
                sb.append("\n").append(L.t("电池温度偏高，摘掉厚壳、避免边充边玩大型游戏。",
                        "Battery is warm; remove thick cases and avoid heavy gaming while charging."));
            }
            if (b.currentMa > 0 && b.speedPctPerHour > 0 && b.speedPctPerHour < 1) {
                sb.append("\n").append(L.t("当前充电速度偏慢，检查数据线、接口或是否在使用无线充电。",
                        "Charging is slow; check the cable, port, or wireless charging pad."));
            }
        } else {
            if (b.level <= 20) {
                sb.append(L.t("电量低于 20%，建议尽快充电，避免深度放电。",
                        "Below 20%, charge soon to avoid deep discharge."));
            } else {
                sb.append(L.t("处于放电状态，锂电池不需要每次都充满，保持在 20%–80% 更耐用。",
                        "On battery. Lithium cells don't need a full charge every time; 20–80% is easier on them."));
            }
        }
        sb.append("\n").append(L.t("说明：Android 不允许普通应用直接限制充电，本应用只做读数、估算与提醒。",
                "Note: Android does not let normal apps cap charging; this app only reads, estimates and reminds."));
        return sb.toString();
    }
}






