import SwiftUI
import Charts

// MARK: - 通用组件

struct PageHeader: View {
    var title: String
    var subtitle: String
    var trailing: String
    var accent: Color = Palette.cyan

    var body: some View {
        HStack(alignment: .center) {
            VStack(alignment: .leading, spacing: 3) {
                Text(title)
                    .font(.system(size: 22, weight: .bold))
                    .foregroundStyle(Palette.textPrimary)
                Text(subtitle)
                    .font(.system(size: 11))
                    .foregroundStyle(Palette.textSecondary)
            }
            Spacer()
            HStack(spacing: 6) {
                Circle().fill(accent.opacity(0.9)).frame(width: 5, height: 5)
                Text(trailing)
                    .font(.system(size: 11, weight: .medium, design: .monospaced))
                    .foregroundStyle(Palette.textSecondary)
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(RoundedRectangle(cornerRadius: 8).fill(Color.white.opacity(0.04)))
        }
    }
}

struct SparkChart: View {
    var points: [HistoryPoint]
    var value: (HistoryPoint) -> Double
    var color: Color
    var fixedMax: Double? = nil
    var height: CGFloat = 150
    var unit: String = "%"

    private var maxValue: Double {
        if let fixedMax { return fixedMax }
        let m = points.map(value).max() ?? 1
        return max(1, m * 1.25)
    }

    var body: some View {
        Chart {
            ForEach(points) { p in
                AreaMark(
                    x: .value(T("时间"), p.time),
                    y: .value(T("值"), value(p))
                )
                .foregroundStyle(
                    LinearGradient(colors: [color.opacity(0.16), color.opacity(0.015)],
                                   startPoint: .top, endPoint: .bottom)
                )
                .interpolationMethod(.catmullRom)

                LineMark(
                    x: .value(T("时间"), p.time),
                    y: .value(T("值"), value(p))
                )
                .foregroundStyle(color)
                .lineStyle(StrokeStyle(lineWidth: 1.6))
                .interpolationMethod(.catmullRom)
            }
        }
        .chartXAxis(.hidden)
        .chartYScale(domain: 0...maxValue)
        .chartYAxis {
            AxisMarks(position: .leading, values: .automatic(desiredCount: 4)) { v in
                AxisGridLine().foregroundStyle(Color.white.opacity(0.06))
                AxisValueLabel {
                    if let d = v.as(Double.self) {
                        Text(fmtAxis(d))
                            .font(.system(size: 9, design: .monospaced))
                            .foregroundStyle(Palette.textSecondary.opacity(0.8))
                    }
                }
            }
        }
        .frame(height: height)
    }

    private func fmtAxis(_ v: Double) -> String {
        if unit == "%" { return "\(Int(v))%" }
        if v >= 1_048_576 { return String(format: "%.0fM", v / 1_048_576) }
        if v >= 1024 { return String(format: "%.0fK", v / 1024) }
        return String(format: "%.0f", v)
    }
}

struct DualSparkChart: View {
    var points: [HistoryPoint]
    var v1: (HistoryPoint) -> Double
    var v2: (HistoryPoint) -> Double
    var c1: Color
    var c2: Color
    var height: CGFloat = 150
    var axisFormat: (Double) -> String = { Fmt.rate($0).replacingOccurrences(of: "/s", with: "") }

    private var maxValue: Double {
        let m = max(points.map(v1).max() ?? 1, points.map(v2).max() ?? 1)
        return max(1, m * 1.25)
    }

    var body: some View {
        Chart {
            ForEach(points) { p in
                LineMark(x: .value(T("时间"), p.time), y: .value(T("下行"), v1(p)), series: .value("s", "a"))
                    .foregroundStyle(c1)
                    .lineStyle(StrokeStyle(lineWidth: 1.6))
                AreaMark(x: .value(T("时间"), p.time), y: .value(T("下行"), v1(p)), series: .value("s", "a"))
                    .foregroundStyle(LinearGradient(colors: [c1.opacity(0.10), .clear], startPoint: .top, endPoint: .bottom))

                LineMark(x: .value(T("时间"), p.time), y: .value(T("上行"), v2(p)), series: .value("s", "b"))
                    .foregroundStyle(c2)
                    .lineStyle(StrokeStyle(lineWidth: 1.6))
                AreaMark(x: .value(T("时间"), p.time), y: .value(T("上行"), v2(p)), series: .value("s", "b"))
                    .foregroundStyle(LinearGradient(colors: [c2.opacity(0.09), .clear], startPoint: .top, endPoint: .bottom))
            }
        }
        .chartXAxis(.hidden)
        .chartYScale(domain: 0...maxValue)
        .chartYAxis {
            AxisMarks(position: .leading, values: .automatic(desiredCount: 4)) { v in
                AxisGridLine().foregroundStyle(Color.white.opacity(0.06))
                AxisValueLabel {
                    if let d = v.as(Double.self) {
                        Text(axisFormat(d))
                            .font(.system(size: 9, design: .monospaced))
                            .foregroundStyle(Palette.textSecondary.opacity(0.8))
                    }
                }
            }
        }
        .frame(height: height)
    }
}

struct PercentDualChart: View {
    var points: [HistoryPoint]
    var v1: (HistoryPoint) -> Double
    var v2: (HistoryPoint) -> Double
    var c1: Color
    var c2: Color
    var height: CGFloat = 150

    var body: some View {
        Chart {
            ForEach(points) { p in
                AreaMark(x: .value(T("时间"), p.time), y: .value("CPU", v1(p)), series: .value("s", "a"))
                    .foregroundStyle(LinearGradient(colors: [c1.opacity(0.24), c1.opacity(0.01)], startPoint: .top, endPoint: .bottom))
                LineMark(x: .value(T("时间"), p.time), y: .value("CPU", v1(p)), series: .value("s", "a"))
                    .foregroundStyle(c1)
                    .lineStyle(StrokeStyle(lineWidth: 1.7))

                LineMark(x: .value(T("时间"), p.time), y: .value(T("内存"), v2(p)), series: .value("s", "b"))
                    .foregroundStyle(c2)
                    .lineStyle(StrokeStyle(lineWidth: 1.5, dash: [4, 3]))
            }
        }
        .chartXAxis(.hidden)
        .chartYScale(domain: 0...100)
        .chartYAxis {
            AxisMarks(position: .leading, values: .automatic(desiredCount: 4)) { v in
                AxisGridLine().foregroundStyle(Color.white.opacity(0.06))
                AxisValueLabel {
                    if let d = v.as(Double.self) {
                        Text("\(Int(d))%")
                            .font(.system(size: 9, design: .monospaced))
                            .foregroundStyle(Palette.textSecondary.opacity(0.8))
                    }
                }
            }
        }
        .frame(height: height)
    }
}

struct LegendDot: View {
    var color: Color
    var text: String
    var body: some View {
        HStack(spacing: 5) {
            Circle().fill(color).frame(width: 6, height: 6)
            Text(text).font(.system(size: 10)).foregroundStyle(Palette.textSecondary)
        }
    }
}

// MARK: - 概览

struct OverviewView: View {
    @ObservedObject var model: AppModel

    var body: some View {
        let s = model.snap
        VStack(spacing: 14) {
            PageHeader(title: T("概览"),
                       subtitle: TF("%@ · %@ · 运行 %@", model.info.chip, model.info.model, Fmt.uptime(ProcessInfo.processInfo.systemUptime)),
                       trailing: TF("更新于 %@", Fmt.time(s.time)))

            HStack(spacing: 14) {
                CardShell(title: T("处理器"), subtitle: TF("%d 核", model.info.cores), accent: Palette.cyan) {
                    HStack(alignment: .top, spacing: 14) {
                        RingGauge(value: s.cpuTotal, color: Palette.cyan, label: T("占用"), caption: T("实时"))
                        VStack(alignment: .leading, spacing: 10) {
                            KVRow(key: T("性能核"), value: TF("%d 核", model.info.perfCores))
                            KVRow(key: T("能效核"), value: TF("%d 核", model.info.effCores))
                            KVRow(key: T("负载 1/5/15"), value: String(format: "%.2f / %.2f / %.2f", s.load1, s.load5, s.load15), mono: true)
                        }
                        .frame(maxWidth: .infinity)
                    }
                }

                CardShell(title: T("内存"), subtitle: TF("%d GB 统一内存", model.info.memoryGB), accent: Palette.purple) {
                    HStack(alignment: .top, spacing: 14) {
                        RingGauge(value: s.mem.total > 0 ? Double(s.mem.used) / Double(s.mem.total) * 100 : 0,
                                  color: Palette.purple, label: T("已用"), caption: TF("压力 %@", T(s.mem.pressureText)))
                        VStack(alignment: .leading, spacing: 10) {
                            KVRow(key: T("已用"), value: Fmt.mem(s.mem.used), mono: true)
                            KVRow(key: T("应用"), value: Fmt.mem(s.mem.app), mono: true)
                            KVRow(key: T("压缩"), value: Fmt.mem(s.mem.compressed), mono: true)
                            KVRow(key: T("交换"), value: Fmt.mem(s.mem.swapUsed), mono: true)
                        }
                        .frame(maxWidth: .infinity)
                    }
                }

                CardShell(title: T("图形处理器"), subtitle: model.info.gpuName, accent: Palette.green) {
                    HStack(alignment: .top, spacing: 14) {
                        RingGauge(value: s.gpuUtil, color: Palette.green, label: T("占用"), caption: TF("%d 核", model.info.gpuCores))
                        VStack(alignment: .leading, spacing: 10) {
                            KVRow(key: T("显存占用"), value: Fmt.bytesU(s.gpuMemUsed), mono: true)
                            KVRow(key: "Metal", value: "Metal 4")
                            KVRow(key: T("类型"), value: T("统一内存"))
                        }
                        .frame(maxWidth: .infinity)
                    }
                }
            }

            HStack(spacing: 14) {
                CardShell(title: T("网络"), subtitle: T("实时吞吐"), accent: Palette.orange) {
                    HStack(spacing: 16) {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(T("下载")).font(.system(size: 10)).foregroundStyle(Palette.textSecondary)
                            BigNumber(value: Fmt.bytes(s.downBps), unit: "/s", color: Palette.cyan, size: 20)
                        }
                        VStack(alignment: .leading, spacing: 2) {
                            Text(T("上传")).font(.system(size: 10)).foregroundStyle(Palette.textSecondary)
                            BigNumber(value: Fmt.bytes(s.upBps), unit: "/s", color: Palette.orange, size: 20)
                        }
                        Spacer()
                        VStack(alignment: .trailing, spacing: 2) {
                            Text(T("累计接收")).font(.system(size: 10)).foregroundStyle(Palette.textSecondary)
                            BigNumber(value: Fmt.bytesU(s.rxTotal), size: 14)
                        }
                    }
                }
                CardShell(title: T("磁盘"), subtitle: T("内部存储"), accent: Palette.pink) {
                    HStack(spacing: 16) {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(T("读")).font(.system(size: 10)).foregroundStyle(Palette.textSecondary)
                            BigNumber(value: Fmt.bytes(s.diskReadBps), unit: "/s", color: Palette.cyan, size: 20)
                        }
                        VStack(alignment: .leading, spacing: 2) {
                            Text(T("写")).font(.system(size: 10)).foregroundStyle(Palette.textSecondary)
                            BigNumber(value: Fmt.bytes(s.diskWriteBps), unit: "/s", color: Palette.pink, size: 20)
                        }
                        Spacer()
                        if let root = s.volumes.first(where: { $0.mount == "/" }) ?? s.volumes.first {
                            VStack(alignment: .trailing, spacing: 2) {
                                Text(T("已用 / 总量")).font(.system(size: 10)).foregroundStyle(Palette.textSecondary)
                                BigNumber(value: "\(Int(root.usedRatio * 100))", unit: "%", color: Palette.textPrimary, size: 14)
                            }
                        }
                    }
                }

                CardShell(title: T("温度与功耗"), subtitle: s.sensors.active ? T("传感器助手运行中") : T("未启用"), accent: Palette.orange) {
                    if s.sensors.active {
                        HStack(alignment: .top, spacing: 12) {
                            VStack(alignment: .leading, spacing: 2) {
                                Text("CPU").font(.system(size: 10)).foregroundStyle(Palette.textSecondary)
                                BigNumber(value: s.sensors.cpuTemp.map { String(format: "%.0f", $0) } ?? "--", unit: "°C", color: Palette.orange, size: 20)
                            }
                            VStack(alignment: .leading, spacing: 2) {
                                Text("GPU").font(.system(size: 10)).foregroundStyle(Palette.textSecondary)
                                BigNumber(value: s.sensors.gpuTemp.map { String(format: "%.0f", $0) } ?? "--", unit: "°C", color: Palette.pink, size: 20)
                            }
                            Spacer()
                            VStack(alignment: .trailing, spacing: 2) {
                                Text(T("整机功耗")).font(.system(size: 10)).foregroundStyle(Palette.textSecondary)
                                BigNumber(value: s.sensors.combinedPower.map { String(format: "%.1f", $0) } ?? "--", unit: "W", color: Palette.cyan, size: 20)
                            }
                        }
                    } else {
                        HStack(spacing: 8) {
                            Image(systemName: "thermometer.medium").font(.system(size: 13)).foregroundStyle(Palette.orange)
                            Text(T("到「温度与功耗」页启用传感器助手")).font(.system(size: 11)).foregroundStyle(Palette.textSecondary)
                        }
                    }
                }
            }

            HStack(alignment: .top, spacing: 14) {
                CardShell(title: T("综合负载"), subtitle: TF("近 %d 秒", model.history.count), accent: Palette.cyan) {
                    VStack(spacing: 8) {
                        PercentDualChart(points: model.history,
                                         v1: { $0.cpu },
                                         v2: { $0.memRatio },
                                         c1: Palette.cyan, c2: Palette.purple, height: 232)
                        HStack(spacing: 16) {
                            LegendDot(color: Palette.cyan, text: T("CPU 占用"))
                            LegendDot(color: Palette.purple, text: T("内存占用"))
                            Spacer()
                            Text(TF("最高 %d%%", Int(model.history.map { $0.cpu }.max() ?? 0)))
                                .font(.system(size: 10, design: .monospaced))
                                .foregroundStyle(Palette.textSecondary)
                        }
                    }
                }

                CardShell(title: T("系统信息"), accent: Palette.purple) {
                    VStack(spacing: 9) {
                        KVRow(key: T("芯片"), value: model.info.chip)
                        KVRow(key: T("型号"), value: model.info.model, mono: true)
                        KVRow(key: T("架构"), value: model.info.arch, mono: true)
                        KVRow(key: T("核心"), value: TF("%d 核（%dP + %dE）", model.info.cores, model.info.perfCores, model.info.effCores))
                        KVRow(key: T("内存"), value: "\(model.info.memoryGB) GB")
                        KVRow(key: T("显卡"), value: TF("%@（%d 核）", model.info.gpuName, model.info.gpuCores))
                        KVRow(key: T("系统"), value: model.info.osVersion)
                        Divider().overlay(Palette.stroke)
                        KVRow(key: T("进程 / 线程"), value: "\(s.processCount) / \(s.threadCount)", mono: true)
                        KVRow(key: T("热压力"), value: T(s.thermalState))
                    }
                }
                .frame(width: 328)
            }
        }
    }
}

// MARK: - CPU

struct CPUView: View {
    @ObservedObject var model: AppModel

    var body: some View {
        let s = model.snap
        VStack(spacing: 14) {
            PageHeader(title: T("处理器"), subtitle: TF("%@ · %d 核（%d 性能 + %d 能效）", model.info.chip, model.info.cores, model.info.perfCores, model.info.effCores),
                       trailing: TF("占用 %d%%", Int(s.cpuTotal)))

            CardShell(title: T("总占用"), subtitle: TF("近 %d 秒", model.history.count), accent: Palette.cyan) {
                SparkChart(points: model.history, value: { $0.cpu }, color: Palette.cyan, fixedMax: 100, height: 236)
            }

            HStack(spacing: 14) {
                MetricTile(title: T("当前占用"), big: String(format: "%.0f%%", s.cpuTotal), sub: T("总利用率"), color: Palette.cyan)
                MetricTile(title: T("负载均值"), big: String(format: "%.2f", s.load1), sub: TF("5 分钟 %.2f", s.load5), color: Palette.orange)
                MetricTile(title: T("进程"), big: "\(s.processCount)", sub: TF("线程 %d", s.threadCount), color: Palette.purple)
                MetricTile(title: T("运行时长"), big: Fmt.uptime(ProcessInfo.processInfo.systemUptime), sub: T("自上次启动"), color: Palette.green, small: true)
            }

            CardShell(title: T("每核占用"), subtitle: TF("前 %d 核为性能核 P，其后为能效核 E", model.info.perfCores), accent: Palette.purple) {
                CoreBars(values: s.perCore, perfCount: model.info.perfCores)
                    .frame(height: 150)
                HStack(spacing: 16) {
                    LegendDot(color: Palette.cyan, text: T("性能核"))
                    LegendDot(color: Palette.purple, text: T("能效核"))
                    Spacer()
                    Text(TF("%d 核 · 逐核利用率", model.info.cores))
                        .font(.system(size: 10))
                        .foregroundStyle(Palette.textSecondary)
                }
            }

            CardShell(title: T("负载均值"), accent: Palette.orange) {
                HStack(spacing: 32) {
                    LoadStat(label: T("1 分钟"), value: s.load1)
                    LoadStat(label: T("5 分钟"), value: s.load5)
                    LoadStat(label: T("15 分钟"), value: s.load15)
                    Spacer()
                    Text(T("每核负载参考：1.0 表示满载"))
                        .font(.system(size: 10))
                        .foregroundStyle(Palette.textSecondary)
                }
            }
        }
    }
}

struct MetricTile: View {
    var title: String
    var big: String
    var sub: String
    var color: Color
    var small: Bool = false

    var body: some View {
        CardShell(title: title, accent: color) {
            VStack(alignment: .leading, spacing: 5) {
                Text(big)
                    .font(.system(size: small ? 17 : 22, weight: .semibold, design: .rounded))
                    .foregroundStyle(color)
                    .monospacedDigit()
                    .lineLimit(1)
                    .minimumScaleFactor(0.7)
                Text(sub)
                    .font(.system(size: 10))
                    .foregroundStyle(Palette.textSecondary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .frame(maxWidth: .infinity, minHeight: 92, alignment: .topLeading)
    }
}

struct LoadStat: View {
    var label: String
    var value: Double
    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(String(format: "%.2f", value))
                .font(.system(size: 22, weight: .semibold, design: .rounded))
                .foregroundStyle(Palette.textPrimary)
                .monospacedDigit()
            Text(label)
                .font(.system(size: 10))
                .foregroundStyle(Palette.textSecondary)
        }
    }
}

struct CoreBars: View {
    var values: [Double]
    var perfCount: Int

    var body: some View {
        GeometryReader { geo in
            let count = max(1, values.count)
            let gap: CGFloat = 6
            let w = (geo.size.width - gap * CGFloat(count - 1)) / CGFloat(count)
            HStack(alignment: .bottom, spacing: gap) {
                ForEach(Array(values.enumerated()), id: \.offset) { idx, v in
                    VStack(spacing: 6) {
                        Spacer(minLength: 0)
                        RoundedRectangle(cornerRadius: 4, style: .continuous)
                            .fill(LinearGradient(colors: [(idx < perfCount ? Palette.cyan : Palette.purple).opacity(0.55),
                                                          (idx < perfCount ? Palette.cyan : Palette.purple)],
                                                 startPoint: .bottom, endPoint: .top))
                            .frame(width: w, height: max(4, (geo.size.height - 26) * CGFloat(v / 100)))
                            .animation(.easeOut(duration: 0.35), value: v)
                        Text("\(Int(v))")
                            .font(.system(size: 9, design: .monospaced))
                            .foregroundStyle(Palette.textSecondary)
                        Text(idx < perfCount ? "P\(idx + 1)" : "E\(idx - perfCount + 1)")
                            .font(.system(size: 9, weight: .medium))
                            .foregroundStyle(idx < perfCount ? Palette.cyan.opacity(0.9) : Palette.purple.opacity(0.9))
                    }
                    .frame(width: w)
                }
            }
        }
    }
}

// MARK: - 内存

struct MemoryView: View {
    @ObservedObject var model: AppModel

    var body: some View {
        let s = model.snap
        let m = s.mem
        let ratio = m.total > 0 ? Double(m.used) / Double(m.total) : 0
        VStack(spacing: 14) {
            PageHeader(title: T("内存"), subtitle: TF("%d GB 统一内存 · 压力 %@", model.info.memoryGB, T(m.pressureText)),
                       trailing: TF("已用 %@", Fmt.mem(m.used)), accent: Palette.purple)

            HStack(alignment: .top, spacing: 14) {
                CardShell(title: T("占用"), accent: Palette.purple) {
                    VStack(spacing: 22) {
                        RingGauge(value: ratio * 100, color: Palette.purple, label: T("已用"),
                                  caption: "\(Fmt.mem(m.used)) / \(Fmt.mem(m.total))", lineWidth: 12, size: 190)
                        HStack(spacing: 8) {
                            Circle()
                                .fill(m.pressure >= 2 ? Palette.orange : Palette.green)
                                .frame(width: 7, height: 7)
                            Text(TF("内存压力 %@", T(m.pressureText)))
                                .font(.system(size: 12, weight: .medium))
                                .foregroundStyle(m.pressure >= 2 ? Palette.orange : Palette.green)
                        }
                        Divider().overlay(Palette.stroke)
                        HStack {
                            VStack(alignment: .leading, spacing: 3) {
                                Text(T("剩余可用")).font(.system(size: 10)).foregroundStyle(Palette.textSecondary)
                                Text(Fmt.mem(m.total - m.used))
                                    .font(.system(size: 15, weight: .semibold, design: .rounded))
                                    .foregroundStyle(Palette.textPrimary)
                            }
                            Spacer()
                            VStack(alignment: .trailing, spacing: 3) {
                                Text(T("已用占比")).font(.system(size: 10)).foregroundStyle(Palette.textSecondary)
                                Text("\(Int(ratio * 100))%")
                                    .font(.system(size: 15, weight: .semibold, design: .rounded))
                                    .foregroundStyle(Palette.purple)
                            }
                        }
                        Spacer(minLength: 0)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                .frame(width: 330, height: 392, alignment: .top)

                CardShell(title: T("内存构成"), subtitle: T("与活动监视器口径近似"), accent: Palette.cyan) {
                    VStack(alignment: .leading, spacing: 22) {
                        MemRow(label: T("应用内存"), value: m.app, total: m.total, color: Palette.cyan)
                        MemRow(label: T("联动内存"), value: m.wired, total: m.total, color: Palette.orange)
                        MemRow(label: T("压缩内存"), value: m.compressed, total: m.total, color: Palette.purple)
                        MemRow(label: T("文件缓存"), value: m.cached, total: m.total, color: Palette.green)
                        Divider().overlay(Palette.stroke)
                        HStack {
                            Text(T("应用 + 联动 + 压缩 即“已用内存”"))
                                .font(.system(size: 10))
                                .foregroundStyle(Palette.textSecondary)
                            Spacer()
                            Text(Fmt.mem(m.app + m.wired + m.compressed))
                                .font(.system(size: 12, weight: .semibold, design: .monospaced))
                                .foregroundStyle(Palette.textPrimary)
                        }
                        Spacer(minLength: 0)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                .frame(height: 392, alignment: .top)

                CardShell(title: T("交换"), subtitle: "Swap", accent: Palette.pink) {
                    VStack(alignment: .leading, spacing: 12) {
                        BigNumber(value: Fmt.mem(m.swapUsed), color: Palette.pink, size: 24)
                        Text(TF("总量 %@", Fmt.mem(m.swapTotal)))
                            .font(.system(size: 11))
                            .foregroundStyle(Palette.textSecondary)
                        BarLine(ratio: m.swapTotal > 0 ? Double(m.swapUsed) / Double(m.swapTotal) : 0,
                                color: Palette.pink, height: 6)
                        Text(m.swapUsed > 5_368_709_120 ? T("交换使用偏高，可能有内存压力") : T("交换使用正常，未出现换页压力"))
                            .font(.system(size: 10))
                            .foregroundStyle(Palette.textSecondary)
                            .fixedSize(horizontal: false, vertical: true)
                        Spacer(minLength: 0)
                        KVRow(key: T("物理内存"), value: "\(model.info.memoryGB) GB", mono: true)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                .frame(width: 290, height: 392, alignment: .top)
            }

            CardShell(title: T("占用趋势"), subtitle: TF("近 %d 秒", model.history.count), accent: Palette.purple) {
                SparkChart(points: model.history, value: { $0.memRatio }, color: Palette.purple, fixedMax: 100, height: 214)
            }
        }
    }
}

struct MemRow: View {
    var label: String
    var value: UInt64
    var total: UInt64
    var color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            HStack {
                Text(label).font(.system(size: 12)).foregroundStyle(Palette.textSecondary)
                Spacer()
                Text(Fmt.mem(value)).font(.system(size: 12, weight: .medium, design: .monospaced)).foregroundStyle(Palette.textPrimary)
            }
            BarLine(ratio: total > 0 ? Double(value) / Double(total) : 0, color: color, height: 5)
        }
    }
}

// MARK: - 温度与功耗

struct ThermalView: View {
    @ObservedObject var model: AppModel

    private func fmt(_ v: Double?, _ digits: Int) -> String {
        guard let v else { return "--" }
        return String(format: "%.\(digits)f", v)
    }

    var body: some View {
        let s = model.snap
        let sen = s.sensors
        let installed = HelperInstaller.isInstalled

        VStack(alignment: .leading, spacing: 14) {
            PageHeader(title: T("温度与功耗"),
                       subtitle: sen.active ? T("特权助手正在采集 SoC 传感器") : T("温度、功耗与风扇读数需要一次管理员授权"),
                       trailing: sen.active ? T("实时采集中") : (installed ? T("助手未响应") : T("未启用")),
                       accent: Palette.orange)

            if sen.active {
                HStack(alignment: .top, spacing: 14) {
                    TileCard(label: T("CPU 温度"), value: fmt(sen.cpuTemp, 1), unit: "°C", note: TF("均值 %.1f °C", sen.cpuTempAvg ?? 0), color: Palette.orange, icon: "cpu")
                    TileCard(label: T("GPU 温度"), value: fmt(sen.gpuTemp, 1), unit: "°C", note: TF("均值 %.1f °C", sen.gpuTempAvg ?? 0), color: Palette.pink, icon: "cpu.fill")
                    TileCard(label: T("整机功耗"), value: fmt(sen.combinedPower, 1), unit: "W", note: "CPU \(fmt(sen.cpuPower, 1)) W · GPU \(fmt(sen.gpuPower, 1)) W", color: Palette.cyan, icon: "bolt.fill")
                    TileCard(label: T("风扇转速"), value: fmt(sen.fanRPM, 0), unit: "RPM", note: sen.fanMax.map { TF("最高 %d RPM", Int($0)) } ?? T("无风扇或未读到"), color: Palette.purple, icon: "fanblades.fill")
                }

                HStack(alignment: .top, spacing: 14) {
                    CardShell(title: T("温度趋势"), subtitle: TF("近 %d 秒", model.history.count), accent: Palette.orange) {
                        VStack(spacing: 8) {
                            DualSparkChart(points: model.history,
                                           v1: { $0.cpuTemp },
                                           v2: { $0.gpuTemp },
                                           c1: Palette.orange, c2: Palette.pink, height: 190,
                                           axisFormat: { "\(Int($0))°" })
                            HStack(spacing: 16) {
                                LegendDot(color: Palette.orange, text: "CPU")
                                LegendDot(color: Palette.pink, text: "GPU")
                                Spacer()
                                Text(TF("热压力 %@", T(s.thermalState)))
                                    .font(.system(size: 10))
                                    .foregroundStyle(Palette.textSecondary)
                            }
                        }
                    }
                    CardShell(title: T("功耗趋势"), subtitle: T("powermetrics 采样"), accent: Palette.cyan) {
                        VStack(spacing: 8) {
                            DualSparkChart(points: model.history,
                                           v1: { $0.power },
                                           v2: { $0.power },
                                           c1: Palette.cyan, c2: Color.clear, height: 190,
                                           axisFormat: { String(format: "%.1fW", $0) })
                            HStack(spacing: 16) {
                                LegendDot(color: Palette.cyan, text: T("整机功耗（CPU+GPU+ANE）"))
                                Spacer()
                                Text(TF("压力等级 %@", sen.pressure ?? "--"))
                                    .font(.system(size: 10))
                                    .foregroundStyle(Palette.textSecondary)
                            }
                        }
                    }
                }

                CardShell(title: T("传感器明细"), subtitle: TF("%d 个 CPU 温度传感器 · %d 个其它", sen.cpuSensors, max(0, sen.sensors.count - sen.cpuSensors)), accent: Palette.purple) {
                    let cols = Array(repeating: GridItem(.flexible(), spacing: 10), count: 4)
                    LazyVGrid(columns: cols, alignment: .leading, spacing: 8) {
                        ForEach(sen.sensors.prefix(28), id: \.key) { item in
                            HStack(spacing: 6) {
                                Text(item.key)
                                    .font(.system(size: 10, design: .monospaced))
                                    .foregroundStyle(Palette.textSecondary)
                                Spacer(minLength: 2)
                                Text(String(format: "%.1f", item.value))
                                    .font(.system(size: 10, weight: .medium, design: .monospaced))
                                    .foregroundStyle(Palette.textPrimary)
                            }
                            .padding(.horizontal, 8)
                            .padding(.vertical, 5)
                            .background(RoundedRectangle(cornerRadius: 6, style: .continuous).fill(Palette.panelSoft.opacity(0.55)))
                        }
                    }
                    if let upd = sen.updated {
                        HStack {
                            Text(TF("更新于 %@", Fmt.time(upd)))
                                .font(.system(size: 10))
                                .foregroundStyle(Palette.textSecondary)
                            Spacer()
                            Button(T("卸载助手")) { model.uninstallHelper() }
                                .buttonStyle(.plain)
                                .font(.system(size: 10))
                                .foregroundStyle(Palette.textSecondary)
                        }
                    }
                }
            } else {
                setupCard(installed: installed)
            }
        }
        .alert(T("操作未完成"), isPresented: Binding(get: { model.helperMessage != nil },
                                                set: { if !$0 { model.helperMessage = nil } })) {
            Button(T("好")) { model.helperMessage = nil }
        } message: {
            Text(model.helperMessage ?? "")
        }
    }

    private func setupCard(installed: Bool) -> some View {
        CardShell(accent: Palette.orange) {
            VStack(alignment: .leading, spacing: 14) {
                HStack(spacing: 12) {
                    ZStack {
                        RoundedRectangle(cornerRadius: 12, style: .continuous)
                            .fill(Palette.orange.opacity(0.14))
                            .frame(width: 42, height: 42)
                        Image(systemName: "thermometer.medium")
                            .font(.system(size: 18))
                            .foregroundStyle(Palette.orange)
                    }
                    VStack(alignment: .leading, spacing: 3) {
                        Text(installed ? T("传感器助手已安装，但没有响应") : T("启用温度、功耗与风扇读数"))
                            .font(.system(size: 15, weight: .semibold))
                            .foregroundStyle(Palette.textPrimary)
                        Text(installed ? T("可以重新安装一次以重启后台服务。") : T("macOS 不允许普通应用直接读取 SoC 传感器，需要安装一个小助手并获得一次授权。"))
                            .font(.system(size: 11))
                            .foregroundStyle(Palette.textSecondary)
                    }
                    Spacer()
                }

                VStack(alignment: .leading, spacing: 8) {
                    BulletLine(icon: "checkmark.seal", text: T("助手只做两件事：读 SMC 温度与风扇、跑 powermetrics 读 CPU/GPU/ANE 功耗"))
                    BulletLine(icon: "lock.shield", text: T("以 root 运行、只写本机 /var/run/hardwaremaster/metrics.json，不联网、不上传任何数据"))
                    BulletLine(icon: "arrow.uturn.backward", text: T("随时可在本页或设置页卸载，删除后不留后台进程"))
                }

                HStack(spacing: 10) {
                    Button {
                        model.installHelper()
                    } label: {
                        HStack(spacing: 6) {
                            if model.helperBusy { ProgressView().controlSize(.small) }
                            else { Image(systemName: "lock.open") }
                            Text(model.helperBusy ? T("正在安装…") : (installed ? T("重新安装助手") : T("启用传感器助手")))
                                .font(.system(size: 12, weight: .medium))
                        }
                        .padding(.horizontal, 14)
                        .padding(.vertical, 8)
                        .background(RoundedRectangle(cornerRadius: 9, style: .continuous).fill(Palette.orange.opacity(0.9)))
                        .foregroundStyle(.white)
                    }
                    .buttonStyle(.plain)
                    .disabled(model.helperBusy)

                    if installed {
                        Button(T("卸载")) { model.uninstallHelper() }
                            .buttonStyle(.plain)
                            .font(.system(size: 11))
                            .foregroundStyle(Palette.textSecondary)
                            .disabled(model.helperBusy)
                    }

                    Text(T("安装时会弹出系统密码框，只需授权一次"))
                        .font(.system(size: 10))
                        .foregroundStyle(Palette.textSecondary.opacity(0.72))
                }
                .padding(.top, 2)
            }
        }
    }
}

struct BulletLine: View {
    var icon: String
    var text: String
    var body: some View {
        HStack(alignment: .top, spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 10))
                .foregroundStyle(Palette.orange)
                .frame(width: 14)
            Text(text)
                .font(.system(size: 11))
                .foregroundStyle(Palette.textSecondary)
                .fixedSize(horizontal: false, vertical: true)
        }
    }
}

struct TileCard: View {
    var label: String
    var value: String
    var unit: String
    var note: String
    var color: Color
    var icon: String

    var body: some View {
        CardShell(accent: color) {
            VStack(alignment: .leading, spacing: 6) {
                HStack(spacing: 6) {
                    Image(systemName: icon).font(.system(size: 10)).foregroundStyle(color)
                    Text(label).font(.system(size: 11)).foregroundStyle(Palette.textSecondary)
                }
                BigNumber(value: value, unit: unit, color: color, size: 24)
                Text(note)
                    .font(.system(size: 9, design: .monospaced))
                    .foregroundStyle(Palette.textSecondary.opacity(0.72))
                    .lineLimit(1)
            }
        }
    }
}

// MARK: - 网络

struct NetworkView: View {
    @ObservedObject var model: AppModel

    var body: some View {
        let s = model.snap
        VStack(spacing: 14) {
            PageHeader(title: T("网络"), subtitle: T("实时吞吐与累计流量 · 不含回环"),
                       trailing: "↓ \(Fmt.rate(s.downBps))  ↑ \(Fmt.rate(s.upBps))", accent: Palette.orange)

            HStack(spacing: 14) {
                CardShell(title: T("吞吐曲线"), subtitle: TF("近 %d 秒", model.history.count), accent: Palette.cyan) {
                    DualSparkChart(points: model.history, v1: { $0.down }, v2: { $0.up },
                                   c1: Palette.cyan, c2: Palette.orange, height: 190)
                    HStack(spacing: 16) {
                        LegendDot(color: Palette.cyan, text: T("下载"))
                        LegendDot(color: Palette.orange, text: T("上传"))
                        Spacer()
                        Text(TF("峰值 %@", Fmt.rate(model.history.map { max($0.down, $0.up) }.max() ?? 0)))
                            .font(.system(size: 10, design: .monospaced))
                            .foregroundStyle(Palette.textSecondary)
                    }
                }

                CardShell(title: T("累计流量"), accent: Palette.purple) {
                    VStack(alignment: .leading, spacing: 14) {
                        VStack(alignment: .leading, spacing: 3) {
                            Text(T("接收")).font(.system(size: 10)).foregroundStyle(Palette.textSecondary)
                            BigNumber(value: Fmt.bytesU(s.rxTotal), color: Palette.cyan, size: 20)
                        }
                        VStack(alignment: .leading, spacing: 3) {
                            Text(T("发送")).font(.system(size: 10)).foregroundStyle(Palette.textSecondary)
                            BigNumber(value: Fmt.bytesU(s.txTotal), color: Palette.orange, size: 20)
                        }
                        Divider().overlay(Palette.stroke)
                        KVRow(key: T("活动接口"), value: TF("%d 个", s.ifaces.filter { !$0.isLoopback && $0.isUp }.count))
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                .frame(width: 240)
            }

            CardShell(title: T("网络接口"), subtitle: T("每个接口的实时速率"), accent: Palette.cyan) {
                VStack(spacing: 8) {
                    HStack {
                        Text(T("接口")).frame(width: 150, alignment: .leading)
                        Text(T("状态")).frame(width: 60, alignment: .leading)
                        Text(T("下载")).frame(width: 110, alignment: .trailing)
                        Text(T("上传")).frame(width: 110, alignment: .trailing)
                        Text(T("累计接收")).frame(maxWidth: .infinity, alignment: .trailing)
                        Text(T("累计发送")).frame(maxWidth: .infinity, alignment: .trailing)
                    }
                    .font(.system(size: 10, weight: .medium))
                    .foregroundStyle(Palette.textSecondary)

                    ForEach(s.ifaces) { iface in
                        HStack {
                            HStack(spacing: 7) {
                                Image(systemName: iface.isLoopback ? "arrow.triangle.2.circlepath" : (iface.isWifi ? "wifi" : "cable.connector"))
                                    .font(.system(size: 11))
                                    .foregroundStyle(iface.isLoopback ? Palette.textSecondary : Palette.cyan)
                                VStack(alignment: .leading, spacing: 1) {
                                    Text(iface.name).font(.system(size: 12, weight: .medium, design: .monospaced)).foregroundStyle(Palette.textPrimary)
                                    if iface.displayName != iface.name {
                                        Text(iface.displayName).font(.system(size: 9)).foregroundStyle(Palette.textSecondary)
                                    }
                                }
                            }
                            .frame(width: 150, alignment: .leading)

                            HStack(spacing: 5) {
                                Circle().fill(iface.isUp ? Palette.green : Palette.textSecondary.opacity(0.4)).frame(width: 5, height: 5)
                                Text(iface.isUp ? T("启用") : T("关闭")).font(.system(size: 10)).foregroundStyle(Palette.textSecondary)
                            }
                            .frame(width: 60, alignment: .leading)

                            Text(Fmt.rate(iface.downBps)).font(.system(size: 11, design: .monospaced)).foregroundStyle(Palette.cyan)
                                .frame(width: 110, alignment: .trailing)
                            Text(Fmt.rate(iface.upBps)).font(.system(size: 11, design: .monospaced)).foregroundStyle(Palette.orange)
                                .frame(width: 110, alignment: .trailing)
                            Text(Fmt.bytesU(iface.rxTotal)).font(.system(size: 11, design: .monospaced)).foregroundStyle(Palette.textSecondary)
                                .frame(maxWidth: .infinity, alignment: .trailing)
                            Text(Fmt.bytesU(iface.txTotal)).font(.system(size: 11, design: .monospaced)).foregroundStyle(Palette.textSecondary)
                                .frame(maxWidth: .infinity, alignment: .trailing)
                        }
                        .padding(.vertical, 7)
                        .padding(.horizontal, 10)
                        .background(RoundedRectangle(cornerRadius: 8).fill(Color.white.opacity(iface.isLoopback ? 0.02 : 0.035)))
                    }
                }
            }
        }
    }
}

// MARK: - 磁盘

struct DiskView: View {
    @ObservedObject var model: AppModel

    var body: some View {
        let s = model.snap
        VStack(spacing: 14) {
            PageHeader(title: T("磁盘"), subtitle: T("卷容量与读写吞吐"),
                       trailing: TF("读 %@ · 写 %@", Fmt.rate(s.diskReadBps), Fmt.rate(s.diskWriteBps)), accent: Palette.pink)

            HStack(alignment: .top, spacing: 14) {
                CardShell(title: T("读写吞吐"), subtitle: TF("近 %d 秒", model.history.count), accent: Palette.pink) {
                    DualSparkChart(points: model.history, v1: { $0.diskRead }, v2: { $0.diskWrite },
                                   c1: Palette.cyan, c2: Palette.pink, height: 208)
                    HStack(spacing: 16) {
                        LegendDot(color: Palette.cyan, text: T("读取"))
                        LegendDot(color: Palette.pink, text: T("写入"))
                        Spacer()
                        Text(TF("峰值 %@", Fmt.rate(model.history.map { max($0.diskRead, $0.diskWrite) }.max() ?? 0)))
                            .font(.system(size: 10, design: .monospaced))
                            .foregroundStyle(Palette.textSecondary)
                    }
                }

                CardShell(title: T("累计读写"), subtitle: T("自本次开机"), accent: Palette.cyan) {
                    VStack(alignment: .leading, spacing: 16) {
                        VStack(alignment: .leading, spacing: 3) {
                            Text(T("累计读取")).font(.system(size: 10)).foregroundStyle(Palette.textSecondary)
                            BigNumber(value: Fmt.bytesU(s.diskReadTotal), color: Palette.cyan, size: 18)
                        }
                        VStack(alignment: .leading, spacing: 3) {
                            Text(T("累计写入")).font(.system(size: 10)).foregroundStyle(Palette.textSecondary)
                            BigNumber(value: Fmt.bytesU(s.diskWriteTotal), color: Palette.pink, size: 18)
                        }
                        Divider().overlay(Palette.stroke)
                        if let root = s.volumes.first(where: { $0.mount == "/" }) ?? s.volumes.first {
                            KVRow(key: T("系统卷已用"), value: "\(Fmt.bytesU(UInt64(root.used))) / \(Fmt.bytesU(UInt64(root.total)))")
                            BarLine(ratio: root.usedRatio,
                                    color: root.usedRatio > 0.9 ? Palette.red : (root.usedRatio > 0.75 ? Palette.orange : Palette.cyan),
                                    height: 6)
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
                .frame(width: 288)
            }

            CardShell(title: T("卷"), subtitle: T("已挂载的本地卷"), accent: Palette.cyan) {
                VStack(spacing: 12) {
                    ForEach(s.volumes) { v in
                        VStack(alignment: .leading, spacing: 7) {
                            HStack {
                                Image(systemName: v.mount == "/" ? "internaldrive.fill" : "externaldrive")
                                    .font(.system(size: 12))
                                    .foregroundStyle(Palette.cyan)
                                Text(v.name)
                                    .font(.system(size: 12, weight: .medium))
                                    .foregroundStyle(Palette.textPrimary)
                                Text(v.mount)
                                    .font(.system(size: 10, design: .monospaced))
                                    .foregroundStyle(Palette.textSecondary.opacity(0.8))
                                Spacer()
                                Text("\(Fmt.bytesU(UInt64(v.used))) / \(Fmt.bytesU(UInt64(v.total)))")
                                    .font(.system(size: 11, design: .monospaced))
                                    .foregroundStyle(Palette.textSecondary)
                                Text("\(Int(v.usedRatio * 100))%")
                                    .font(.system(size: 11, weight: .semibold, design: .monospaced))
                                    .foregroundStyle(v.usedRatio > 0.9 ? Palette.red : Palette.textPrimary)
                                    .frame(width: 40, alignment: .trailing)
                            }
                            BarLine(ratio: v.usedRatio,
                                    color: v.usedRatio > 0.9 ? Palette.red : (v.usedRatio > 0.75 ? Palette.orange : Palette.cyan),
                                    height: 7)
                        }
                    }
                }
            }
        }
    }
}

// MARK: - 设置

struct SettingsView: View {
    @ObservedObject var model: AppModel

    var body: some View {
        VStack(spacing: 14) {
            PageHeader(title: T("设置"), subtitle: T("采样与显示"), trailing: "v1.1.0")

            CardShell(title: T("采样"), accent: Palette.cyan) {
                VStack(alignment: .leading, spacing: 14) {
                    HStack {
                        Text(T("刷新间隔")).font(.system(size: 12)).foregroundStyle(Palette.textSecondary)
                        Spacer()
                        Picker("", selection: Binding(
                            get: { Int(model.interval) },
                            set: { model.setInterval(Double($0)) }
                        )) {
                            Text(T("1 秒")).tag(1)
                            Text(T("2 秒")).tag(2)
                            Text(T("5 秒")).tag(5)
                        }
                        .pickerStyle(.segmented)
                        .frame(width: 240)
                    }
                    HStack {
                        Text(T("暂停采集")).font(.system(size: 12)).foregroundStyle(Palette.textSecondary)
                        Spacer()
                        Toggle("", isOn: $model.paused).labelsHidden().toggleStyle(.switch)
                    }
                    Text(T("暂停后界面保留最后一次读数，恢复时继续采集。"))
                        .font(.system(size: 10))
                        .foregroundStyle(Palette.textSecondary.opacity(0.8))
                }
            }

            CardShell(title: T("界面语言"), subtitle: T("选择显示语言"), accent: Palette.orange) {
                VStack(alignment: .leading, spacing: 8) {
                    HStack {
                        Text(T("界面语言")).font(.system(size: 12)).foregroundStyle(Palette.textSecondary)
                        Spacer()
                        Picker("", selection: Binding(
                            get: { model.language },
                            set: { model.setLanguage($0) }
                        )) {
                            ForEach(Localizer.languages, id: \.code) { lang in
                                Text(lang.name).tag(lang.code)
                            }
                        }
                        .pickerStyle(.menu)
                        .frame(width: 240)
                    }
                    Text(T("共 25 种语言，含简繁中文（台湾 / 香港用词）"))
                        .font(.system(size: 10))
                        .foregroundStyle(Palette.textSecondary.opacity(0.8))
                }
            }

            CardShell(title: T("温度与功耗助手"), subtitle: HelperInstaller.isInstalled ? T("已安装") : T("未安装"), accent: Palette.orange) {
                HStack(spacing: 10) {
                    if model.snap.sensors.active && HelperInstaller.isInstalled {
                        Text(T("助手正在采集温度、功耗与风扇读数")).font(.system(size: 11)).foregroundStyle(Palette.green)
                    } else {
                        Text(T("未运行，温度与功耗读数不可用")).font(.system(size: 11)).foregroundStyle(Palette.textSecondary)
                    }
                    Spacer()
                    Button(T(HelperInstaller.isInstalled ? "卸载" : "启用")) {
                        if HelperInstaller.isInstalled { model.uninstallHelper() } else { model.installHelper() }
                    }
                    .buttonStyle(.plain)
                    .font(.system(size: 11, weight: .medium))
                    .padding(.horizontal, 12).padding(.vertical, 6)
                    .background(RoundedRectangle(cornerRadius: 8, style: .continuous).fill(Palette.panelSoft.opacity(0.8)))
                    .foregroundStyle(Palette.textPrimary)
                    .disabled(model.helperBusy)
                }
            }

            CardShell(title: T("数据来源"), accent: Palette.purple) {
                VStack(alignment: .leading, spacing: 8) {
                    KVRow(key: "CPU", value: T("host_processor_info（每核 tick）"))
                    KVRow(key: T("内存"), value: "host_statistics64 + vm.swapusage")
                    KVRow(key: "GPU", value: "IOAccelerator PerformanceStatistics")
                    KVRow(key: T("网络"), value: T("sysctl NET_RT_IFLIST2（各接口字节计数）"))
                    KVRow(key: T("磁盘"), value: T("IOBlockStorageDriver Statistics + 卷容量"))
                    KVRow(key: T("热压力"), value: "ProcessInfo.thermalState + pmset -g therm")
                }
                Text(T("所有数据仅在本机内存中计算，不写入磁盘、不上传网络，无任何后台常驻服务。"))
                    .font(.system(size: 10))
                    .foregroundStyle(Palette.textSecondary.opacity(0.85))
                    .padding(.top, 4)
            }
        }
    }
}

// MARK: - 关于

struct AboutView: View {
    @ObservedObject var model: AppModel

    var body: some View {
        VStack(spacing: 14) {
            PageHeader(title: T("关于"), subtitle: T("硬件管理大师 · macOS 版"), trailing: "v1.0.0")

            CardShell(title: T("产品"), accent: Palette.cyan) {
                VStack(alignment: .leading, spacing: 10) {
                    HStack(spacing: 12) {
                        ZStack {
                            RoundedRectangle(cornerRadius: 14, style: .continuous)
                                .fill(LinearGradient(colors: [Palette.cyan, Palette.purple], startPoint: .topLeading, endPoint: .bottomTrailing))
                                .frame(width: 56, height: 56)
                            Image(systemName: "memorychip.fill")
                                .font(.system(size: 26, weight: .semibold))
                                .foregroundStyle(.white)
                        }
                        VStack(alignment: .leading, spacing: 3) {
                            Text(T("硬件管理大师")).font(.system(size: 15, weight: .semibold)).foregroundStyle(Palette.textPrimary)
                            Text("Hardware Master for macOS").font(.system(size: 11)).foregroundStyle(Palette.textSecondary)
                            Text(T("版本 1.1.0 · arm64")).font(.system(size: 10, design: .monospaced)).foregroundStyle(Palette.textSecondary)
                        }
                    }
                    Text(T("面向 Apple Silicon Mac 的本地硬件监控工具：处理器、内存、图形、网络、磁盘与热压力，全部本地采集，无遥测、无后台服务、无广告。"))
                        .font(.system(size: 11))
                        .foregroundStyle(Palette.textSecondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }

            CardShell(title: T("当前设备"), accent: Palette.purple) {
                VStack(spacing: 9) {
                    KVRow(key: T("机型"), value: model.info.model, mono: true)
                    KVRow(key: T("芯片"), value: model.info.chip)
                    KVRow(key: T("核心"), value: "\(model.info.cores)（\(model.info.perfCores)P + \(model.info.effCores)E）")
                    KVRow(key: T("内存"), value: "\(model.info.memoryGB) GB")
                    KVRow(key: T("显卡"), value: TF("%@ · %d 核", model.info.gpuName, model.info.gpuCores))
                    KVRow(key: T("系统"), value: model.info.osVersion)
                    KVRow(key: T("主机名"), value: model.info.hostName)
                }
            }

            CardShell(title: T("隐私与说明"), accent: Palette.green) {
                VStack(alignment: .leading, spacing: 8) {
                    Label(T("不上传任何数据，不包含网络请求"), systemImage: "lock.shield")
                    Label(T("不安装后台服务与开机自启项"), systemImage: "xmark.bin")
                    Label(T("温度与功耗需安装可选的传感器助手"), systemImage: "thermometer.medium")
                    Label(T("数值为系统公开接口采样，与活动监视器口径略有差异"), systemImage: "info.circle")
                }
                .font(.system(size: 11))
                .foregroundStyle(Palette.textSecondary)
            }
        }
    }
}
