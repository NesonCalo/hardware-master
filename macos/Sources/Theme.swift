import SwiftUI

extension Color {
    init(hex: UInt32, alpha: Double = 1.0) {
        let r = Double((hex >> 16) & 0xFF) / 255
        let g = Double((hex >> 8) & 0xFF) / 255
        let b = Double(hex & 0xFF) / 255
        self.init(.sRGB, red: r, green: g, blue: b, opacity: alpha)
    }
}

enum Palette {
    static let bgTop = Color(hex: 0x0A0F1C)
    static let bgBottom = Color(hex: 0x05070D)
    static let panel = Color(hex: 0x121A2B)
    static let panelSoft = Color(hex: 0x182238)
    static let stroke = Color.white.opacity(0.08)
    static let textPrimary = Color(hex: 0xEDF2FF)
    static let textSecondary = Color(hex: 0x8E9BB5)
    static let cyan = Color(hex: 0x35D6FF)
    static let purple = Color(hex: 0x9B8CFF)
    static let green = Color(hex: 0x43E0A0)
    static let orange = Color(hex: 0xFFB35C)
    static let red = Color(hex: 0xFF6B7A)
    static let pink = Color(hex: 0xFF7AC6)

    static func levelColor(_ v: Double) -> Color {
        if v >= 85 { return red }
        if v >= 60 { return orange }
        return cyan
    }
}

struct CardShell<Content: View>: View {
    var title: String? = nil
    var subtitle: String? = nil
    var accent: Color = Palette.cyan
    @ViewBuilder var content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            if let title {
                HStack(spacing: 8) {
                    RoundedRectangle(cornerRadius: 2)
                        .fill(accent)
                        .frame(width: 3, height: 13)
                    Text(title)
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundStyle(Palette.textPrimary)
                    if let subtitle {
                        Text(subtitle)
                            .font(.system(size: 11))
                            .foregroundStyle(Palette.textSecondary)
                    }
                    Spacer()
                }
            }
            content
        }
        .padding(16)
        .background(
            RoundedRectangle(cornerRadius: 16, style: .continuous)
                .fill(Palette.panel.opacity(0.78))
                .overlay(
                    RoundedRectangle(cornerRadius: 16, style: .continuous)
                        .stroke(Palette.stroke, lineWidth: 1)
                )
        )
    }
}

struct BigNumber: View {
    var value: String
    var unit: String = ""
    var color: Color = Palette.textPrimary
    var size: CGFloat = 26

    var body: some View {
        HStack(alignment: .firstTextBaseline, spacing: 3) {
            Text(value)
                .font(.system(size: size, weight: .semibold, design: .rounded))
                .foregroundStyle(color)
                .monospacedDigit()
            if !unit.isEmpty {
                Text(unit)
                    .font(.system(size: 11, weight: .medium))
                    .foregroundStyle(Palette.textSecondary)
            }
        }
    }
}

struct RingGauge: View {
    var value: Double          // 0...100
    var color: Color
    var label: String
    var caption: String
    var lineWidth: CGFloat = 8
    var size: CGFloat = 116

    var body: some View {
        ZStack {
            Circle()
                .stroke(Color.white.opacity(0.06), lineWidth: lineWidth)
            Circle()
                .trim(from: 0, to: min(1, max(0, value / 100)))
                .stroke(
                    AngularGradient(colors: [color.opacity(0.55), color], center: .center),
                    style: StrokeStyle(lineWidth: lineWidth, lineCap: .round)
                )
                .rotationEffect(.degrees(-90))
                .animation(.easeOut(duration: 0.4), value: value)
            VStack(spacing: 2) {
                Text("\(Int(value))")
                    .font(.system(size: 24, weight: .semibold, design: .rounded))
                    .foregroundStyle(Palette.textPrimary)
                    .monospacedDigit()
                Text(label)
                    .font(.system(size: 10))
                    .foregroundStyle(Palette.textSecondary)
            }
        }
        .frame(width: size, height: size)
        .overlay(alignment: .bottom) {
            Text(caption)
                .font(.system(size: 10))
                .foregroundStyle(Palette.textSecondary)
                .offset(y: 18)
        }
    }
}

struct KVRow: View {
    var key: String
    var value: String
    var mono: Bool = false

    var body: some View {
        HStack(alignment: .top) {
            Text(key)
                .font(.system(size: 12))
                .foregroundStyle(Palette.textSecondary)
            Spacer(minLength: 12)
            Text(value)
                .font(.system(size: 12, weight: .medium, design: mono ? .monospaced : .default))
                .foregroundStyle(Palette.textPrimary)
                .multilineTextAlignment(.trailing)
                .lineLimit(2)
                .truncationMode(.middle)
        }
    }
}

struct BarLine: View {
    var ratio: Double
    var color: Color
    var height: CGFloat = 6

    var body: some View {
        GeometryReader { geo in
            ZStack(alignment: .leading) {
                Capsule().fill(Color.white.opacity(0.06))
                Capsule()
                    .fill(LinearGradient(colors: [color.opacity(0.6), color], startPoint: .leading, endPoint: .trailing))
                    .frame(width: max(2, geo.size.width * min(1, max(0, ratio))))
            }
        }
        .frame(height: height)
    }
}

// MARK: - 格式化

enum Fmt {
    static func bytes(_ v: Double) -> String {
        let units = ["B", "KB", "MB", "GB", "TB"]
        var value = v
        var idx = 0
        while value >= 1024 && idx < units.count - 1 { value /= 1024; idx += 1 }
        if idx == 0 { return String(format: "%.0f %@", value, units[idx]) }
        return String(format: value >= 100 ? "%.0f %@" : "%.1f %@", value, units[idx])
    }

    static func bytesU(_ v: UInt64) -> String { bytes(Double(v)) }

    static func rate(_ v: Double) -> String { bytes(v) + "/s" }

    static func mem(_ v: UInt64) -> String {
        let gb = Double(v) / 1_073_741_824
        if gb >= 1 { return String(format: "%.1f GB", gb) }
        return String(format: "%.0f MB", Double(v) / 1_048_576)
    }

    static func uptime(_ t: TimeInterval) -> String {
        let total = Int(t)
        let d = total / 86400, h = (total % 86400) / 3600, m = (total % 3600) / 60
        if d > 0 { return "\(d) \(T("天")) \(h) \(T("小时"))" }
        if h > 0 { return "\(h) \(T("小时")) \(m) \(T("分"))" }
        return "\(m) \(T("分钟"))"
    }

    static func time(_ d: Date) -> String {
        let f = DateFormatter()
        f.locale = Locale(identifier: "en_US_POSIX")
        f.dateFormat = "HH:mm:ss"
        return f.string(from: d)
    }
}
