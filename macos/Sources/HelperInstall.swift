import Foundation

enum HelperInstaller {
    static let label = "com.nesoncalo.hardwaremaster.helper"
    static let installedBinary = "/Library/PrivilegedHelperTools/\(label)"
    static let installedPlist = "/Library/LaunchDaemons/\(label).plist"
    static let runDir = "/var/run/hardwaremaster"
    static let metricsPath = "/var/run/hardwaremaster/metrics.json"

    static var isInstalled: Bool {
        FileManager.default.fileExists(atPath: installedBinary) &&
        FileManager.default.fileExists(atPath: installedPlist)
    }

    static var isRunning: Bool {
        guard let attrs = try? FileManager.default.attributesOfItem(atPath: metricsPath),
              let mod = attrs[.modificationDate] as? Date else { return false }
        return Date().timeIntervalSince(mod) < 5
    }

    private static func runScript(_ body: String) -> (Bool, String) {
        let scriptPath = "/tmp/hardwaremaster-helper-action.sh"
        do {
            try ("#!/bin/sh\nset -e\n" + body).write(toFile: scriptPath, atomically: true, encoding: .utf8)
            try FileManager.default.setAttributes([.posixPermissions: 0o700], ofItemAtPath: scriptPath)
        } catch {
            return (false, error.localizedDescription)
        }

        let p = Process()
        p.executableURL = URL(fileURLWithPath: "/usr/bin/osascript")
        p.arguments = ["-e", "do shell script \"/bin/sh \(scriptPath)\" with administrator privileges"]
        let pipe = Pipe()
        p.standardOutput = pipe
        p.standardError = pipe
        do {
            try p.run()
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            p.waitUntilExit()
            let out = String(data: data, encoding: .utf8) ?? ""
            if p.terminationStatus == 0 { return (true, out) }
            let msg = out.trimmingCharacters(in: .whitespacesAndNewlines)
            if msg.contains("-128") || msg.lowercased().contains("cancel") {
                return (false, "已取消授权")
            }
            return (false, msg.isEmpty ? "授权或安装失败（\(p.terminationStatus)）" : msg)
        } catch {
            return (false, error.localizedDescription)
        }
    }

    static func install() -> (Bool, String) {
        guard let helper = Bundle.main.url(forResource: "hardwaremaster-helper", withExtension: nil)?.path,
              let plist = Bundle.main.url(forResource: "helper", withExtension: "plist")?.path else {
            return (false, "安装资源缺失，请重新下载完整安装包")
        }
        let body = """
        /bin/mkdir -p /Library/PrivilegedHelperTools "\(runDir)"
        /bin/cp "\(helper)" "\(installedBinary)"
        /usr/sbin/chown root:wheel "\(installedBinary)"
        /bin/chmod 755 "\(installedBinary)"
        /bin/cp "\(plist)" "\(installedPlist)"
        /usr/sbin/chown root:wheel "\(installedPlist)"
        /bin/chmod 644 "\(installedPlist)"
        /bin/launchctl bootout system/\(label) >/dev/null 2>&1 || true
        /bin/launchctl bootstrap system "\(installedPlist)"
        /bin/launchctl kickstart -k system/\(label) >/dev/null 2>&1 || true
        """
        let r = runScript(body)
        if r.0 {
            // 等助手写出第一份数据
            for _ in 0..<20 {
                if isRunning { break }
                Thread.sleep(forTimeInterval: 0.2)
            }
        }
        return r
    }

    static func uninstall() -> (Bool, String) {
        let body = """
        /bin/launchctl bootout system/\(label) >/dev/null 2>&1 || true
        /bin/rm -f "\(installedPlist)"
        /bin/rm -f "\(installedBinary)"
        /bin/rm -rf "\(runDir)"
        """
        return runScript(body)
    }
}
