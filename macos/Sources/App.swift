import SwiftUI
import AppKit

final class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
        NSApp.activate(ignoringOtherApps: true)
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
}

#if !SNAPSHOT
@main
struct HardwareMasterApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var delegate

    var body: some Scene {
        WindowGroup(T("硬件管理大师")) {
            ContentView()
                .frame(minWidth: 1060, minHeight: 700)
                .preferredColorScheme(.dark)
        }
        .windowStyle(.hiddenTitleBar)
        .windowResizability(.contentMinSize)
        .defaultSize(width: 1280, height: 840)
        .commands {
            CommandGroup(replacing: .newItem) {}
        }
    }
}
#endif

struct ContentView: View {
    @StateObject private var model = AppModel()

    var body: some View {
        MainLayout(model: model)
            .id(model.language)
    }
}

struct MainLayout: View {
    @ObservedObject var model: AppModel

    var body: some View {
        HStack(spacing: 0) {
            Sidebar(model: model)
            ZStack {
                Palette.bgTop
                LinearGradient(colors: [Palette.bgTop, Palette.bgBottom], startPoint: .topLeading, endPoint: .bottomTrailing)
                RadialGradient(colors: [Palette.cyan.opacity(0.07), .clear], center: .topLeading, startRadius: 10, endRadius: 620)
                RadialGradient(colors: [Palette.purple.opacity(0.06), .clear], center: .bottomTrailing, startRadius: 10, endRadius: 700)

                ScrollView {
                    pageContent
                        .padding(.horizontal, 22)
                        .padding(.top, 18)
                        .padding(.bottom, 28)
                }
                .scrollIndicators(.never)
            }
            .ignoresSafeArea()
        }
        .background(Palette.bgBottom)
    }

    @ViewBuilder
    private var pageContent: some View {
        switch model.page {
        case .overview: OverviewView(model: model)
        case .cpu: CPUView(model: model)
        case .memory: MemoryView(model: model)
        case .thermal: ThermalView(model: model)
        case .network: NetworkView(model: model)
        case .disk: DiskView(model: model)
        case .settings: SettingsView(model: model)
        case .about: AboutView(model: model)
        }
    }
}

struct Sidebar: View {
    @ObservedObject var model: AppModel

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack(spacing: 10) {
                ZStack {
                    RoundedRectangle(cornerRadius: 10, style: .continuous)
                        .fill(LinearGradient(colors: [Palette.cyan, Palette.purple], startPoint: .topLeading, endPoint: .bottomTrailing))
                    Image(systemName: "memorychip.fill")
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundStyle(.white)
                }
                .frame(width: 34, height: 34)

                VStack(alignment: .leading, spacing: 1) {
                    Text(T("硬件管理大师"))
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundStyle(Palette.textPrimary)
                    Text("Hardware Master")
                        .font(.system(size: 10))
                        .foregroundStyle(Palette.textSecondary)
                }
            }
            .padding(.horizontal, 16)
            .padding(.top, 42)
            .padding(.bottom, 18)

            Text(T("监控"))
                .font(.system(size: 10, weight: .medium))
                .foregroundStyle(Palette.textSecondary.opacity(0.7))
                .tracking(1.5)
                .padding(.horizontal, 20)
                .padding(.bottom, 6)

            ForEach([Page.overview, .cpu, .memory, .thermal, .network, .disk]) { p in
                SidebarItem(page: p, selected: model.page == p) {
                    withAnimation(.easeInOut(duration: 0.18)) { model.page = p }
                }
            }

            Spacer(minLength: 12)

            Text(T("其它"))
                .font(.system(size: 10, weight: .medium))
                .foregroundStyle(Palette.textSecondary.opacity(0.7))
                .tracking(1.5)
                .padding(.horizontal, 20)
                .padding(.bottom, 6)

            ForEach([Page.settings, .about]) { p in
                SidebarItem(page: p, selected: model.page == p) {
                    withAnimation(.easeInOut(duration: 0.18)) { model.page = p }
                }
            }

            Divider().overlay(Palette.stroke).padding(.horizontal, 16).padding(.vertical, 12)

            VStack(alignment: .leading, spacing: 6) {
                HStack(spacing: 6) {
                    Circle()
                        .fill(model.paused ? Palette.orange : Palette.green)
                        .frame(width: 6, height: 6)
                    Text(model.paused ? T("已暂停") : T("实时采集中"))
                        .font(.system(size: 11))
                        .foregroundStyle(Palette.textSecondary)
                }
                Text(TF("采样间隔 %d 秒 · 全部本地", Int(model.interval)))
                    .font(.system(size: 10))
                    .foregroundStyle(Palette.textSecondary.opacity(0.75))
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 18)
        }
        .frame(width: 208)
        .background(Palette.panel.opacity(0.55))
        .overlay(alignment: .trailing) {
            Rectangle().fill(Palette.stroke).frame(width: 1)
        }
    }
}

struct SidebarItem: View {
    let page: Page
    let selected: Bool
    let action: () -> Void
    @State private var hover = false

    var body: some View {
        Button(action: action) {
            HStack(spacing: 10) {
                Image(systemName: page.icon)
                    .font(.system(size: 13, weight: .medium))
                    .frame(width: 18)
                    .foregroundStyle(selected ? Palette.cyan : Palette.textSecondary)
                Text(T(page.rawValue))
                    .font(.system(size: 12, weight: selected ? .semibold : .regular))
                    .foregroundStyle(selected ? Palette.textPrimary : Palette.textSecondary)
                Spacer()
            }
            .padding(.vertical, 8)
            .padding(.horizontal, 12)
            .background(
                RoundedRectangle(cornerRadius: 9, style: .continuous)
                    .fill(selected ? Palette.cyan.opacity(0.12) : (hover ? Color.white.opacity(0.04) : .clear))
            )
            .overlay(alignment: .leading) {
                if selected {
                    RoundedRectangle(cornerRadius: 2)
                        .fill(Palette.cyan)
                        .frame(width: 2.5, height: 16)
                        .padding(.leading, 3)
                }
            }
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .padding(.horizontal, 10)
        .onHover { hover = $0 }
    }
}
