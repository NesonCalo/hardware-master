package com.nesoncalo.hardwaremaster;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;

/** 后台充电监控：常驻通知 + 30 秒采样 + 80% / 高温 / 慢充提醒。 */
public class ChargingService extends Service {

    private static final int NOTIF_ONGOING = 1;
    private static final int NOTIF_ALERT = 2;
    private static final String CH_ONGOING = "hm_charging";
    private static final String CH_ALERT = "hm_alerts";

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final BatteryReader reader = new BatteryReader();

    private boolean alerted80;
    private boolean alertedTemp;
    private boolean alertedSlow;
    private boolean wasCharging;

    private final Runnable tick = new Runnable() {
        @Override
        public void run() {
            try {
                reader.read(ChargingService.this);
                SessionStore.tick(ChargingService.this, reader);
                updateNotification();
                checkAlerts();
            } catch (Throwable ignored) {}
            handler.postDelayed(this, 30000);
        }
    };

    @Override
    public void onCreate() {
        super.onCreate();
        createChannels();
        reader.read(this);
        startInForeground();
        handler.post(tick);
    }

    private void startInForeground() {
        Notification n = buildOngoing();
        if (Build.VERSION.SDK_INT >= 34) {
            startForeground(NOTIF_ONGOING, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE);
        } else {
            startForeground(NOTIF_ONGOING, n);
        }
    }

    private void createChannels() {
        if (Build.VERSION.SDK_INT < 26) return;
        NotificationManager nm = getSystemService(NotificationManager.class);
        NotificationChannel ongoing = new NotificationChannel(CH_ONGOING,
                L.t("充电监控", "Charging monitor"), NotificationManager.IMPORTANCE_LOW);
        ongoing.setShowBadge(false);
        NotificationChannel alerts = new NotificationChannel(CH_ALERT,
                L.t("充电提醒", "Charging alerts"), NotificationManager.IMPORTANCE_HIGH);
        nm.createNotificationChannel(ongoing);
        nm.createNotificationChannel(alerts);
    }

    private PendingIntent openApp() {
        Intent i = new Intent(this, MainActivity.class);
        i.setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        int flags = PendingIntent.FLAG_UPDATE_CURRENT;
        if (Build.VERSION.SDK_INT >= 23) flags |= PendingIntent.FLAG_IMMUTABLE;
        return PendingIntent.getActivity(this, 0, i, flags);
    }

    private Notification buildOngoing() {
        String title = reader.charging
                ? L.t("充电中 ", "Charging ") + reader.level + "%"
                : L.t("使用电池 ", "On battery ") + reader.level + "%";
        String text = reader.charging
                ? Fmt.watts(Math.abs(reader.powerW)) + "  ·  " + reader.statusText()
                + (SessionStore.active ? "  ·  " + Fmt.wh(SessionStore.wh) : "")
                : reader.statusText() + (reader.tempC > 0 ? "  ·  " + Fmt.temp(reader.tempC) : "");
        Notification.Builder b = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(this, CH_ONGOING)
                : new Notification.Builder(this);
        b.setSmallIcon(android.R.drawable.ic_lock_idle_charging)
                .setContentTitle(title)
                .setContentText(text)
                .setContentIntent(openApp())
                .setOngoing(true)
                .setOnlyAlertOnce(true);
        if (Build.VERSION.SDK_INT >= 21) b.setShowWhen(false);
        return b.build();
    }

    private void updateNotification() {
        NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        nm.notify(NOTIF_ONGOING, buildOngoing());
    }

    private void checkAlerts() {
        if (!reader.charging) {
            alerted80 = false;
            alertedTemp = false;
            alertedSlow = false;
            wasCharging = false;
            return;
        }
        if (!wasCharging) {
            alerted80 = reader.level >= 80;
            alertedTemp = reader.tempC >= Prefs.tempLimit(this);
            alertedSlow = false;
            wasCharging = true;
        }
        if (!alerted80 && Prefs.alert80(this) && reader.level >= 80) {
            alerted80 = true;
            alert(L.t("已经充到 80%", "Reached 80%"),
                    L.t("日常使用可以把线拔了，减少满电停留。", "Unplug for daily use to avoid sitting at full charge."));
        }
        if (!alertedTemp && Prefs.alertTemp(this) && reader.tempC >= Prefs.tempLimit(this)) {
            alertedTemp = true;
            alert(L.t("电池温度偏高", "Battery is warm"),
                    L.t("当前 ", "Now ") + Fmt.temp(reader.tempC) + L.t("，建议摘掉保护壳或暂停充电。", " — remove the case or pause charging."));
        }
        if (!alertedSlow && Prefs.alertSlow(this) && reader.level < 95
                && Math.abs(reader.powerW) < 5 && reader.currentMa > 0) {
            alertedSlow = true;
            alert(L.t("充电速度偏慢", "Slow charging"),
                    L.t("当前功率 ", "Power ") + Fmt.watts(Math.abs(reader.powerW)) + L.t("，检查线材与接口。", " — check cable and port."));
        }
    }

    private void alert(String title, String text) {
        Notification.Builder b = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(this, CH_ALERT)
                : new Notification.Builder(this);
        b.setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentTitle(title)
                .setContentText(text)
                .setContentIntent(openApp())
                .setAutoCancel(true);
        NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        nm.notify(NOTIF_ALERT, b.build());
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        return START_STICKY;
    }

    @Override
    public void onDestroy() {
        handler.removeCallbacks(tick);
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}




