import Foundation

@main
struct Probe {
    static func main() {
        let e = MetricsEngine()
        _ = e.sample()
        Thread.sleep(forTimeInterval: 1.2)
        let s = e.sample()
        print("CPU \(String(format: "%.1f", s.cpuTotal))%  cores=\(s.perCore.count)")
        print("perCore: " + s.perCore.map { String(format: "%.0f", $0) }.joined(separator: " "))
        print("load \(s.load1) \(s.load5) \(s.load15)  proc=\(s.processCount) threads=\(s.threadCount)")
        print("MEM used=\(Fmt2.bytes(s.mem.used)) total=\(Fmt2.bytes(s.mem.total)) app=\(Fmt2.bytes(s.mem.app)) wired=\(Fmt2.bytes(s.mem.wired)) comp=\(Fmt2.bytes(s.mem.compressed)) swap=\(Fmt2.bytes(s.mem.swapUsed))/\(Fmt2.bytes(s.mem.swapTotal)) pressure=\(s.mem.pressureText)")
        print("GPU util=\(s.gpuUtil)% used=\(Fmt2.bytes(s.gpuMemUsed)) alloc=\(Fmt2.bytes(s.gpuMemAlloc))")
        print("NET down=\(s.downBps) up=\(s.upBps) rx=\(s.rxTotal) tx=\(s.txTotal) ifaces=\(s.ifaces.map { "\($0.name):\(Int($0.downBps))/\(Int($0.upBps))" }.joined(separator: ","))")
        print("DISK r=\(Int(s.diskReadBps))/s w=\(Int(s.diskWriteBps))/s totalR=\(s.diskReadTotal) totalW=\(s.diskWriteTotal)")
        print("VOL " + s.volumes.map { "\($0.name) \(Int($0.used)) / \(Int($0.total))" }.joined(separator: " | "))
        print("THERM \(s.thermalState) warn=\(s.thermalWarn)")
        let info = SystemInfo.collect()
        print("INFO \(info.chip) \(info.model) \(info.cores)核 \(info.perfCores)P+\(info.effCores)E \(info.memoryGB)GB GPU=\(info.gpuName) \(info.gpuCores)核 \(info.osVersion) \(info.arch)")
    }
}

enum Fmt2 {
    static func bytes(_ v: UInt64) -> String {
        String(format: "%.1f MB", Double(v) / 1_048_576)
    }
}
