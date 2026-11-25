package com.nesoncalo.hardwaremaster;

import android.app.AlertDialog;
import android.view.Gravity;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONObject;

/** 记录：每次充电会话的归档，最多 60 条。 */
public class HistoryPage extends Page {

    private LinearLayout listBox;
    private TextView countValue;
    private TextView totalValue;
    private TextView emptyHint;
    private TextView avgPeakValue;

    public HistoryPage(MainActivity a) {
        super(a);
        buildSummary();
        buildList();
        refreshList();
    }

    private void buildSummary() {
        LinearLayout card = Ui.card(c);
        card.addView(Ui.sectionTitle(c, L.t("累计", "Totals")));
        LinearLayout row = Ui.row(c);
        row.addView(kv(L.t("充电次数", "Sessions"), "countValue"), new LinearLayout.LayoutParams(0, -2, 1f));
        row.addView(kv(L.t("累计充入", "Total added"), "totalValue"), new LinearLayout.LayoutParams(0, -2, 1f));
        row.addView(kv(L.t("平均峰值", "Avg peak"), "avgPeakValue"), new LinearLayout.LayoutParams(0, -2, 1f));
        card.addView(row);
        addWithBottom(card, 12);
    }

    private LinearLayout kv(String label, String ref) {
        LinearLayout l = Ui.column(c);
        l.addView(Ui.text(c, label, 11, Ui.SUB));
        l.addView(Ui.gap(c, 4));
        TextView v = Ui.boldText(c, "—", 16, Ui.TEXT);
        l.addView(v);
        if ("countValue".equals(ref)) countValue = v;
        else if ("totalValue".equals(ref)) totalValue = v;
        else avgPeakValue = v;
        return l;
    }

    private void buildList() {
        LinearLayout head = Ui.row(c);
        TextView title = Ui.sectionTitle(c, L.t("充电会话", "Sessions"));
        head.addView(title, new LinearLayout.LayoutParams(0, -2, 1f));
        TextView clear = Ui.button(c, L.t("清空", "Clear"), Ui.RED, false);
        clear.setOnClickListener(v -> confirmClear());
        head.addView(clear);
        add(head);

        emptyHint = Ui.text(c, L.t("还没有记录。插上充电器并用一会儿，拔线后会自动归档。",
                "No records yet. Charge for a while and unplug to archive a session."), 12, Ui.FAINT);
        emptyHint.setLineSpacing(Ui.dp(c, 3), 1f);
        addWithBottom(emptyHint, 8);

        listBox = Ui.column(c);
        add(listBox);
    }

    private void confirmClear() {
        new AlertDialog.Builder(c)
                .setTitle(L.t("清空充电记录？", "Clear charging history?"))
                .setMessage(L.t("只删除本机保存的会话记录，不影响电池数据。", "Only local session records are removed."))
                .setNegativeButton(L.t("取消", "Cancel"), null)
                .setPositiveButton(L.t("清空", "Clear"), (d, w) -> {
                    Prefs.setSessions(c, "[]");
                    refreshList();
                })
                .show();
    }

    /** 重新读取本地会话并重建列表。 */
    public void refreshList() {
        listBox.removeAllViews();
        JSONArray arr;
        try {
            arr = new JSONArray(Prefs.sessions(c));
        } catch (Throwable t) {
            arr = new JSONArray();
        }
        int n = arr.length();
        emptyHint.setVisibility(n == 0 ? View.VISIBLE : View.GONE);
        countValue.setText(String.valueOf(n));
        double totalWh = 0;
        double peakSum = 0;
        for (int i = 0; i < n; i++) {
            try {
                JSONObject o = arr.getJSONObject(i);
                totalWh += o.optDouble("wh", 0);
                peakSum += o.optDouble("peakW", 0);
            } catch (Throwable ignored) {}
        }
        totalValue.setText(Fmt.wh(totalWh));
        avgPeakValue.setText(n == 0 ? "—" : Fmt.watts(peakSum / n));

        for (int i = n - 1; i >= 0; i--) {
            try {
                listBox.addView(rowCard(arr.getJSONObject(i)));
                listBox.addView(Ui.gap(c, 8));
            } catch (Throwable ignored) {}
        }
    }

    private LinearLayout rowCard(JSONObject o) {
        LinearLayout card = new LinearLayout(c);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(Ui.dp(c, 14), Ui.dp(c, 12), Ui.dp(c, 14), Ui.dp(c, 12));
        card.setBackground(Ui.roundStroke(Ui.CARD_SOFT, 14, Ui.STROKE, c));

        LinearLayout top = Ui.row(c);
        long start = o.optLong("start", 0);
        TextView when = Ui.boldText(c, Fmt.dayClock(start), 13, Ui.TEXT);
        top.addView(when, new LinearLayout.LayoutParams(0, -2, 1f));
        TextView range = Ui.boldText(c, o.optInt("startLevel") + "% → " + o.optInt("endLevel") + "%", 13, Ui.GREEN);
        top.addView(range);
        card.addView(top);

        card.addView(Ui.gap(c, 6));
        LinearLayout bottom = Ui.row(c);
        long dur = Math.max(0, o.optLong("end", 0) - start);
        String line = Fmt.duration(dur) + " · " + Fmt.wh(o.optDouble("wh", 0)) + " · " + L.t("峰值 ", "peak ")
                + Fmt.watts(o.optDouble("peakW", 0));
        TextView detail = Ui.text(c, line, 11, Ui.SUB);
        bottom.addView(detail, new LinearLayout.LayoutParams(0, -2, 1f));
        bottom.addView(Ui.text(c, L.t("平均 ", "avg ") + Fmt.watts(dur > 0 ? o.optDouble("wh", 0) / (dur / 3600000.0) : 0), 11, Ui.FAINT));
        card.addView(bottom);
        return card;
    }

    @Override
    public void update(BatteryReader b) {
        // 列表只在进入页面或清空时重建，避免每秒刷屏
    }
}




