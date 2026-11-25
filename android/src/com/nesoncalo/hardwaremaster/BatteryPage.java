package com.nesoncalo.hardwaremaster;

import android.content.res.ColorStateList;
import android.view.Gravity;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

/** 电池：容量、损耗、健康、循环次数与估算说明。 */
public class BatteryPage extends Page {

    private TextView wearBig;
    private TextView wearHint;
    private CapacityBarView bar;
    private TextView barLabel;

    private TextView designValue;
    private TextView fullValue;
    private TextView healthValue;
    private TextView cycleValue;
    private TextView techValue;
    private TextView voltValue;
    private TextView statusValue;
    private TextView sourceValue;

    public BatteryPage(MainActivity a) {
        super(a);
        buildHero();
        buildRows();
        buildNotes();
    }

    private void buildHero() {
        LinearLayout card = Ui.card(c);

        card.addView(Ui.text(c, L.t("电池损耗", "Battery wear"), 11, Ui.SUB));
        card.addView(Ui.gap(c, 4));
        wearBig = Ui.boldText(c, "未知", 30, Ui.FAINT);
        card.addView(wearBig);
        wearHint = Ui.text(c, "—", 11, Ui.FAINT);
        card.addView(wearHint);

        card.addView(Ui.gap(c, 14));
        bar = new CapacityBarView(c);
        card.addView(bar, new LinearLayout.LayoutParams(-1, Ui.dp(c, 8)));
        card.addView(Ui.gap(c, 8));
        barLabel = Ui.text(c, "—", 11, Ui.FAINT);
        card.addView(barLabel);

        card.addView(Ui.divider(c));

        LinearLayout bottom = Ui.row(c);
        LinearLayout h = Ui.column(c);
        h.addView(Ui.text(c, L.t("健康状态", "Health"), 11, Ui.SUB));
        h.addView(Ui.gap(c, 3));
        healthValue = Ui.boldText(c, "—", 15, Ui.GREEN);
        h.addView(healthValue);
        bottom.addView(h, new LinearLayout.LayoutParams(0, -2, 1f));

        LinearLayout cy = Ui.column(c);
        cy.addView(Ui.text(c, L.t("循环次数", "Cycle count"), 11, Ui.SUB));
        cy.addView(Ui.gap(c, 3));
        cycleValue = Ui.boldText(c, "—", 15, Ui.TEXT);
        cy.addView(cycleValue);
        bottom.addView(cy, new LinearLayout.LayoutParams(0, -2, 1f));
        card.addView(bottom);

        addWithBottom(card, 12);
    }

    private void buildRows() {
        LinearLayout card = Ui.card(c);
        card.addView(Ui.sectionTitle(c, L.t("容量明细", "Capacity")));

        designValue = kvRow(card, L.t("设计容量", "Design capacity"));
        fullValue = kvRow(card, L.t("当前满充容量", "Full charge capacity"));
        voltValue = kvRow(card, L.t("当前电压", "Voltage"));
        techValue = kvRow(card, L.t("电池技术", "Technology"));
        statusValue = kvRow(card, L.t("充电状态", "Status"));
        sourceValue = kvRow(card, L.t("数据来源", "Source"));

        addWithBottom(card, 12);
    }

    private TextView kvRow(LinearLayout card, String label) {
        LinearLayout row = Ui.row(c);
        row.addView(Ui.text(c, label, 12, Ui.SUB), new LinearLayout.LayoutParams(0, -2, 1f));
        TextView v = Ui.boldText(c, "—", 12, Ui.TEXT);
        v.setGravity(Gravity.END);
        row.addView(v);
        card.addView(row);
        card.addView(Ui.gap(c, 9));
        return v;
    }

    private void buildNotes() {
        LinearLayout card = Ui.card(c);
        card.addView(Ui.sectionTitle(c, L.t("怎么算的", "How it is calculated")));
        TextView t = Ui.text(c, L.t(
                "损耗 = 1 − 当前满充容量 ÷ 设计容量。设计容量优先读系统电池节点，读不到就用设置里手填的标称容量；满充容量优先读 charge_full，读不到时用「剩余电荷 ÷ 当前电量」反推。\n\n"
                        + "新机一般在 0–5%，超过 20% 说明可用容量明显缩水。部分厂商会隐藏这两个值，此时损耗显示为未知，可以在设置里填入官网标称容量来获得估算。\n\n"
                        + "循环次数由 Android 14 起部分机型提供，读不到不代表电池有问题。",
                "Wear = 1 − full charge capacity ÷ design capacity. Design capacity comes from the system battery node, "
                        + "or from the nominal value you enter in Settings. Full capacity comes from charge_full, or is "
                        + "estimated as remaining charge ÷ current level.\n\n"
                        + "A new cell is usually 0–5%; above 20% means noticeable capacity loss. Some vendors hide these values; "
                        + "wear then shows unknown until you enter the rated capacity.\n\n"
                        + "Cycle count is exposed by some devices on Android 14+; missing values are normal."),
                12, Ui.SUB);
        t.setLineSpacing(Ui.dp(c, 4), 1f);
        card.addView(t);
        addWithBottom(card, 12);

        LinearLayout tip = Ui.card(c);
        tip.addView(Ui.sectionTitle(c, L.t("使用建议", "Tips")));
        TextView t2 = Ui.text(c, L.t(
                "• 日常保持在 20%–80%，比每次充满更护电池。\n"
                        + "• 避免长时间满电插着，尤其是高温环境。\n"
                        + "• 每月一次完整充放到校准电量显示，不必频繁做。\n"
                        + "• 温度对寿命的影响比循环次数更大。",
                "• Stay between 20–80% for daily use.\n"
                        + "• Avoid sitting at 100% for long periods, especially when warm.\n"
                        + "• A full charge/discharge once a month can recalibrate the gauge.\n"
                        + "• Heat ages cells faster than cycle count."),
                12, Ui.SUB);
        t2.setLineSpacing(Ui.dp(c, 4), 1f);
        tip.addView(t2);
        add(tip);
    }

    @Override
    public void update(BatteryReader b) {
        double wear = b.wearPercent();
        if (wear < 0) {
            wearBig.setText(L.t("未知", "Unknown"));
            wearBig.setTextSize(24);
            wearBig.setTextColor(Ui.FAINT);
            wearHint.setText(L.t("缺少容量数据，可在设置填写设计容量", "No capacity data; set design capacity"));
            bar.setRatio(0);
            barLabel.setText(L.t("满充容量未知", "Full capacity unknown"));
        } else {
            wearBig.setTextSize(30);
            wearBig.setText(String.format(java.util.Locale.US, "%.1f%%", wear));
            wearBig.setTextColor(wear >= 20 ? Ui.RED : (wear >= 10 ? Ui.ORANGE : Ui.GREEN));
            String hint;
            if (wear < 5) hint = L.t("接近新电池水平", "Close to new");
            else if (wear < 10) hint = L.t("轻度损耗，正常", "Slight wear, normal");
            else if (wear < 20) hint = L.t("中度损耗，续航略降", "Moderate wear");
            else hint = L.t("损耗偏大，建议考虑换电池", "High wear; consider a battery service");
            wearHint.setText(hint);
            int ratio = (int) Math.round(b.fullCapacityMah / b.designCapacityMah * 100);
            bar.setRatio(ratio / 100f);
            barLabel.setText(L.t("满充容量约为设计容量的 ", "Full capacity is ") + ratio + "% "
                    + L.t("（", "(") + Fmt.mah(b.fullCapacityMah) + " / " + Fmt.mah(b.designCapacityMah) + "）");
        }
        healthValue.setText(b.healthText());
        healthValue.setTextColor(b.health == android.os.BatteryManager.BATTERY_HEALTH_GOOD ? Ui.GREEN : Ui.ORANGE);
        cycleValue.setText(Fmt.cycles(b.cycleCount));
        designValue.setText(b.designCapacityMah > 0 ? Fmt.mah(b.designCapacityMah) : L.t("未知（可在设置填写）", "Unknown (set in Settings)"));
        fullValue.setText(Fmt.mah(b.fullCapacityMah));
        voltValue.setText(Fmt.volt(b.voltageV));
        techValue.setText(b.technology.isEmpty() ? "—" : b.technology);
        statusValue.setText(b.statusText() + " · " + b.plugText());
        if (b.designCapacityMah > 0 && b.fullCapacityMah > 0) {
            sourceValue.setText(b.designSource.equals(b.capacitySource)
                    ? b.designSource
                    : b.designSource + " / " + b.capacitySource);
        } else {
            sourceValue.setText(L.t("系统未提供", "Not exposed"));
        }
    }
}






