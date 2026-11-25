package com.nesoncalo.hardwaremaster;

import android.content.Context;
import android.os.Build;
import android.os.PowerManager;
import android.view.Gravity;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.util.ArrayDeque;

/** 温度与功耗助手：电池温度、系统热状态、实时功率与温度趋势。 */
public class ThermalPage extends Page {

    private TextView tempBig;
    private TextView tempState;
    private TextView tempHint;
    private Stat powerStat;
    private Stat currentStat;
    private Stat voltStat;
    private Stat thermalStat;
    private TextView advice;
    private TempChartView chart;

    private final ArrayDeque<Float> history = new ArrayDeque<>();

    public ThermalPage(MainActivity a) {
        super(a);
        buildHero();
        buildStats();
        buildChart();
        buildAdvice();
    }

    private void buildHero() {
        LinearLayout card = Ui.card(c);
        card.addView(Ui.sectionTitle(c, L.t("电池温度", "Battery temperature")));

        LinearLayout row = Ui.row(c);
        row.setGravity(Gravity.CENTER_VERTICAL);
        tempBig = Ui.boldText(c, "—", 38, Ui.ORANGE);
        row.addView(tempBig);
        TextView unit = Ui.text(c, "°C", 16, Ui.SUB);
        LinearLayout.LayoutParams ulp = new LinearLayout.LayoutParams(-2, -2);
        ulp.leftMargin = Ui.dp(c, 6);
        ulp.bottomMargin = Ui.dp(c, 4);
        row.addView(unit, ulp);

        LinearLayout right = Ui.column(c);
        tempState = Ui.boldText(c, "—", 15, Ui.TEXT);
        tempHint = Ui.text(c, "", 11, Ui.FAINT);
        tempHint.setLineSpacing(Ui.dp(c, 2), 1f);
        right.addView(tempState);
        right.addView(Ui.gap(c, 4));
        right.addView(tempHint);
        LinearLayout.LayoutParams rlp = new LinearLayout.LayoutParams(0, -2, 1f);
        rlp.leftMargin = Ui.dp(c, 18);
        row.addView(right, rlp);

        card.addView(row);
        addWithBottom(card, 12);
    }

    private void buildStats() {
        powerStat = stat(L.t("充电功率", "Charging power"), Ui.ACCENT, "—", "");
        currentStat = stat(L.t("电流", "Current draw"), Ui.GREEN, "—", "");
        LinearLayout r1 = twoCols(powerStat.view, currentStat.view);
        addWithBottom(r1, 8);

        voltStat = stat(L.t("电压", "Voltage"), Ui.PURPLE, "—", "");
        thermalStat = stat(L.t("系统热状态", "Thermal status"), Ui.ORANGE, "—", "");
        LinearLayout r2 = twoCols(voltStat.view, thermalStat.view);
        addWithBottom(r2, 12);
    }

    private void buildChart() {
        LinearLayout card = Ui.card(c);
        LinearLayout head = Ui.row(c);
        head.setGravity(Gravity.CENTER_VERTICAL);
        head.addView(Ui.sectionTitle(c, L.t("温度趋势", "Battery temperature trend")), new LinearLayout.LayoutParams(0, -2, 1f));
        head.addView(Ui.text(c, L.t("最近 90 秒", "Last 90 s"), 11, Ui.FAINT));
        card.addView(head);
        card.addView(Ui.gap(c, 8));
        chart = new TempChartView(c);
        card.addView(chart, new LinearLayout.LayoutParams(-1, Ui.dp(c, 150)));
        TextView note = Ui.text(c, L.t("每秒采样一次电池温度；超过 40℃ 会逐步限制充电功率。",
                "Battery temperature every second; charging tapers above 40℃."), 11, Ui.FAINT);
        note.setPadding(0, Ui.dp(c, 6), 0, 0);
        card.addView(note);
        addWithBottom(card, 12);
    }

    private void buildAdvice() {
        LinearLayout card = Ui.card(c);
        card.addView(Ui.sectionTitle(c, L.t("温度与功耗建议", "Thermal & power advice")));
        advice = Ui.text(c, "", 12, Ui.SUB);
        advice.setLineSpacing(Ui.dp(c, 4), 1f);
        card.addView(advice);
        card.addView(Ui.gap(c, 10));
        TextView p = Ui.text(c, L.t(
                "Android 不向普通应用开放 CPU/GPU 温度，这里用电池温度与系统热状态判断整机发热；读数只在本机使用。",
                "Android does not expose CPU/GPU sensors to normal apps, so battery temperature and thermal status stand in. All data stays on-device."), 11, Ui.FAINT);
        p.setLineSpacing(Ui.dp(c, 3), 1f);
        card.addView(p);
        add(card);
    }

    @Override
    public void update(BatteryReader b) {
        tempBig.setText(String.format(java.util.Locale.US, "%.1f", b.tempC));
        int color = b.tempC >= 43 ? Ui.RED : (b.tempC >= 40 ? Ui.ORANGE : Ui.GREEN);
        tempBig.setTextColor(color);

        String state;
        String hint;
        if (b.tempC >= 43) {
            state = L.t("温度偏高", "Too hot");
            hint = L.t("暂停充电，摘下保护壳，远离阳光直射。", "Pause charging, remove the case, avoid direct sun.");
        } else if (b.tempC >= 40) {
            state = L.t("偏热", "Warm");
            hint = L.t("仍在安全范围，但充电功率可能开始下降。", "Still safe, but charging may taper.");
        } else if (b.tempC >= 33) {
            state = L.t("温度正常", "Normal temperature");
            hint = L.t("锂电池较舒适的工作区间。", "A comfortable range for lithium cells.");
        } else if (b.tempC > 0) {
            state = L.t("偏凉", "Cool");
            hint = L.t("低温时充电速度可能受限。", "Charging may be slower when cold.");
        } else {
            state = L.t("未知", "Unknown");
            hint = L.t("设备未提供电池温度。", "The device does not report battery temperature.");
        }
        tempState.setText(state);
        tempState.setTextColor(color);
        tempHint.setText(hint);

        powerStat.value.setText(Fmt.watts(b.powerW));
        currentStat.value.setText(Fmt.ma(b.currentMa));
        voltStat.value.setText(Fmt.volt(b.voltageV));
        thermalStat.value.setText(thermalText());

        history.addLast((float) b.tempC);
        while (history.size() > 90) history.removeFirst();
        chart.setData(history);

        StringBuilder sb = new StringBuilder();
        if (b.charging) {
            sb.append(L.t("正在充电，实时功率 ", "Charging at ")).append(Fmt.watts(b.powerW))
                    .append(L.t("；电池温度 ", "; battery ")).append(Fmt.temp(b.tempC)).append("。");
        } else {
            sb.append(L.t("未在充电，电池放电功率约 ", "On battery, draw about ")).append(Fmt.watts(b.powerW)).append("。");
        }
        sb.append("\n");
        if (b.tempC >= 43) {
            sb.append(L.t("高温会加速容量衰减，建议先停止充电并让手机降温。",
                    "Heat accelerates capacity fade; stop charging and let the phone cool."));
        } else if (b.charging && b.powerW > 0 && b.powerW < 5) {
            sb.append(L.t("当前功率偏低，检查线材、接口或无线充电对位。",
                    "Low power; check the cable, port or wireless alignment."));
        } else {
            sb.append(L.t("温度与功率都在正常范围，无需干预。",
                    "Temperature and power are in the normal range."));
        }
        advice.setText(sb.toString());
    }

    private String thermalText() {
        if (Build.VERSION.SDK_INT < 29) return L.t("系统未提供", "Not available");
        try {
            PowerManager pm = (PowerManager) c.getSystemService(Context.POWER_SERVICE);
            int s = pm.getCurrentThermalStatus();
            switch (s) {
                case PowerManager.THERMAL_STATUS_NONE: return L.t("热状态正常", "Normal");
                case PowerManager.THERMAL_STATUS_LIGHT: return L.t("轻微", "Light");
                case PowerManager.THERMAL_STATUS_MODERATE: return L.t("中度", "Moderate");
                case PowerManager.THERMAL_STATUS_SEVERE: return L.t("严重", "Severe");
                case PowerManager.THERMAL_STATUS_CRITICAL: return L.t("临界", "Critical");
                case PowerManager.THERMAL_STATUS_EMERGENCY: return L.t("紧急", "Emergency");
                case PowerManager.THERMAL_STATUS_SHUTDOWN: return L.t("关机级", "Shutdown");
                default: return L.t("未知", "Unknown");
            }
        } catch (Throwable t) {
            return L.t("未知", "Unknown");
        }
    }
}





