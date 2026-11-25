#import <Foundation/Foundation.h>
#include <IOKit/IOKitLib.h>
#include <dispatch/dispatch.h>
#include <sys/stat.h>
#include <unistd.h>
#include "smc.h"

static NSString *gRunDir;
static NSString *gOutPath;
static NSString *gLogPath;

static NSMutableString *gLog = nil;

static void setupPaths(void) {
    NSString *dirOverride = [[NSProcessInfo processInfo] environment][@"HM_RUN_DIR"];
    gRunDir = dirOverride.length ? dirOverride : @"/var/run/hardwaremaster";
    gOutPath = [gRunDir stringByAppendingPathComponent:@"metrics.json"];
    NSString *logOverride = [[NSProcessInfo processInfo] environment][@"HM_LOG_PATH"];
    gLogPath = logOverride.length ? logOverride : @"/var/log/hardwaremaster-helper.log";
}

static void HMLog(NSString *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    NSString *line = [[NSString alloc] initWithFormat:fmt arguments:args];
    va_end(args);
    NSString *stamp = [NSDateFormatter localizedStringFromDate:[NSDate date]
                                                     dateStyle:NSDateFormatterMediumStyle
                                                     timeStyle:NSDateFormatterMediumStyle];
    NSString *full = [NSString stringWithFormat:@"%@  %@\n", stamp, line];
    if (!gLog) gLog = [NSMutableString new];
    [gLog appendString:full];
    if (gLog.length > 20000) { [gLog deleteCharactersInRange:NSMakeRange(0, gLog.length - 10000)]; }
    [gLog writeToFile:gLogPath atomically:YES encoding:NSUTF8StringEncoding error:nil];
    NSLog(@"%@", full);
}

static double decodeSMC(UInt32 type, const unsigned char *b, UInt32 size) {
    char t[5] = {0};
    t[0] = (char)((type >> 24) & 0xFF);
    t[1] = (char)((type >> 16) & 0xFF);
    t[2] = (char)((type >> 8) & 0xFF);
    t[3] = (char)(type & 0xFF);

    if (strcmp(t, "flt ") == 0 && size >= 4) {
        float f;
        memcpy(&f, b, 4);
        return (double)f;
    }
    if (strcmp(t, "sp78") == 0 && size >= 2) {
        int16_t raw = (int16_t)(((uint16_t)b[0] << 8) | b[1]);
        return raw / 256.0;
    }
    if (strcmp(t, "fpe2") == 0 && size >= 2) {
        return (((uint16_t)b[0] << 8) | b[1]) / 4.0;
    }
    if (strcmp(t, "ui16") == 0 && size >= 2) {
        return (double)(((uint16_t)b[0] << 8) | b[1]);
    }
    if (strcmp(t, "ui8 ") == 0 && size >= 1) {
        return (double)b[0];
    }
    if (strcmp(t, "sp87") == 0 && size >= 2) {
        int16_t raw = (int16_t)(((uint16_t)b[0] << 8) | b[1]);
        return raw / 128.0;
    }
    return NAN;
}

static NSDictionary *readSMC(NSString *keyName) {
    unsigned char bytes[32];
    UInt32 size = 0, type = 0;
    if (smc_read_key(keyName.UTF8String, bytes, &size, &type) != 0) return nil;
    double v = decodeSMC(type, bytes, size);
    if (isnan(v)) return nil;
    char t[5] = {0};
    t[0] = (char)((type >> 24) & 0xFF);
    t[1] = (char)((type >> 16) & 0xFF);
    t[2] = (char)((type >> 8) & 0xFF);
    t[3] = (char)(type & 0xFF);
    return @{@"key": keyName, @"value": @(v), @"type": [NSString stringWithUTF8String:t], @"size": @(size)};
}

// 型号不同，温度键不同：P 核 Tp/Tf、E 核 Te、GPU Tg、内存 Tm、Intel 老键 TC
static NSArray<NSString *> *cpuKeys(void) {
    return @[@"Tp09", @"Tp0P", @"Tp01", @"Tp0D", @"Tp05", @"Tp0H", @"Tp0L", @"Tp0T", @"Tp0X",
             @"Tp0b", @"Tp0f", @"Tp0j", @"Tp0v", @"Tp0z", @"Tp1h", @"Tp1p", @"Tp1t", @"Tp1R",
             @"Tf04", @"Tf09", @"Tf0D", @"Tf0H", @"Tf0L", @"Tf0P", @"Tf0X",
             @"Te05", @"Te0D", @"Te0L", @"Te0P", @"Te0T",
             @"TC0P", @"TC0D", @"TC0E", @"TC0F", @"TC0H", @"TC0J", @"TC0C"];
}

static NSArray<NSString *> *gpuKeys(void) {
    return @[@"Tg05", @"Tg0D", @"Tg0f", @"Tg0j", @"Tg0L", @"Tg0T", @"Tg0P", @"Tg1j", @"TG0D", @"TG0P"];
}

static NSArray<NSString *> *memKeys(void) {
    return @[@"Tm02", @"Tm06", @"Tm08", @"Tm09", @"Tm0P", @"TM0P"];
}

@interface Collector : NSObject
@property (nonatomic, assign) BOOL smcReady;
@property (nonatomic, strong) NSMutableData *pmBuffer;
@property (nonatomic, assign) double cpuPower;
@property (nonatomic, assign) double gpuPower;
@property (nonatomic, assign) double combinedPower;
@property (nonatomic, assign) double anePower;
@property (nonatomic, copy) NSString *pressure;
@property (nonatomic, assign) BOOL powermetricsAlive;
@end

@implementation Collector

- (instancetype)init {
    self = [super init];
    _pmBuffer = [NSMutableData new];
    _pressure = @"";
    return self;
}

- (void)startPowermetrics {
    NSTask *task = [NSTask new];
    task.launchPath = @"/usr/bin/powermetrics";
    task.arguments = @[@"--samplers", @"cpu_power,gpu_power,ane_power,thermal",
                       @"--format", @"text",
                       @"--sample-rate", @"2000",
                       @"--sample-count", @"-1",
                       @"--hide-cpu-duty-cycle"];
    NSPipe *pipe = [NSPipe pipe];
    task.standardOutput = pipe;
    task.standardError = [NSPipe pipe];
    @try {
        [task launch];
    } @catch (NSException *e) {
        HMLog(@"powermetrics launch failed: %@", e);
        return;
    }
    _powermetricsAlive = YES;
    HMLog(@"powermetrics started pid=%d", task.processIdentifier);

    int fd = [[pipe fileHandleForReading] fileDescriptor];
    dispatch_queue_t q = dispatch_queue_create("hm.pm.read", DISPATCH_QUEUE_SERIAL);
    dispatch_source_t src = dispatch_source_create(DISPATCH_SOURCE_TYPE_READ, fd, 0, q);
    dispatch_source_set_event_handler(src, ^{
        uint8_t buf[8192];
        ssize_t n = read(fd, buf, sizeof(buf));
        if (n <= 0) {
            self.powermetricsAlive = NO;
            dispatch_source_cancel(src);
            return;
        }
        [self.pmBuffer appendBytes:buf length:(NSUInteger)n];
        [self drainLines];
    });
    dispatch_source_set_cancel_handler(src, ^{
        HMLog(@"powermetrics output closed");
    });
    dispatch_resume(src);
}

- (void)drainLines {
    while (YES) {
        const void *bytes = self.pmBuffer.bytes;
        NSUInteger len = self.pmBuffer.length;
        const char *nl = memchr(bytes, '\n', len);
        if (!nl) break;
        NSUInteger lineLen = (NSUInteger)(nl - (const char *)bytes);
        NSData *lineData = [self.pmBuffer subdataWithRange:NSMakeRange(0, lineLen)];
        [self.pmBuffer replaceBytesInRange:NSMakeRange(0, lineLen + 1) withBytes:NULL length:0];
        NSString *line = [[NSString alloc] initWithData:lineData encoding:NSUTF8StringEncoding];
        if (line) [self parseLine:line];
        if (self.pmBuffer.length > 200000) { [self.pmBuffer setLength:0]; }
    }
}

- (void)parseLine:(NSString *)line {
    NSString *trim = [line stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceCharacterSet]];
    if (trim.length == 0) return;
    NSRange colon = [trim rangeOfString:@":"];
    if (colon.location == NSNotFound) return;
    NSString *name = [[trim substringToIndex:colon.location] stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceCharacterSet]];
    NSString *rest = [[trim substringFromIndex:colon.location + 1] stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceCharacterSet]];

    if ([name hasPrefix:@"Current pressure level"]) {
        self.pressure = rest;
        return;
    }
    if (![rest hasSuffix:@"mW"]) return;
    NSString *numStr = [[rest stringByReplacingOccurrencesOfString:@"mW" withString:@""]
        stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceCharacterSet]];
    double mw = numStr.doubleValue;
    if ([name isEqualToString:@"CPU Power"]) self.cpuPower = mw / 1000.0;
    else if ([name isEqualToString:@"GPU Power"]) self.gpuPower = mw / 1000.0;
    else if ([name hasPrefix:@"Combined Power"]) self.combinedPower = mw / 1000.0;
    else if ([name hasPrefix:@"ANE Power"]) self.anePower = mw / 1000.0;
}

- (NSDictionary *)snapshot {
    NSMutableDictionary *d = [NSMutableDictionary new];
    d[@"ts"] = @([[NSDate date] timeIntervalSince1970]);
    d[@"powermetrics"] = @(self.powermetricsAlive);

    NSMutableArray *cpuVals = [NSMutableArray array];
    NSMutableArray *gpuVals = [NSMutableArray array];
    NSMutableArray *memVals = [NSMutableArray array];
    NSMutableArray *sensorList = [NSMutableArray array];

    if (self.smcReady) {
        for (NSString *k in cpuKeys()) {
            NSDictionary *s = readSMC(k);
            if (s && [s[@"value"] doubleValue] > 5 && [s[@"value"] doubleValue] < 118) {
                [cpuVals addObject:s[@"value"]];
                if (sensorList.count < 24) [sensorList addObject:s];
            }
        }
        for (NSString *k in gpuKeys()) {
            NSDictionary *s = readSMC(k);
            if (s && [s[@"value"] doubleValue] > 5 && [s[@"value"] doubleValue] < 118) {
                [gpuVals addObject:s[@"value"]];
                if (sensorList.count < 40) [sensorList addObject:s];
            }
        }
        for (NSString *k in memKeys()) {
            NSDictionary *s = readSMC(k);
            if (s && [s[@"value"] doubleValue] > 5 && [s[@"value"] doubleValue] < 118) {
                [memVals addObject:s[@"value"]];
            }
        }
        NSDictionary *fan = readSMC(@"F0Ac");
        if (fan && [fan[@"value"] doubleValue] >= 0 && [fan[@"value"] doubleValue] < 20000) {
            d[@"fan_rpm"] = fan[@"value"];
        }
        NSDictionary *fanMax = readSMC(@"F0Mx");
        if (fanMax && [fanMax[@"value"] doubleValue] > 0) d[@"fan_max"] = fanMax[@"value"];
    }

    if (cpuVals.count > 0) {
        double maxV = 0, sum = 0;
        for (NSNumber *n in cpuVals) { maxV = MAX(maxV, n.doubleValue); sum += n.doubleValue; }
        d[@"cpu_temp"] = @(maxV);
        d[@"cpu_temp_avg"] = @(sum / cpuVals.count);
        d[@"cpu_sensors"] = @(cpuVals.count);
    }
    if (gpuVals.count > 0) {
        double maxV = 0, sum = 0;
        for (NSNumber *n in gpuVals) { maxV = MAX(maxV, n.doubleValue); sum += n.doubleValue; }
        d[@"gpu_temp"] = @(maxV);
        d[@"gpu_temp_avg"] = @(sum / gpuVals.count);
    }
    if (memVals.count > 0) {
        double maxV = 0;
        for (NSNumber *n in memVals) { maxV = MAX(maxV, n.doubleValue); }
        d[@"mem_temp"] = @(maxV);
    }

    if (self.cpuPower > 0) d[@"cpu_power"] = @(self.cpuPower);
    if (self.gpuPower > 0) d[@"gpu_power"] = @(self.gpuPower);
    if (self.combinedPower > 0) d[@"combined_power"] = @(self.combinedPower);
    if (self.anePower > 0) d[@"ane_power"] = @(self.anePower);
    if (self.pressure.length > 0) d[@"pressure"] = self.pressure;
    if (sensorList.count > 0) d[@"sensors"] = sensorList;
    return d;
}

- (void)writeSnapshot {
    NSDictionary *snap = [self snapshot];
    NSData *json = [NSJSONSerialization dataWithJSONObject:snap options:0 error:nil];
    if (!json) return;
    NSString *tmp = [gOutPath stringByAppendingString:@".tmp"];
    [json writeToFile:tmp atomically:YES];
    [[NSFileManager defaultManager] removeItemAtPath:gOutPath error:nil];
    [[NSFileManager defaultManager] moveItemAtPath:tmp toPath:gOutPath error:nil];
    [[NSFileManager defaultManager] setAttributes:@{NSFilePosixPermissions: @0644}
                                    ofItemAtPath:gOutPath error:nil];
}
@end

int main(int argc, const char *argv[]) {
    @autoreleasepool {
        setupPaths();
        [[NSFileManager defaultManager] createDirectoryAtPath:gRunDir
                                  withIntermediateDirectories:YES
                                                   attributes:@{NSFilePosixPermissions: @0755}
                                                        error:nil];

        int opened = smc_open();
        HMLog(@"helper starting, smc_open=%d", opened);

        Collector *c = [Collector new];
        c.smcReady = (opened == 0);
        if (!c.smcReady) {
            HMLog(@"SMC open failed (%d) - temperature/fan unavailable", opened);
        }
        [c startPowermetrics];

        dispatch_queue_t q = dispatch_queue_create("hm.timer", DISPATCH_QUEUE_SERIAL);
        dispatch_source_t timer = dispatch_source_create(DISPATCH_SOURCE_TYPE_TIMER, 0, 0, q);
        dispatch_source_set_timer(timer, dispatch_time(DISPATCH_TIME_NOW, 0), 1 * NSEC_PER_SEC, 50 * NSEC_PER_MSEC);
        dispatch_source_set_event_handler(timer, ^{
            @autoreleasepool { [c writeSnapshot]; }
        });
        dispatch_resume(timer);
        dispatch_main();
    }
    return 0;
}
