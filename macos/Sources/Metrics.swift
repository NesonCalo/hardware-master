import Foundation
import Darwin
import IOKit
import IOKit.storage

// MARK: - 数据模型

struct NetIface: Identifiable, Sendable {
    var id: String { name }
    var name: String
    var displayName: String
    var isUp: Bool
    var isLoopback: Bool
    var isWifi: Bool
    var downBps: Double
    var upBps: Double
    var rxTotal: UInt64
    var txTotal: UInt64
}

struct VolumeInfo: Identifiable, Sendable {
    var id: String { mount }
    var mount: String
    var name: String
    var total: Int64
    var free: Int64
    var used: Int64 { max(0, total - free) }
    var usedRatio: Double { total > 0 ? Double(used) / Double(total) : 0 }
}

struct MemBreakdown: Sendable {
    var total: UInt64 = 0
    var used: UInt64 = 0
    var app: UInt64 = 0
    var wired: UInt64 = 0
    var compressed: UInt64 = 0
    var cached: UInt64 = 0
    var swapUsed: UInt64 = 0
    var swapTotal: UInt64 = 0
    var pressure: Int = 1          // 1 正常 / 2 警告 / 4 严重
    var pressureText: String = "正常"
}

struct SMCSensor: Identifiable, Sendable {
    var id: String { key }
    var key: String
    var value: Double
}

struct SensorData: Sendable {
    var active = false
    var stale = false
    var updated: Date? = nil
    var cpuTemp: Double? = nil
    var cpuTempAvg: Double? = nil
    var gpuTemp: Double? = nil
    var gpuTempAvg: Double? = nil
    var memTemp: Double? = nil
    var fanRPM: Double? = nil
    var fanMax: Double? = nil
    var cpuPower: Double? = nil
    var gpuPower: Double? = nil
    var combinedPower: Double? = nil
    var anePower: Double? = nil
    var pressure: String? = nil
    var sensors: [SMCSensor] = []
    var cpuSensors: Int = 0
}

struct Snapshot: Sendable {
    var time: Date = Date()
    // CPU
    var cpuTotal: Double = 0
    var perCore: [Double] = []
    var perfCoreCount: Int = 0
    var effCoreCount: Int = 0
    var load1: Double = 0
    var load5: Double = 0
    var load15: Double = 0
    var processCount: Int = 0
    var threadCount: Int = 0
    // 内存
    var mem: MemBreakdown = MemBreakdown()
    // GPU
    var gpuUtil: Double = 0
    var gpuMemUsed: UInt64 = 0
    var gpuMemAlloc: UInt64 = 0
    // 网络
    var ifaces: [NetIface] = []
    var downBps: Double = 0
    var upBps: Double = 0
    var rxTotal: UInt64 = 0
    var txTotal: UInt64 = 0
    // 磁盘
    var diskReadBps: Double = 0
    var diskWriteBps: Double = 0
    var diskReadTotal: UInt64 = 0
    var diskWriteTotal: UInt64 = 0
    var volumes: [VolumeInfo] = []
    // 温度 / 热
    var thermalState: String = "正常"
    var thermalLevel: Int = 0        // 0 正常 1 偏热 2 严重
    var thermalWarn: String = "无记录"
    // 特权传感器助手
    var sensors: SensorData = SensorData()
}

struct SystemInfo: Sendable {
    var chip: String = "Apple Silicon"
    var model: String = ""
    var cores: Int = 0
    var perfCores: Int = 0
    var effCores: Int = 0
    var memoryGB: Int = 0
    var gpuName: String = "Apple GPU"
    var gpuCores: Int = 0
    var osVersion: String = ""
    var hostName: String = ""
    var arch: String = ""
    var bootTime: Date = Date()

    static func collect() -> SystemInfo {
        var info = SystemInfo()
        info.chip = sysctlString("machdep.cpu.brand_string") ?? "Apple Silicon"
        info.model = sysctlString("hw.model") ?? ""
        info.cores = Int(sysctlInt("hw.logicalcpu") ?? 0)
        info.perfCores = Int(sysctlInt("hw.perflevel0.physicalcpu") ?? 0)
        info.effCores = Int(sysctlInt("hw.perflevel1.physicalcpu") ?? 0)
        info.memoryGB = Int((sysctlInt64("hw.memsize") ?? 0) / 1_073_741_824)
        info.osVersion = ProcessInfo.processInfo.operatingSystemVersionString
        info.hostName = ProcessInfo.processInfo.hostName.replacingOccurrences(of: ".local", with: "")
        info.arch = sysctlString("hw.machine") ?? ""
        info.bootTime = Date(timeIntervalSinceNow: -ProcessInfo.processInfo.systemUptime)
        info.gpuName = info.chip
        if let sp = GPUProbe.cores() {
            info.gpuCores = sp
            if let name = GPUProbe.name(), !name.isEmpty { info.gpuName = name }
        }
        return info
    }
}

// MARK: - sysctl 工具

func sysctlString(_ name: String) -> String? {
    var size = 0
    guard sysctlbyname(name, nil, &size, nil, 0) == 0, size > 0 else { return nil }
    var buf = [CChar](repeating: 0, count: size + 1)
    guard sysctlbyname(name, &buf, &size, nil, 0) == 0 else { return nil }
    return String(cString: buf)
}

func sysctlInt(_ name: String) -> Int64? {
    var value: Int64 = 0
    var size = MemoryLayout<Int64>.size
    guard sysctlbyname(name, &value, &size, nil, 0) == 0 else { return nil }
    return value
}

func sysctlInt64(_ name: String) -> UInt64? {
    var value: UInt64 = 0
    var size = MemoryLayout<UInt64>.size
    guard sysctlbyname(name, &value, &size, nil, 0) == 0 else { return nil }
    return value
}

// MARK: - GPU 静态信息（Metal + system_profiler 兜底）

enum GPUProbe {
    private static var cachedName: String?
    private static var cachedCores: Int?

    static func name() -> String? {
        loadIfNeeded()
        return cachedName
    }

    static func cores() -> Int? {
        loadIfNeeded()
        return cachedCores
    }

    private static func loadIfNeeded() {
        if cachedCores != nil { return }
        // 先试 system_profiler（能拿到核心数）
        let p = Process()
        p.executableURL = URL(fileURLWithPath: "/usr/sbin/system_profiler")
        p.arguments = ["SPDisplaysDataType", "-json"]
        let pipe = Pipe()
        p.standardOutput = pipe
        p.standardError = Pipe()
        do {
            try p.run()
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            p.waitUntilExit()
            if let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let arr = obj["SPDisplaysDataType"] as? [[String: Any]],
               let first = arr.first {
                cachedName = first["sppci_model"] as? String ?? first["_name"] as? String
                if let s = first["sppci_cores"] as? String { cachedCores = Int(s) }
                else if let n = first["sppci_cores"] as? Int { cachedCores = n }
            }
        } catch { /* ignore */ }
        if cachedCores == nil { cachedCores = 0 }
    }
}

// MARK: - 采集引擎

final class MetricsEngine: @unchecked Sendable {
    private let queue = DispatchQueue(label: "com.nesoncalo.hardwaremaster.metrics")
    private var prevCPUTicks: [UInt32] = []
    private var prevNet: [String: (rx: UInt64, tx: UInt64)] = [:]
    private var prevDisk: (r: UInt64, w: UInt64) = (0, 0)
    private var prevTime: Date = Date()
    private var lastDiskTotals: (r: UInt64, w: UInt64) = (0, 0)

    func sample() -> Snapshot {
        queue.sync { self._sample() }
    }

    private func _sample() -> Snapshot {
        var snap = Snapshot()
        let now = Date()
        let dt = max(0.2, now.timeIntervalSince(prevTime))
        prevTime = now

        // ---- CPU ----
        if let cpu = sampleCPU() {
            snap.cpuTotal = cpu.total
            snap.perCore = cpu.perCore
        }
        snap.load1 = loadAvg(0)
        snap.load5 = loadAvg(1)
        snap.load15 = loadAvg(2)
        snap.perfCoreCount = Int(sysctlInt("hw.perflevel0.physicalcpu") ?? 0)
        snap.effCoreCount = Int(sysctlInt("hw.perflevel1.physicalcpu") ?? 0)
        snap.processCount = processCount()
        snap.threadCount = threadCount()

        // ---- 内存 ----
        snap.mem = memoryInfo()

        // ---- GPU ----
        if let gpu = gpuInfo() {
            snap.gpuUtil = gpu.util
            snap.gpuMemUsed = gpu.used
            snap.gpuMemAlloc = gpu.alloc
        }

        // ---- 网络 ----
        let ifaces = netIfaces(prev: prevNet, dt: dt)
        snap.ifaces = ifaces
        var newPrev: [String: (rx: UInt64, tx: UInt64)] = [:]
        var down = 0.0, up = 0.0
        var rxSum: UInt64 = 0, txSum: UInt64 = 0
        for i in ifaces {
            newPrev[i.name] = (i.rxTotal, i.txTotal)
            if i.isLoopback { continue }
            down += i.downBps
            up += i.upBps
            rxSum += i.rxTotal
            txSum += i.txTotal
        }
        prevNet = newPrev
        snap.downBps = down
        snap.upBps = up
        snap.rxTotal = rxSum
        snap.txTotal = txSum

        // ---- 磁盘 ----
        let disk = diskTotals()
        if prevDisk != (0, 0), disk.r >= prevDisk.r, disk.w >= prevDisk.w {
            snap.diskReadBps = Double(disk.r - prevDisk.r) / dt
            snap.diskWriteBps = Double(disk.w - prevDisk.w) / dt
        }
        prevDisk = disk
        lastDiskTotals = disk
        snap.diskReadTotal = disk.r
        snap.diskWriteTotal = disk.w
        snap.volumes = volumes()

        // ---- 温度 / 热压力 ----
        let thermal = thermalInfo()
        snap.thermalState = thermal.text
        snap.thermalLevel = thermal.level
        snap.thermalWarn = thermal.warn

        // ---- 特权助手传感器 ----
        snap.sensors = loadSensors()
        return snap
    }

    // CPU 采样
    private func sampleCPU() -> (total: Double, perCore: [Double])? {
        var info: processor_info_array_t?
        var numCpuInfo: mach_msg_type_number_t = 0
        var numCPUs: UInt32 = 0
        let result = host_processor_info(mach_host_self(), PROCESSOR_CPU_LOAD_INFO, &numCPUs, &info, &numCpuInfo)
        guard result == KERN_SUCCESS, let ptr = info else { return nil }
        defer {
            vm_deallocate(mach_task_self_, vm_address_t(UInt(bitPattern: ptr)),
                          vm_size_t(numCpuInfo) * vm_size_t(MemoryLayout<integer_t>.stride))
        }
        let count = Int(numCPUs)
        var ticks = [UInt32](repeating: 0, count: count * 4)
        for i in 0..<(count * 4) { ticks[i] = UInt32(bitPattern: ptr[i]) }

        guard prevCPUTicks.count == ticks.count else {
            prevCPUTicks = ticks
            return (0, Array(repeating: 0, count: count))
        }

        var perCore: [Double] = []
        var busyAll: Double = 0
        var totalAll: Double = 0
        for core in 0..<count {
            let base = core * 4
            var busy: Double = 0
            var total: Double = 0
            for s in 0..<4 {
                let delta = Double(ticks[base + s] - prevCPUTicks[base + s])
                total += delta
                if s == 0 || s == 1 || s == 3 { busy += delta }   // USER SYSTEM NICE 为忙，IDLE(2) 为闲
            }
            let usage = total > 0 ? min(100, max(0, busy / total * 100)) : 0
            perCore.append(usage)
            busyAll += busy
            totalAll += total
        }
        prevCPUTicks = ticks
        let total = totalAll > 0 ? min(100, busyAll / totalAll * 100) : 0
        return (total, perCore)
    }

    private func loadAvg(_ idx: Int) -> Double {
        var loads = [Double](repeating: 0, count: 3)
        if getloadavg(&loads, 3) > 0 { return loads[idx] }
        return 0
    }

    private func processCount() -> Int {
        var pids = [pid_t](repeating: 0, count: 4096)
        let n = pids.withUnsafeMutableBufferPointer { buf in
            proc_listpids(UInt32(PROC_ALL_PIDS), 0, buf.baseAddress, Int32(buf.count * MemoryLayout<pid_t>.size))
        }
        return max(0, Int(n) / MemoryLayout<pid_t>.size)
    }

    private func threadCount() -> Int {
        var pids = [pid_t](repeating: 0, count: 4096)
        let n = pids.withUnsafeMutableBufferPointer { buf in
            proc_listpids(UInt32(PROC_ALL_PIDS), 0, buf.baseAddress, Int32(buf.count * MemoryLayout<pid_t>.size))
        }
        let cnt = Int(n) / MemoryLayout<pid_t>.size
        var threads = 0
        for i in 0..<cnt where pids[i] > 0 {
            var info = proc_taskinfo()
            let sz = Int32(MemoryLayout<proc_taskinfo>.size)
            if proc_pidinfo(pids[i], PROC_PIDTASKINFO, 0, &info, sz) == sz {
                threads += Int(info.pti_threadnum)
            }
        }
        return threads
    }

    // 内存
    private func memoryInfo() -> MemBreakdown {
        var m = MemBreakdown()
        m.total = sysctlInt64("hw.memsize") ?? 0
        var stats = vm_statistics64_data_t()
        var count = mach_msg_type_number_t(MemoryLayout<vm_statistics64_data_t>.size / MemoryLayout<integer_t>.size)
        let kr = withUnsafeMutablePointer(to: &stats) {
            $0.withMemoryRebound(to: integer_t.self, capacity: Int(count)) {
                host_statistics64(mach_host_self(), HOST_VM_INFO64, $0, &count)
            }
        }
        let page = UInt64(vm_kernel_page_size)
        if kr == KERN_SUCCESS {
            let active = UInt64(stats.active_count) * page
            let wired = UInt64(stats.wire_count) * page
            let compressed = UInt64(stats.compressor_page_count) * page
            let cached = UInt64(stats.external_page_count) * page
            m.app = active
            m.wired = wired
            m.compressed = compressed
            m.cached = cached
            m.used = active + wired + compressed
            if m.used > m.total { m.used = m.total }
        }
        var swap = xsw_usage()
        var size = MemoryLayout<xsw_usage>.size
        if sysctlbyname("vm.swapusage", &swap, &size, nil, 0) == 0 {
            m.swapUsed = swap.xsu_used
            m.swapTotal = swap.xsu_total
        }
        var level: Int32 = 1
        var lsize = MemoryLayout<Int32>.size
        if sysctlbyname("kern.memorystatus_vm_pressure_level", &level, &lsize, nil, 0) == 0 {
            m.pressure = Int(level)
        }
        switch m.pressure {
        case 2: m.pressureText = "警告"
        case 4: m.pressureText = "严重"
        default: m.pressureText = "正常"
        }
        return m
    }

    // GPU 占用（IOAccelerator PerformanceStatistics）
    private func gpuInfo() -> (util: Double, used: UInt64, alloc: UInt64)? {
        var iter: io_iterator_t = 0
        guard IOServiceGetMatchingServices(kIOMainPortDefault, IOServiceMatching("IOAccelerator"), &iter) == KERN_SUCCESS else {
            return nil
        }
        defer { IOObjectRelease(iter) }
        var service = IOIteratorNext(iter)
        while service != 0 {
            defer {
                IOObjectRelease(service)
                service = IOIteratorNext(iter)
            }
            if let prop = IORegistryEntryCreateCFProperty(service, "PerformanceStatistics" as CFString, kCFAllocatorDefault, 0)?.takeRetainedValue(),
               let dict = prop as? [String: Any] {
                let util = (dict["Device Utilization %"] as? NSNumber)?.doubleValue
                    ?? (dict["Renderer Utilization %"] as? NSNumber)?.doubleValue ?? 0
                let used = (dict["In use system memory"] as? NSNumber)?.uint64Value ?? 0
                let alloc = (dict["Alloc system memory"] as? NSNumber)?.uint64Value ?? 0
                return (util, used, alloc)
            }
        }
        return nil
    }

    // 网络：sysctl NET_RT_IFLIST2 解析 if_msghdr2
    private func netIfaces(prev: [String: (rx: UInt64, tx: UInt64)], dt: Double) -> [NetIface] {
        var entries: [(name: String, flags: Int32, rx: UInt64, tx: UInt64)] = []
        var mib: [Int32] = [CTL_NET, PF_ROUTE, 0, 0, NET_RT_IFLIST2, 0]
        var len = 0
        guard sysctl(&mib, 6, nil, &len, nil, 0) == 0, len > 0 else { return [] }
        var buf = [UInt8](repeating: 0, count: len)
        guard sysctl(&mib, 6, &buf, &len, nil, 0) == 0 else { return [] }

        buf.withUnsafeBytes { raw in
            var offset = 0
            while offset + 112 <= len {
                let msglen = Int(raw.load(fromByteOffset: offset, as: UInt16.self))
                guard msglen > 0, offset + msglen <= len else { break }
                let type = raw.load(fromByteOffset: offset + 3, as: UInt8.self)
                if type == UInt8(RTM_IFINFO2) {
                    let flags = raw.load(fromByteOffset: offset + 8, as: Int32.self)
                    let index = raw.load(fromByteOffset: offset + 12, as: UInt16.self)
                    // if_msghdr2 内嵌 if_data64：ibytes 在 +64、obytes 在 +72，头部占 32 字节
                    let rx = raw.loadUnaligned(fromByteOffset: offset + 32 + 64, as: UInt64.self)
                    let tx = raw.loadUnaligned(fromByteOffset: offset + 32 + 72, as: UInt64.self)
                    var nameBuf = [CChar](repeating: 0, count: Int(IFNAMSIZ) + 1)
                    if if_indextoname(UInt32(index), &nameBuf) != nil {
                        let name = String(cString: nameBuf)
                        if !name.isEmpty {
                            entries.append((name, flags, rx, tx))
                        }
                    }
                }
                offset += msglen
            }
        }

        var result: [NetIface] = []
        for e in entries {
            let loopback = (e.flags & Int32(IFF_LOOPBACK)) != 0
            let up = (e.flags & Int32(IFF_UP)) != 0
            let wifi = e.name.hasPrefix("en")
            // 只保留有实际流量或主用接口，避免列表被内部空接口淹没
            let hasTraffic = (e.rx + e.tx) > 0
            if loopback { continue }
            if !hasTraffic && e.name != "en0" && e.name != "en1" { continue }
            if !up && !hasTraffic { continue }
            var down = 0.0, up_ = 0.0
            if let p = prev[e.name], e.rx >= p.rx, e.tx >= p.tx {
                down = Double(e.rx - p.rx) / dt
                up_ = Double(e.tx - p.tx) / dt
            }
            result.append(NetIface(name: e.name,
                                   displayName: displayName(for: e.name),
                                   isUp: up,
                                   isLoopback: loopback,
                                   isWifi: wifi,
                                   downBps: down,
                                   upBps: up_,
                                   rxTotal: e.rx,
                                   txTotal: e.tx))
        }
        return result.sorted { a, b in
            if a.isLoopback != b.isLoopback { return !a.isLoopback }
            return a.name < b.name
        }
    }

    private func displayName(for name: String) -> String {
        switch name {
        case "en0": return "主网络接口"
        case "en1": return "第二网络接口"
        case "lo0": return "本地回环"
        case "utun0", "utun1", "utun2", "utun3": return "VPN 隧道"
        case "awdl0": return "AirDrop / 隔空"
        case "llw0": return "低功耗无线"
        case "bridge0": return "桥接网络"
        case "gif0": return "隧道接口"
        case "stf0": return "6to4 隧道"
        default: return name
        }
    }

    // 磁盘累计读写字节
    private func diskTotals() -> (r: UInt64, w: UInt64) {
        var iter: io_iterator_t = 0
        guard IOServiceGetMatchingServices(kIOMainPortDefault, IOServiceMatching("IOBlockStorageDriver"), &iter) == KERN_SUCCESS else {
            return (0, 0)
        }
        defer { IOObjectRelease(iter) }
        var r: UInt64 = 0, w: UInt64 = 0
        var service = IOIteratorNext(iter)
        while service != 0 {
            if let prop = IORegistryEntryCreateCFProperty(service, "Statistics" as CFString, kCFAllocatorDefault, 0)?.takeRetainedValue(),
               let dict = prop as? [String: Any] {
                r += (dict["Bytes (Read)"] as? NSNumber)?.uint64Value ?? 0
                w += (dict["Bytes (Write)"] as? NSNumber)?.uint64Value ?? 0
            }
            IOObjectRelease(service)
            service = IOIteratorNext(iter)
        }
        return (r, w)
    }

    private func volumes() -> [VolumeInfo] {
        let keys: [URLResourceKey] = [.volumeNameKey, .volumeTotalCapacityKey, .volumeAvailableCapacityKey, .volumeIsInternalKey]
        guard let urls = FileManager.default.mountedVolumeURLs(includingResourceValuesForKeys: keys, options: [.skipHiddenVolumes]) else {
            return []
        }
        var list: [VolumeInfo] = []
        for url in urls {
            guard let v = try? url.resourceValues(forKeys: Set(keys)) else { continue }
            let total = Int64(v.volumeTotalCapacity ?? 0)
            let free = Int64(v.volumeAvailableCapacity ?? 0)
            guard total > 0 else { continue }
            list.append(VolumeInfo(mount: url.path, name: v.volumeName ?? url.lastPathComponent, total: total, free: free))
        }
        return list.sorted { $0.mount == "/" ? true : ($1.mount == "/" ? false : $0.total > $1.total) }
    }

    private func thermalInfo() -> (text: String, level: Int, warn: String) {
        var text = "正常"
        var level = 0
        switch ProcessInfo.processInfo.thermalState {
        case .nominal: text = "正常"; level = 0
        case .fair: text = "偏热"; level = 1
        case .serious: text = "较热"; level = 2
        case .critical: text = "过热"; level = 3
        @unknown default: text = "未知"
        }
        var warn = "无记录"
        let p = Process()
        p.executableURL = URL(fileURLWithPath: "/usr/bin/pmset")
        p.arguments = ["-g", "therm"]
        let pipe = Pipe()
        p.standardOutput = pipe
        p.standardError = Pipe()
        if (try? p.run()) != nil {
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            p.waitUntilExit()
            if let out = String(data: data, encoding: .utf8) {
                if out.contains("No thermal warning level") && out.contains("No performance warning level") {
                    warn = "无记录"
                } else if let line = out.split(separator: "\n").first(where: { $0.contains("thermal") || $0.contains("performance") }) {
                    warn = String(line).trimmingCharacters(in: .whitespaces)
                }
            }
        }
        return (text, level, warn)
    }

    // 读取特权助手写出的 JSON
    private func loadSensors() -> SensorData {
        var d = SensorData()
        let path = ProcessInfo.processInfo.environment["HM_METRICS_PATH"] ?? "/var/run/hardwaremaster/metrics.json"
        guard let attrs = try? FileManager.default.attributesOfItem(atPath: path),
              let mod = attrs[.modificationDate] as? Date else { return d }
        let age = Date().timeIntervalSince(mod)
        d.stale = age > 6
        guard age < 60,
              let data = FileManager.default.contents(atPath: path),
              let obj = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any] else { return d }
        d.updated = mod
        d.active = false

        func num(_ k: String) -> Double? {
            if let n = obj[k] as? NSNumber { return n.doubleValue }
            if let v = obj[k] as? Double { return v }
            return nil
        }
        d.cpuTemp = num("cpu_temp")
        d.cpuTempAvg = num("cpu_temp_avg")
        d.gpuTemp = num("gpu_temp")
        d.gpuTempAvg = num("gpu_temp_avg")
        d.memTemp = num("mem_temp")
        d.fanRPM = num("fan_rpm")
        d.fanMax = num("fan_max")
        d.cpuPower = num("cpu_power")
        d.gpuPower = num("gpu_power")
        d.combinedPower = num("combined_power")
        d.anePower = num("ane_power")
        d.pressure = obj["pressure"] as? String
        d.cpuSensors = Int((obj["cpu_sensors"] as? NSNumber)?.intValue ?? 0)
        if let arr = obj["sensors"] as? [[String: Any]] {
            d.sensors = arr.compactMap { item in
                guard let key = item["key"] as? String,
                      let v = (item["value"] as? NSNumber)?.doubleValue else { return nil }
                return SMCSensor(key: key, value: v)
            }
        }
        d.active = age < 6 && (d.cpuTemp != nil || d.combinedPower != nil)
        return d
    }
}
