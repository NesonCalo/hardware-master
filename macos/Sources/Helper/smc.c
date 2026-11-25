#include "smc.h"
#include <string.h>

static io_connect_t gConn = 0;

static UInt32 fourcc(const char *key) {
    return ((UInt32)(unsigned char)key[0] << 24) |
           ((UInt32)(unsigned char)key[1] << 16) |
           ((UInt32)(unsigned char)key[2] << 8) |
           ((UInt32)(unsigned char)key[3]);
}

int smc_open(void) {
    if (gConn) return 0;
    io_service_t service = IOServiceGetMatchingService(kIOMainPortDefault, IOServiceMatching("AppleSMC"));
    if (!service) return -1;
    kern_return_t kr = IOServiceOpen(service, mach_task_self(), 0, &gConn);
    IOObjectRelease(service);
    if (kr != KERN_SUCCESS) { gConn = 0; return -2; }
    return 0;
}

void smc_close(void) {
    if (gConn) { IOServiceClose(gConn); gConn = 0; }
}

int smc_read_key(const char *key, SMCBytes_t out, UInt32 *size, UInt32 *type) {
    if (!gConn) return -3;

    SMCKeyData_t input;
    SMCKeyData_t output;
    memset(&input, 0, sizeof(input));
    memset(&output, 0, sizeof(output));

    input.key = fourcc(key);
    input.data8 = SMC_CMD_READ_KEYINFO;
    size_t outSize = sizeof(output);
    kern_return_t kr = IOConnectCallStructMethod(gConn, KERNEL_INDEX_SMC,
                                                 &input, sizeof(input),
                                                 &output, &outSize);
    if (kr != KERN_SUCCESS) return -4;
    if (output.result != 0) return -5;
    if (output.keyInfo.dataSize > 32) return -6;

    input.keyInfo.dataSize = output.keyInfo.dataSize;
    input.data8 = SMC_CMD_READ_BYTES;
    memset(&output, 0, sizeof(output));
    outSize = sizeof(output);
    kr = IOConnectCallStructMethod(gConn, KERNEL_INDEX_SMC,
                                   &input, sizeof(input),
                                   &output, &outSize);
    if (kr != KERN_SUCCESS) return -7;
    if (output.result != 0) return -8;

    memcpy(out, output.bytes, 32);
    if (size) *size = output.keyInfo.dataSize;
    if (type) *type = output.keyInfo.dataType;
    return 0;
}
