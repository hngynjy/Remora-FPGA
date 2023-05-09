#ifndef REMORA_H
#define REMORA_H

#define JOINTS              3
#define VARIABLE_OUTPUTS    1
#define VARIABLE_INPUTS     0
#define VARIABLES           1
#define DIGITAL_OUTPUTS     8
#define DIGITAL_INPUTS      8
#define SPIBUFSIZE          20

#define PRU_DATA            0x64617461
#define PRU_READ            0x72656164
#define PRU_WRITE           0x77726974
#define PRU_ESTOP           0x65737470
#define STEPBIT             22
#define STEP_MASK           (1L<<STEPBIT)
#define STEP_OFFSET         (1L<<(STEPBIT-1))
#define PRU_BASEFREQ        PRU_BASEFREQ

typedef union {
    struct {
        uint8_t txBuffer[SPIBUFSIZE];
    };
    struct {
        int32_t header;
        int32_t jointFreqCmd[JOINTS];
        int16_t setPoint[VARIABLE_OUTPUTS];
        uint8_t jointEnable;
        uint8_t outputs;
    };
} txData_t;
static txData_t txData;

typedef union
{
    struct {
        uint8_t rxBuffer[SPIBUFSIZE];
    };
    struct {
        int32_t header;
        int32_t jointFeedback[JOINTS];
        int16_t processVariable[VARIABLE_INPUTS];
        uint8_t inputs;
    };
} rxData_t;
static rxData_t rxData;

#endif
