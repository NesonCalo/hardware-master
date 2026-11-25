package com.nesoncalo.hardwaremaster;

import android.content.Context;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.ScrollView;

/** 页面基类：统一滚动容器与内边距。 */
public abstract class Page {

    protected final MainActivity act;
    protected final Context c;
    protected final LinearLayout body;
    protected final ScrollView root;

    Page(MainActivity a) {
        this.act = a;
        this.c = a;
        root = new ScrollView(c);
        root.setFillViewport(true);
        root.setClipToPadding(false);
        root.setPadding(Ui.dp(c, 18), Ui.dp(c, 10), Ui.dp(c, 18), Ui.dp(c, 24));
        body = new LinearLayout(c);
        body.setOrientation(LinearLayout.VERTICAL);
        root.addView(body, new ScrollView.LayoutParams(
                ScrollView.LayoutParams.MATCH_PARENT, ScrollView.LayoutParams.WRAP_CONTENT));
    }

    public View root() {
        return root;
    }

    protected static class Stat {
        public LinearLayout view;
        public android.widget.TextView value;
    }

    /** 四宫格指标，保存数值 TextView 以便刷新。 */
    protected Stat stat(String label, int accent, String value, String unit) {
        Stat s = new Stat();
        LinearLayout box = new LinearLayout(c);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(Ui.dp(c, 12), Ui.dp(c, 12), Ui.dp(c, 12), Ui.dp(c, 12));
        box.setBackground(Ui.roundStroke(Ui.CARD_SOFT, 14, Ui.STROKE, c));

        LinearLayout head = Ui.row(c);
        head.addView(Ui.text(c, "▍", 11, accent));
        head.addView(Ui.text(c, label, 11, Ui.SUB));
        box.addView(head);
        box.addView(Ui.gap(c, 6));

        LinearLayout val = Ui.row(c);
        s.value = Ui.boldText(c, value, 21, accent);
        val.addView(s.value);
        if (unit != null && !unit.isEmpty()) {
            android.widget.TextView u = Ui.text(c, unit, 11, Ui.SUB);
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT);
            lp.leftMargin = Ui.dp(c, 4);
            lp.bottomMargin = Ui.dp(c, 2);
            u.setLayoutParams(lp);
            val.addView(u);
        }
        box.addView(val);
        s.view = box;
        return s;
    }

    protected LinearLayout twoCols(View left, View right) {
        LinearLayout row = Ui.row(c);
        LinearLayout.LayoutParams lp1 = new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f);
        lp1.rightMargin = Ui.dp(c, 8);
        row.addView(left, lp1);
        LinearLayout.LayoutParams lp2 = new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f);
        lp2.leftMargin = Ui.dp(c, 8);
        row.addView(right, lp2);
        return row;
    }

    protected void add(View v) {
        body.addView(v, Ui.matchWrap());
    }

    protected void addWithBottom(View v, float bottomDp) {
        LinearLayout.LayoutParams lp = Ui.matchWrap();
        lp.bottomMargin = Ui.dp(c, bottomDp);
        body.addView(v, lp);
    }

    public void update(BatteryReader b) {}

    public void onSample(BatteryReader b) {}
}




