package com.nesoncalo.hardwaremaster;

import android.content.Context;
import android.content.res.AssetManager;

import org.json.JSONObject;

import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;

/** 多语言：中文原文为 key，25 种语言资源放在 assets/i18n/<tag>.json。 */
public final class L {

    public static final String[] TAGS = {
            "zh-CN", "zh-TW", "zh-HK", "en", "ja", "ko", "de", "fr", "es", "pt-BR",
            "ru", "it", "nl", "pl", "sv", "tr", "uk", "ar", "fa", "hi",
            "bn", "th", "vi", "id", "ms"
    };

    public static final String[] NAMES = {
            "简体中文", "繁體中文（台灣）", "繁體中文（香港）", "English", "日本語", "한국어",
            "Deutsch", "Français", "Español", "Português (Brasil)", "Русский", "Italiano",
            "Nederlands", "Polski", "Svenska", "Türkçe", "Українська", "العربية",
            "فارسی", "हिन्दी", "বাংলা", "ไทย", "Tiếng Việt", "Bahasa Indonesia", "Bahasa Melayu"
    };

    private static String tag = "zh-CN";
    private static final Map<String, String> map = new HashMap<>();

    private L() {}

    public static void init(Context ctx) {
        String saved = Prefs.getLang(ctx);
        tag = "auto".equals(saved) || saved.isEmpty() ? deviceTag() : normalize(saved);
        load(ctx);
    }

    public static String currentTag() {
        return tag;
    }

    public static String displayName(String t) {
        if ("auto".equals(t)) return t;
        for (int i = 0; i < TAGS.length; i++) if (TAGS[i].equals(t)) return NAMES[i];
        return t;
    }

    public static String deviceTagPublic() {
        return deviceTag();
    }

    public static boolean isChinese() {
        return tag.startsWith("zh");
    }

    public static String t(String zh, String english) {
        if (isChinese()) {
            if ("zh-CN".equals(tag)) return zh;
            String v = map.get(zh);
            return v != null ? v : zh;
        }
        String v = map.get(zh);
        return v != null ? v : english;
    }

    /** 用完整文案作为翻译 key，但界面显示更短的写法。 */
    public static String tk(String key, String zh, String english) {
        String v = map.get(key);
        if (v != null) return v;
        return isChinese() ? zh : english;
    }

    private static String deviceTag() {
        Locale l = Locale.getDefault();
        String lang = l.getLanguage();
        String country = l.getCountry();
        if ("zh".equals(lang)) {
            if ("TW".equals(country)) return "zh-TW";
            if ("HK".equals(country) || "MO".equals(country)) return "zh-HK";
            return "zh-CN";
        }
        String full = country.isEmpty() ? lang : lang + "-" + country;
        for (String t : TAGS) if (t.equalsIgnoreCase(full)) return t;
        for (String t : TAGS) if (t.equals(lang)) return t;
        return "en";
    }

    private static String normalize(String saved) {
        if ("zh".equals(saved)) return "zh-CN";
        if ("en".equals(saved)) return "en";
        for (String t : TAGS) if (t.equals(saved)) return t;
        return deviceTag();
    }

    private static void load(Context ctx) {
        map.clear();
        if ("zh-CN".equals(tag) || "en".equals(tag)) return;
        try {
            AssetManager am = ctx.getAssets();
            InputStream in = am.open("i18n/" + tag + ".json");
            ByteArrayOutputStream bos = new ByteArrayOutputStream();
            byte[] buf = new byte[4096];
            int n;
            while ((n = in.read(buf)) > 0) bos.write(buf, 0, n);
            in.close();
            JSONObject obj = new JSONObject(new String(bos.toByteArray(), StandardCharsets.UTF_8));
            java.util.Iterator<String> it = obj.keys();
            while (it.hasNext()) {
                String k = it.next();
                map.put(k, obj.optString(k));
            }
        } catch (Throwable ignored) {
        }
    }
}




