#ifndef SMC_H
#define SMC_H

#include <stdio.h>
#include <IOKit/IOKitLib.h>

#define KERNEL_INDEX_SMC 2
#define SMC_CMD_READ_BYTES 5
#define SMC_CMD_READ_KEYINFO 9

typedef struct {
    UInt8 major;
    UInt8 minor;
    UInt8 build;
    UInt8 reserved;
    UInt16 release;
} SMCKeyData_vers_t;

typedef struct {
    UInt16 version;
    UInt16 length;
    UInt32 cpuPLimit;
    UInt32 gpuPLimit;
    UInt32 memPLimit;
} SMCKeyData_pLimitData_t;

typedef struct {
    UInt32 dataSize;
    UInt32 dataType;
    UInt8 dataAttributes;
} SMCKeyData_keyInfo_t;

typedef unsigned char SMCBytes_t[32];

typedef struct {
    UInt32 key;
    SMCKeyData_vers_t vers;
    SMCKeyData_pLimitData_t pLimitData;
    UInt32 result;
    UInt8 status;
    UInt8 data8;
    UInt32 data32;
    SMCBytes_t bytes;
    SMCKeyData_keyInfo_t keyInfo;
} SMCKeyData_t;

int smc_open(void);
void smc_close(void);
/* 返回 0 成功；out 为原始 32 字节，size/type 为 SMC 返回的数据长度与类型 */
int smc_read_key(const char *key, SMCBytes_t out, UInt32 *size, UInt32 *type);

#endif
