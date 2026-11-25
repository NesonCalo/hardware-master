import AppKit
import SwiftUI

@main
struct SnapshotMain {
    @MainActor
    static func main() {
        let app = NSApplication.shared
        app.setActivationPolicy(.accessory)

        let model = AppModel()
        let wait = Double(ProcessInfo.processInfo.environment["HM_SNAP_WAIT"] ?? "") ?? 2.6
        RunLoop.main.run(until: Date().addingTimeInterval(wait))

        let pages: [Page] = [.overview, .cpu, .memory, .thermal, .network, .disk, .settings, .about]
        for p in pages {
            model.page = p
            RunLoop.main.run(until: Date().addingTimeInterval(0.4))
            render(model: model, page: p)
        }
        exit(0)
    }

    @MainActor
    static func render(model: AppModel, page: Page) {
        let size = NSSize(width: 1280, height: 840)
        let root = MainLayout(model: model)
            .frame(width: size.width, height: size.height)
            .preferredColorScheme(.dark)
        let host = NSHostingView(rootView: root)
        host.frame = NSRect(origin: .zero, size: size)

        let window = NSWindow(contentRect: NSRect(x: -3000, y: -3000, width: size.width, height: size.height),
                              styleMask: [.borderless],
                              backing: .buffered,
                              defer: false)
        window.contentView = host
        window.orderFrontRegardless()
        host.layoutSubtreeIfNeeded()
        window.displayIfNeeded()
        RunLoop.main.run(until: Date().addingTimeInterval(0.5))

        guard let rep = host.bitmapImageRepForCachingDisplay(in: host.bounds) else {
            print("no rep for \(page.rawValue)")
            window.close()
            return
        }
        host.cacheDisplay(in: host.bounds, to: rep)
        if let data = rep.representation(using: .png, properties: [:]) {
            let path = "/tmp/snap_\(page.rawValue).png"
            try? data.write(to: URL(fileURLWithPath: path))
            print("written \(path) \(rep.pixelsWide)x\(rep.pixelsHigh)")
        }
        window.close()
    }
}
