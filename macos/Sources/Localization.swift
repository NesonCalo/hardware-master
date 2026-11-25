import Foundation

final class Localizer {
    static let shared = Localizer()

    static let languages: [(code: String, name: String)] = [
        ("en", "English"),
        ("zh-CN", "简体中文"),
        ("zh-TW", "繁體中文（台灣）"),
        ("zh-HK", "繁體中文（香港）"),
        ("ja", "日本語"),
        ("ko", "한국어"),
        ("de", "Deutsch"),
        ("fr", "Français"),
        ("es", "Español"),
        ("it", "Italiano"),
        ("pt-BR", "Português (Brasil)"),
        ("ru", "Русский"),
        ("uk", "Українська"),
        ("pl", "Polski"),
        ("nl", "Nederlands"),
        ("sv", "Svenska"),
        ("tr", "Türkçe"),
        ("ar", "العربية"),
        ("fa", "فارسی"),
        ("hi", "हिन्दी"),
        ("bn", "বাংলা"),
        ("th", "ไทย"),
        ("vi", "Tiếng Việt"),
        ("id", "Bahasa Indonesia"),
        ("ms", "Bahasa Melayu")
    ]

    private(set) var code: String
    private var table: [String: String] = [:]
    private var english: [String: String] = [:]
    private var extras: [String: [String: String]] = [:]

    private init() {
        if let env = ProcessInfo.processInfo.environment["HM_LANG"] {
            code = env
        } else {
            let saved = UserDefaults.standard.string(forKey: "appLanguage")
            code = saved ?? Localizer.systemDefaultCode()
        }
        load()
    }

    static func systemDefaultCode() -> String {
        for pref in Locale.preferredLanguages {
            let lower = pref.lowercased()
            if lower.hasPrefix("zh-hant") || lower.hasPrefix("zh-tw") || lower.hasPrefix("zh-hk") { return "zh-HK" }
            if lower.hasPrefix("zh") { return "zh-CN" }
            if let hit = languages.first(where: { lower.hasPrefix($0.code.lowercased()) }) { return hit.code }
        }
        return "en"
    }

    func set(_ newCode: String) {
        guard newCode != code else { return }
        code = newCode
        UserDefaults.standard.set(newCode, forKey: "appLanguage")
        load()
    }

    func t(_ key: String) -> String {
        table[key] ?? english[key] ?? key
    }

    func tf(_ key: String, _ args: [CVarArg]) -> String {
        let fmt = t(key)
        return String(format: fmt, arguments: args)
    }

    private func load() {
        english = loadBase("en")
        table = code == "en" ? english : loadBase(code)
        extras = loadExtras()
        for (key, values) in extras {
            if let v = values[code], !v.isEmpty {
                table[key] = v
            } else if code != "zh-CN", let v = values["en"], !v.isEmpty {
                table[key] = v
            }
        }
    }

    private func resourceDir() -> URL? {
        var candidates: [URL] = []
        let fm = FileManager.default
        if let r = Bundle.main.resourceURL { candidates.append(r.appendingPathComponent("locales")) }
        candidates.append(Bundle.main.bundleURL.appendingPathComponent("Contents/Resources/locales"))
        candidates.append(Bundle.main.bundleURL.appendingPathComponent("locales"))
        let exeDir = URL(fileURLWithPath: CommandLine.arguments[0]).deletingLastPathComponent()
        candidates.append(exeDir.appendingPathComponent("Resources/locales"))
        candidates.append(exeDir.appendingPathComponent("../Resources/locales").standardized)
        candidates.append(URL(fileURLWithPath: fm.currentDirectoryPath).appendingPathComponent("Resources/locales"))
        for c in candidates where fm.fileExists(atPath: c.path) { return c }
        return nil
    }

    private func loadBase(_ lang: String) -> [String: String] {
        guard let dir = resourceDir(),
              let data = try? Data(contentsOf: dir.appendingPathComponent("\(lang).json")),
              let obj = (try? JSONSerialization.jsonObject(with: data)) as? [String: String] else {
            return [:]
        }
        return obj
    }

    private func loadExtras() -> [String: [String: String]] {
        guard let dir = resourceDir(),
              let data = try? Data(contentsOf: dir.appendingPathComponent("macos-extra.json")),
              let obj = (try? JSONSerialization.jsonObject(with: data)) as? [String: [String: String]] else {
            return [:]
        }
        return obj
    }
}

/// 按当前界面语言取文案，key 为中文原文
func T(_ key: String) -> String { Localizer.shared.t(key) }

/// 带占位符的文案，例如 TF("近 %d 秒", 16)
func TF(_ key: String, _ args: CVarArg...) -> String { Localizer.shared.tf(key, args) }
