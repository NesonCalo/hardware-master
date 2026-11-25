package com.nesoncalo.hardwaremaster;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.res.ColorStateList;
import android.os.Build;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.Switch;
import android.widget.TextView;

/** 设置：语言、设计容量、提醒、后台监控、关于。 */
public class SettingsPage extends Page {

    private EditText designInput;
    private TextView designHint;

    public SettingsPage(MainActivity a) {
        super(a);
        buildLanguage();
        buildCapacity();
        buildAlerts();
        buildBackground();
        buildAbout();
    }

    private void buildLanguage() {
        LinearLayout card = Ui.card(c);
        card.addView(Ui.sectionTitle(c, L.t("界面语言", "Language")));
        TextView cur = Ui.button(c, langLabel(), Ui.ACCENT, true);
        cur.setOnClickListener(v -> pickLanguage());
        card.addView(cur);
        card.addView(Ui.gap(c, 8));
        card.addView(Ui.text(c, L.t("25 种语言，随时可切换。", "25 languages, switch anytime."), 11, Ui.FAINT));
        addWithBottom(card, 12);
    }

    private String langLabel() {
        String saved = Prefs.getLang(c);
        if ("auto".equals(saved) || saved.isEmpty()) {
            return L.t("跟随系统", "System") + " · " + L.displayName(L.currentTag());
        }
        return L.displayName(saved);
    }

    private void pickLanguage() {
        String[] labels = new String[L.TAGS.length + 1];
        labels[0] = L.t("跟随系统", "System") + " · " + L.displayName(L.deviceTagPublic());
        for (int i = 0; i < L.TAGS.length; i++) labels[i + 1] = L.NAMES[i];
        new android.app.AlertDialog.Builder(c, android.R.style.Theme_DeviceDefault_Dialog_Alert)
                .setTitle(L.t("选择界面语言", "Choose language"))
                .setItems(labels, (d, w) -> {
                    Prefs.setLang(c, w == 0 ? "auto" : L.TAGS[w - 1]);
                    L.init(c);
                    act.recreate();
                })
                .show();
    }

    private void buildCapacity() {
        LinearLayout card = Ui.card(c);
        card.addView(Ui.sectionTitle(c, L.t("电池设计容量", "Design capacity")));
        card.addView(Ui.text(c, L.t("系统读不到标称容量时，填入官网参数可让损耗估算更准。",
                "If the system hides the rated capacity, enter the official value for a better wear estimate."), 11, Ui.FAINT));
        card.addView(Ui.gap(c, 10));

        LinearLayout row = Ui.row(c);
        designInput = new EditText(c);
        designInput.setInputType(InputType.TYPE_CLASS_NUMBER);
        designInput.setTextColor(Ui.TEXT);
        designInput.setHintTextColor(Ui.FAINT);
        designInput.setHint(L.t("例如 5000", "e.g. 5000"));
        designInput.setTextSize(14);
        designInput.setPadding(Ui.dp(c, 12), Ui.dp(c, 10), Ui.dp(c, 12), Ui.dp(c, 10));
        designInput.setBackground(Ui.roundStroke(Ui.CARD_SOFT, 12, Ui.STROKE, c));
        int saved = Prefs.getDesignMah(c);
        if (saved > 0) designInput.setText(String.valueOf(saved));
        row.addView(designInput, new LinearLayout.LayoutParams(0, -2, 1f));
        row.addView(Ui.hgap(c, 8));
        TextView save = Ui.button(c, L.t("保存", "Save"), Ui.ACCENT, true);
        save.setOnClickListener(v -> {
            String s = designInput.getText().toString().trim();
            int v2 = 0;
            try {
                v2 = Integer.parseInt(s);
            } catch (Throwable ignored) {}
            if (v2 > 100 && v2 < 20000) {
                Prefs.setDesignMah(c, v2);
                designHint.setText(L.t("已保存 ", "Saved ") + v2 + " mAh");
                designHint.setTextColor(Ui.GREEN);
            } else {
                designHint.setText(L.t("请输入 100–20000 之间的数值", "Enter a value between 100 and 20000"));
                designHint.setTextColor(Ui.RED);
            }
        });
        row.addView(save);
        card.addView(row);

        card.addView(Ui.gap(c, 8));
        designHint = Ui.text(c, L.t("单位 mAh，只影响损耗估算，不会修改系统。",
                "Unit mAh; only affects the wear estimate."), 11, Ui.FAINT);
        card.addView(designHint);
        addWithBottom(card, 12);
    }

    private void buildAlerts() {
        LinearLayout card = Ui.card(c);
        card.addView(Ui.sectionTitle(c, L.t("充电提醒", "Charging alerts")));
        card.addView(switchRow(L.t("充到 80% 提醒", "Alert at 80%"),
                L.t("日常充电到 80% 就可以拔线", "Unplug around 80% for daily use"),
                Prefs.alert80(c), v -> Prefs.setAlert80(c, v)));
        card.addView(switchRow(L.t("电池高温提醒", "High temperature alert"),
                L.t("超过 43℃ 时提醒降温", "Remind when above 43℃"),
                Prefs.alertTemp(c), v -> Prefs.setAlertTemp(c, v)));
        card.addView(switchRow(L.t("充电偏慢提醒", "Slow charging alert"),
                L.t("功率低于 5W 时提醒检查线材", "Remind when power is below 5W"),
                Prefs.alertSlow(c), v -> Prefs.setAlertSlow(c, v)));
        addWithBottom(card, 12);
    }

    private void buildBackground() {
        LinearLayout card = Ui.card(c);
        card.addView(Ui.sectionTitle(c, L.t("后台充电监控", "Background monitor")));
        card.addView(Ui.text(c, L.t("开启后常驻一条通知，每 30 秒采样一次，闭屏也能累计会话与提醒。",
                "Keeps a notification and samples every 30 seconds, even with the screen off."), 11, Ui.FAINT));
        card.addView(Ui.gap(c, 8));
        card.addView(switchRow(L.t("充电时后台监控", "Monitor in background"),
                L.t("仅读取电量与充电数据，不联网", "Reads battery data only, no network"),
                Prefs.bgMonitor(c), v -> {
            Prefs.setBgMonitor(c, v);
            if (v) startMonitor(); else stopMonitor();
        }));
        addWithBottom(card, 12);
    }

    private void startMonitor() {
        if (Build.VERSION.SDK_INT >= 33
                && c.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            act.requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 101);
        }
        Intent i = new Intent(c, ChargingService.class);
        if (Build.VERSION.SDK_INT >= 26) c.startForegroundService(i); else c.startService(i);
    }

    private void stopMonitor() {
        c.stopService(new Intent(c, ChargingService.class));
    }

    private void buildAbout() {
        LinearLayout card = Ui.card(c);
        card.addView(Ui.sectionTitle(c, L.t("关于", "About")));
        kvRow(card, L.t("版本", "Version"), "1.2.0 (Build 13)");
        kvRow(card, L.t("包名", "Package"), "com.nesoncalo.hardwaremaster");
        kvRow(card, L.t("设备", "Device"), BatteryReader.deviceSummary());
        kvRow(card, L.t("系统", "Android"), "API " + Build.VERSION.SDK_INT);
        card.addView(Ui.divider(c));
        TextView p = Ui.text(c, L.t(
                "所有读数来自 BatteryManager、ACTION_BATTERY_CHANGED 与 /sys/class/power_supply，只在本机计算；没有账号、没有联网上报、没有广告。",
                "All readings come from BatteryManager, ACTION_BATTERY_CHANGED and /sys/class/power_supply and are computed on-device. No account, no telemetry, no ads."), 11, Ui.FAINT);
        p.setLineSpacing(Ui.dp(c, 3), 1f);
        card.addView(p);
        add(card);
    }

    private TextView kvRow(LinearLayout card, String label, String value) {
        LinearLayout row = Ui.row(c);
        row.addView(Ui.text(c, label, 12, Ui.SUB), new LinearLayout.LayoutParams(0, -2, 1f));
        TextView v = Ui.boldText(c, value, 12, Ui.TEXT);
        v.setGravity(Gravity.END);
        row.addView(v);
        card.addView(row);
        card.addView(Ui.gap(c, 8));
        return v;
    }

    private LinearLayout switchRow(String label, String desc, boolean checked, SwitchListener listener) {
        LinearLayout row = Ui.row(c);
        LinearLayout texts = Ui.column(c);
        texts.addView(Ui.text(c, label, 13, Ui.TEXT));
        texts.addView(Ui.gap(c, 3));
        texts.addView(Ui.text(c, desc, 11, Ui.FAINT));
        row.addView(texts, new LinearLayout.LayoutParams(0, -2, 1f));

        Switch sw = new Switch(c);
        sw.setChecked(checked);
        sw.setThumbTintList(ColorStateList.valueOf(checked ? Ui.ACCENT : 0xFF6A7A90));
        sw.setTrackTintList(ColorStateList.valueOf(0x3329C6E8));
        sw.setOnCheckedChangeListener((buttonView, isChecked) -> {
            sw.setThumbTintList(ColorStateList.valueOf(isChecked ? Ui.ACCENT : 0xFF6A7A90));
            listener.onChanged(isChecked);
        });
        row.addView(sw);
        LinearLayout wrap = Ui.column(c);
        wrap.addView(row);
        wrap.addView(Ui.gap(c, 10));
        return wrap;
    }

    interface SwitchListener {
        void onChanged(boolean checked);
    }
}





