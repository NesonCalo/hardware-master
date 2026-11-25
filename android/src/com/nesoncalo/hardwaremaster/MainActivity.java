package com.nesoncalo.hardwaremaster;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.util.ArrayList;
import java.util.List;

/** 主界面：顶部状态、页面容器、底部五页导航。 */
public class MainActivity extends Activity {

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final BatteryReader reader = new BatteryReader();
    private final List<Page> pages = new ArrayList<>();
    private final List<LinearLayout> navItems = new ArrayList<>();

    private LinearLayout host;
    private TextView statusPill;
    private TextView subtitle;
    private int index = 0;

    private final Runnable ticker = new Runnable() {
        @Override
        public void run() {
            try {
                reader.read(MainActivity.this);
                SessionStore.tick(MainActivity.this, reader);
                header();
                if (index >= 0 && index < pages.size()) {
                    pages.get(index).update(reader);
                    pages.get(index).onSample(reader);
                }
            } catch (Throwable ignored) {}
            handler.postDelayed(this, 1000);
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        L.init(this);
        if (Prefs.bgMonitor(this)) {
            Intent svc = new Intent(this, ChargingService.class);
            startForegroundService(svc);
        }
        getWindow().setStatusBarColor(Ui.BG);
        getWindow().setNavigationBarColor(Ui.BG);

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Ui.BG);
        root.setFitsSystemWindows(true);

        root.addView(buildHeader(), new LinearLayout.LayoutParams(-1, -2));

        host = new LinearLayout(this);
        host.setOrientation(LinearLayout.VERTICAL);
        root.addView(host, new LinearLayout.LayoutParams(-1, 0, 1f));

        root.addView(buildNav(), new LinearLayout.LayoutParams(-1, Ui.dp(this, 64)));

        setContentView(root);

        pages.add(new OverviewPage(this));
        pages.add(new ChargingPage(this));
        pages.add(new BatteryPage(this));
        pages.add(new ThermalPage(this));
        pages.add(new HistoryPage(this));
        pages.add(new SettingsPage(this));

        show(0);
    }

    private View buildHeader() {
        LinearLayout bar = new LinearLayout(this);
        bar.setOrientation(LinearLayout.HORIZONTAL);
        bar.setGravity(Gravity.CENTER_VERTICAL);
        bar.setPadding(Ui.dp(this, 20), Ui.dp(this, 12), Ui.dp(this, 16), Ui.dp(this, 8));

        LinearLayout titles = new LinearLayout(this);
        titles.setOrientation(LinearLayout.VERTICAL);
        TextView t = new TextView(this);
        t.setText(L.t("硬件管理大师", "Hardware Master"));
        t.setTextSize(20);
        t.setTextColor(Ui.TEXT);
        t.setTypeface(Typeface.create("sans-serif-medium", Typeface.NORMAL));
        titles.addView(t);

        subtitle = new TextView(this);
        subtitle.setText(L.t("Android · 电池与充电", "Android · battery & charging"));
        subtitle.setTextSize(11);
        subtitle.setTextColor(Ui.SUB);
        titles.addView(subtitle);
        bar.addView(titles, new LinearLayout.LayoutParams(0, -2, 1f));

        statusPill = Ui.pill(this, L.t("读取中", "Reading"), Ui.ACCENT);
        bar.addView(statusPill);
        return bar;
    }

    private View buildNav() {
        LinearLayout nav = new LinearLayout(this);
        nav.setOrientation(LinearLayout.HORIZONTAL);
        nav.setGravity(Gravity.CENTER);
        nav.setPadding(Ui.dp(this, 6), Ui.dp(this, 6), Ui.dp(this, 6), Ui.dp(this, 6));
        nav.setBackgroundColor(Ui.CARD_SOFT);

        String[][] items = {
                {"◉", L.t("概览", "Overview")},
                {"⚡", L.t("充电", "Charging")},
                {"▮", L.t("电池", "Battery")},
                {"℃", L.t("温度", "Temp")},
                {"≡", L.t("充电记录", "Charging history")},
                {"⚙", L.t("设置", "Settings")}
        };
        for (int i = 0; i < items.length; i++) {
            final int idx = i;
            LinearLayout item = new LinearLayout(this);
            item.setOrientation(LinearLayout.VERTICAL);
            item.setGravity(Gravity.CENTER);
            TextView icon = new TextView(this);
            icon.setText(items[i][0]);
            icon.setTextSize(16);
            icon.setGravity(Gravity.CENTER);
            TextView label = new TextView(this);
            label.setText(items[i][1]);
            label.setTextSize(9);
            label.setGravity(Gravity.CENTER);
            item.addView(icon, new LinearLayout.LayoutParams(-1, -2));
            item.addView(label, new LinearLayout.LayoutParams(-1, -2));
            item.setOnClickListener(v -> show(idx));
            nav.addView(item, new LinearLayout.LayoutParams(0, -1, 1f));
            navItems.add(item);
        }
        return nav;
    }

    private void show(int i) {
        index = i;
        host.removeAllViews();
        View page = pages.get(i).root();
        if (page.getParent() != null) ((android.view.ViewGroup) page.getParent()).removeView(page);
        host.addView(page, new LinearLayout.LayoutParams(-1, -1));

        for (int k = 0; k < navItems.size(); k++) {
            LinearLayout item = navItems.get(k);
            boolean on = k == i;
            for (int n = 0; n < item.getChildCount(); n++) {
                TextView tv = (TextView) item.getChildAt(n);
                tv.setTextColor(on ? Ui.ACCENT : Ui.FAINT);
                tv.setTypeface(on ? Typeface.create("sans-serif-medium", Typeface.NORMAL) : Typeface.DEFAULT);
            }
        }
        reader.read(this);
        pages.get(i).update(reader);
        if (pages.get(i) instanceof HistoryPage) ((HistoryPage) pages.get(i)).refreshList();
    }

    private void header() {
        int c = reader.charging ? Ui.GREEN : (reader.pluggedIn ? Ui.ORANGE : Ui.ORANGE);
        statusPill.setText(reader.statusText() + " · " + reader.level + "%");
        statusPill.setTextColor(c);
        android.graphics.drawable.GradientDrawable d = new android.graphics.drawable.GradientDrawable();
        d.setColor(Color.argb(28, Color.red(c), Color.green(c), Color.blue(c)));
        d.setCornerRadius(Ui.dp(this, 20));
        d.setStroke(Ui.dp(this, 1), Color.argb(90, Color.red(c), Color.green(c), Color.blue(c)));
        statusPill.setBackground(d);
        subtitle.setText(L.t("Android · 电池与充电", "Android · battery & charging")
                + (SessionStore.active ? " · " + L.t("本次充入电量 ", "energy added ") + Fmt.wh(SessionStore.wh) : ""));
    }

    @Override
    protected void onResume() {
        super.onResume();
        handler.removeCallbacks(ticker);
        handler.post(ticker);
    }

    @Override
    protected void onPause() {
        super.onPause();
        handler.removeCallbacks(ticker);
    }
}





