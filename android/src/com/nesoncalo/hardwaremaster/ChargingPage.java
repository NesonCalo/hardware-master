package com.nesoncalo.hardwaremaster;

import android.view.Gravity;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;

/** 充电：实时功率、电流电压、速度、曲线与会话统计。 */
public class ChargingPage extends Page {

    private TextView powerBig;
    private TextView powerUnit;
    private TextView typePill;
    private TextView currentValue;
    private TextView voltageValue;
    private TextView tempValue;

    private TextView speedValue;
    private TextView remainValue;
    private TextView sessionWhValue;
    private TextView peakValue;

    private TextView sessionRange;
    private TextView sessionDuration;
    private TextView sessionAvg;

    private CurveView curve;

    public ChargingPage(MainActivity a) {
        super(a);
        buildPower();
        buildTiles();
        buildCurve();
        buildSession();
    }

    private void buildPower() {
        LinearLayout card = Ui.card(c);
        LinearLayout top = Ui.row(c);

        LinearLayout left = Ui.column(c);
        LinearLayout bigRow = Ui.row(c);
        powerBig = Ui.boldText(c, "—", 36, Ui.GREEN);
        bigRow.addView(powerBig);
        powerUnit = Ui.text(c, "W", 13, Ui.SUB);
        LinearLayout.LayoutParams upl = new LinearLayout.LayoutParams(-2, -2);
        upl.leftMargin = Ui.dp(c, 4);
        upl.bottomMargin = Ui.dp(c, 4);
        powerUnit.setLayoutParams(upl);
        bigRow.addView(powerUnit);
        left.addView(bigRow);
        left.addView(Ui.text(c, L.t("实时充电功率", "Real-time charging power"), 11, Ui.SUB));
        top.addView(left, new LinearLayout.LayoutParams(0, -2, 1f));

        typePill = Ui.pill(c, L.t("未连接", "Unplugged"), Ui.SUB);
        top.addView(typePill);
        card.addView(top);

        card.addView(Ui.divider(c));

        LinearLayout metrics = Ui.row(c);
        metrics.addView(kvBlock(L.t("电流", "Current draw"), "currentValue"), new LinearLayout.LayoutParams(0, -2, 1f));
        metrics.addView(kvBlock(L.t("电压", "Voltage"), "voltageValue"), new LinearLayout.LayoutParams(0, -2, 1f));
        metrics.addView(kvBlock(L.t("电池温度", "Battery temp"), "tempValue"), new LinearLayout.LayoutParams(0, -2, 1f));
        card.addView(metrics);

        addWithBottom(card, 12);
    }

    private LinearLayout kvBlock(String label, String which) {
        LinearLayout l = Ui.column(c);
        l.addView(Ui.text(c, label, 11, Ui.SUB));
        l.addView(Ui.gap(c, 4));
        TextView v = Ui.boldText(c, "—", 16, Ui.TEXT);
        l.addView(v);
        if ("currentValue".equals(which)) currentValue = v;
        else if ("voltageValue".equals(which)) voltageValue = v;
        else tempValue = v;
        return l;
    }

    private void buildTiles() {
        Stat speed = stat(L.t("充电速度", "Charging rate"), Ui.ACCENT, "—", "");
        Stat remain = stat(L.t("充满剩余时间", "Time to full charge"), Ui.PURPLE, "—", "");
        addWithBottom(twoCols(speed.view, remain.view), 8);

        Stat wh = stat(L.t("本次充入电量", "Added energy"), Ui.GREEN, "—", "");
        Stat peak = stat(L.t("峰值功率", "Peak"), Ui.ORANGE, "—", "W");
        addWithBottom(twoCols(wh.view, peak.view), 12);

        speedValue = speed.value;
        remainValue = remain.value;
        sessionWhValue = wh.value;
        peakValue = peak.value;
    }

    private void buildCurve() {
        LinearLayout card = Ui.card(c);
        LinearLayout titleRow = Ui.row(c);
        titleRow.addView(Ui.sectionTitle(c, L.t("充电曲线", "Charging curve")), new LinearLayout.LayoutParams(0, -2, 1f));
        TextView tag = Ui.text(c, L.t("近 90 秒", "last 90s"), 11, Ui.FAINT);
        titleRow.addView(tag);
        card.addView(titleRow);

        curve = new CurveView(c);
        card.addView(curve, new LinearLayout.LayoutParams(-1, Ui.dp(c, 170)));
        android.widget.TextView note = Ui.text(c, L.t("曲线每秒采样一次，用于观察功率爬坡与降速。", "Sampled every second to show power ramp and taper."), 11, Ui.FAINT);
        note.setPadding(0, Ui.dp(c, 6), 0, 0);
        card.addView(note);
        addWithBottom(card, 12);
    }

    private void buildSession() {
        LinearLayout card = Ui.card(c);
        card.addView(Ui.sectionTitle(c, L.t("本次充电", "This session")));

        sessionRange = kvRow(card, L.t("电量区间", "Level range"));
        sessionDuration = kvRow(card, L.t("已充时长", "Duration"));
        sessionAvg = kvRow(card, L.t("平均功率", "Average"));

        card.addView(Ui.gap(c, 8));
        card.addView(Ui.text(c, L.t("会话在拔线后自动归档到「记录」页。", "Sessions are archived to History when unplugged."), 11, Ui.FAINT));
        add(card);
    }

    private TextView kvRow(LinearLayout card, String label) {
        LinearLayout row = Ui.row(c);
        row.addView(Ui.text(c, label, 12, Ui.SUB), new LinearLayout.LayoutParams(0, -2, 1f));
        TextView v = Ui.boldText(c, "—", 12, Ui.TEXT);
        v.setGravity(Gravity.END);
        row.addView(v);
        card.addView(row);
        card.addView(Ui.gap(c, 8));
        return v;
    }

    @Override
    public void onSample(BatteryReader b) {
        curve.push(b.level, Math.abs(b.powerW));
    }

    @Override
    public void update(BatteryReader b) {
        powerBig.setText(b.charging && b.powerW > 0 ? Fmt.watts(b.powerW).replace(" W", "") : "—");
        powerBig.setTextColor(b.charging ? Ui.GREEN : Ui.FAINT);

        typePill.setText(b.plugText());
        int color = b.charging ? Ui.GREEN : (b.pluggedIn ? Ui.ORANGE : Ui.SUB);
        typePill.setTextColor(color);
        android.graphics.drawable.GradientDrawable d = new android.graphics.drawable.GradientDrawable();
        d.setColor(android.graphics.Color.argb(28, android.graphics.Color.red(color), android.graphics.Color.green(color), android.graphics.Color.blue(color)));
        d.setCornerRadius(Ui.dp(c, 20));
        d.setStroke(Ui.dp(c, 1), android.graphics.Color.argb(90, android.graphics.Color.red(color), android.graphics.Color.green(color), android.graphics.Color.blue(color)));
        typePill.setBackground(d);

        currentValue.setText(Fmt.ma(b.currentMa));
        voltageValue.setText(Fmt.volt(b.voltageV));
        tempValue.setText(b.tempC > 0 ? String.format(java.util.Locale.US, "%.1f ℃", b.tempC) : "—");

        speedValue.setText(b.speedPctPerHour > 0 ? String.format(java.util.Locale.US, "%.1f", b.speedPctPerHour) : "—");
        remainValue.setText(b.minutesToFull > 0 ? Fmt.minutes(b.minutesToFull) : "—");
        sessionWhValue.setText(SessionStore.active ? Fmt.wh(SessionStore.wh) : "—");
        peakValue.setText(SessionStore.active && SessionStore.peakW > 0 ? String.format(java.util.Locale.US, "%.1f", SessionStore.peakW) : "—");

        if (SessionStore.active) {
            sessionRange.setText(SessionStore.startLevel + "% → " + b.level + "%");
            sessionDuration.setText(Fmt.duration(System.currentTimeMillis() - SessionStore.startMs));
            sessionAvg.setText(Fmt.watts(SessionStore.avgW()));
        } else {
            sessionRange.setText("—");
            sessionDuration.setText("—");
            sessionAvg.setText("—");
        }
        if (sessionWhValue.getText().toString().isEmpty()) sessionWhValue.setText("—");
    }
}





