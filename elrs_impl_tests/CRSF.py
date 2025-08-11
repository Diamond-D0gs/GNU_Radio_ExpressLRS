CRSF_CHANNEL_VALUE_MIN = 172 # 987us - actual CRSF min is 0 with E.Limits on.
CRSF_CHANNEL_VALUE_MAX = 1811 # 2012us - actual CRSF max is 1984 with E.Limits on.
CRSF_CHANNEL_VALUE_MID = 992
CRSF_CHANNEL_VALUE_1000 = 191
CRSF_CHANNEL_VALUE_2000 = 1792
CRSF_MAX_PACKET_LEN = 64
CRSF_NUM_CHANNELS = 16

CHANNEL_BIN_COUNT = 6
CHANNEL_BIN_SIZE = (CRSF_CHANNEL_VALUE_MAX - CRSF_CHANNEL_VALUE_MIN) / CHANNEL_BIN_COUNT

def fmap(x: int, in_min: int, in_max: int, out_min: int, out_max: int) -> int:
    return int(out_min + (x - in_min) * (out_max - out_min) / (in_max - in_min))

def CRSF_to_UINT10(val: int) -> int:
    return fmap(val, CRSF_CHANNEL_VALUE_MIN,  CRSF_CHANNEL_VALUE_MAX, 0, 1023)

def CRSF_to_N(val: int, cnt: int) -> int:
    if val <= CRSF_CHANNEL_VALUE_1000:
        return 0
    elif val >= CRSF_CHANNEL_VALUE_2000:
        return cnt - 1
    else:
        return (val - CRSF_CHANNEL_VALUE_1000) * cnt / (CRSF_CHANNEL_VALUE_2000 - CRSF_CHANNEL_VALUE_1000 + 1)
    
def CRSF_to_SWITCH3b(ch: int) -> int:
    if ch < (CRSF_CHANNEL_VALUE_MID - CHANNEL_BIN_SIZE / 4) or ch > (CRSF_CHANNEL_VALUE_MID + CHANNEL_BIN_SIZE / 4):
        return CRSF_to_N(ch, CHANNEL_BIN_COUNT)
    else:
        return 7

def UINT10_to_CRSF(val: int) -> int:
    return fmap(val, 0, 1023, CRSF_CHANNEL_VALUE_MIN, CRSF_CHANNEL_VALUE_MAX)

def BIT_TO_CRSF(val: bool) -> int:
    return CRSF_CHANNEL_VALUE_2000 if val else CRSF_CHANNEL_VALUE_1000

def N_TO_CRSF(val: int, max: int) -> int:
    return val * (CRSF_CHANNEL_VALUE_2000 - CRSF_CHANNEL_VALUE_1000) / max + CRSF_CHANNEL_VALUE_1000

def SWITCH3b_to_CRSF(val: int) -> int:
    if val == 0: return CRSF_CHANNEL_VALUE_1000
    elif val == 5: return CRSF_CHANNEL_VALUE_2000
    elif val == 6 or val == 7: return CRSF_CHANNEL_VALUE_MID
    else: return val * 240 + 391 # (val - 1) * 240 + 630; aka 150us spacing, starting at 1275