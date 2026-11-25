import Foundation
import SwiftUI

struct HistoryPoint: Identifiable, Sendable {
    var id = UUID()
    var time: Date
    var cpu: Double
    var memRatio: Double
    var gpu: Double
    var down: Double
    var up: Double
    var diskRead: Double
    var diskWrite: Double
    var netTotal: Double
    var cpuTemp: Double
    var gpuTemp: Double
    var power: Double
}


enum Page: String, CaseIterable, Identifiable {
    case overview = "概览"
    case cpu = "处理器"
    case memory = "内存"
    case thermal = "温度与功耗"
    case network = "网络"
    case disk = "磁盘"
    case settings = "设置"
    case about = "关于"

    var id: String { rawValue }

    var icon: String {
        switch self {
        case .overview: return "square.grid.2x2"
        case .cpu: return "cpu"
        case .memory: return "memorychip"
        case .thermal: return "thermometer.medium"
        case .network: return "wifi.router"
        case .disk: return "internaldrive"
        case .settings: return "slider.horizontal.3"
        case .about: return "info.circle"
        }
    }
}

@MainActor
final class AppModel: ObservableObject {
    @Published var snap = Snapshot()
    @Published var info = SystemInfo()
    @Published var history: [HistoryPoint] = []
    @Published var page: Page = .overview
    @Published var interval: Double = 1.0
    @Published var paused = false
    @Published var helperBusy = false
    @Published var helperMessage: String? = nil
    @Published var language: String = Localizer.shared.code

    private let engine = MetricsEngine()
    private var timer: Timer?
    private let maxPoints = 180

    init() {
        refreshInfo()
        restartTimer()
    }

    func refreshInfo() {
        Task.detached(priority: .utility) {
            let i = SystemInfo.collect()
            await MainActor.run { self.info = i }
        }
    }

    func setInterval(_ v: Double) {
        interval = v
        restartTimer()
    }

    func restartTimer() {
        timer?.invalidate()
        let t = Timer(timeInterval: interval, repeats: true) { [weak self] _ in
            Task { @MainActor in self?.tick() }
        }
        t.tolerance = interval * 0.15
        RunLoop.main.add(t, forMode: .common)
        timer = t
        tick()
    }

    private func tick() {
        guard !paused else { return }
        Task.detached(priority: .utility) { [engine] in
            let s = engine.sample()
            await MainActor.run { self.apply(s) }
        }
    }

    func setLanguage(_ code: String) {
        guard code != language else { return }
        Localizer.shared.set(code)
        language = code
    }

    func installHelper() {
        guard !helperBusy else { return }
        helperBusy = true
        Task.detached(priority: .userInitiated) {
            let r = HelperInstaller.install()
            await MainActor.run {
                self.helperBusy = false
                if !r.0 { self.helperMessage = r.1 }
                self.restartTimer()
            }
        }
    }

    func uninstallHelper() {
        guard !helperBusy else { return }
        helperBusy = true
        Task.detached(priority: .userInitiated) {
            let r = HelperInstaller.uninstall()
            await MainActor.run {
                self.helperBusy = false
                if !r.0 { self.helperMessage = r.1 }
            }
        }
    }

    private func apply(_ s: Snapshot) {
        snap = s
        let memRatio = s.mem.total > 0 ? Double(s.mem.used) / Double(s.mem.total) : 0
        history.append(HistoryPoint(time: s.time,
                                    cpu: s.cpuTotal,
                                    memRatio: memRatio * 100,
                                    gpu: s.gpuUtil,
                                    down: s.downBps,
                                    up: s.upBps,
                                    diskRead: s.diskReadBps,
                                    diskWrite: s.diskWriteBps,
                                    netTotal: s.downBps + s.upBps,
                                    cpuTemp: s.sensors.cpuTemp ?? 0,
                                    gpuTemp: s.sensors.gpuTemp ?? 0,
                                    power: s.sensors.combinedPower ?? 0))
        if history.count > maxPoints { history.removeFirst(history.count - maxPoints) }
    }
}
