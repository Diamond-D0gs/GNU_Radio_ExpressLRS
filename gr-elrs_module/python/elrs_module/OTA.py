import ctypes

# --- Constants from ExpressLRS Source ---
# NOTE: These values are derived from the ExpressLRS source for 4-byte headers.
# The payload length for this packet type is 6 bytes. These constants define
# the size of arrays within different payload types.
# (e.g., msp_ul payload is 1 byte for index + 5 bytes for data = 6 bytes total)
ELRS4_MSP_BYTES_PER_CALL = 5
ELRS4_TELEMETRY_BYTES_PER_CALL = 5
ELRS4_TELEMETRY_SHIFT = 2
ELRS4_TELEMETRY_MAX_PACKAGES = 255 >> ELRS4_TELEMETRY_SHIFT
ELRS8_MSP_BYTES_PER_CALL = 10
ELRS8_TELEMETRY_BYTES_PER_CALL = 10
ELRS8_TELEMETRY_SHIFT = 3
ELRS8_TELEMETRY_MAX_PACKAGES = 255 >> ELRS8_TELEMETRY_SHIFT

# Value is implicit leading 1, comment is Koopman formatting (implicit trailing 1) https://users.ece.cmu.edu/~koopman/crc/
ELRS_CRC_POLY = 0x07 # 0x83
ELRS_CRC14_POLY = 0x2E57 # 0x372b
ELRS_CRC16_POLY = 0x3D65 # 0x9eb2

PACKET_TYPE_DATA = 0b01
PACKET_TYPE_RCDATA = 0b00
PACKET_TYPE_SYNC = 0b10
PACKET_TYPE_LINKSTATS = 0b00

# --- Base Structure Definitions ---

class OTA_Sync_s(ctypes.Structure):
    """
    typedef struct {
        uint8_t fhssIndex;
        uint8_t nonce;
        uint8_t rfRateEnum;
        uint8_t switchEncMode:1,
                newTlmRatio:3,
                geminiMode:1,
                otaProtocol:2,
                free:1;
        uint8_t UID4;
        uint8_t UID5;
    } PACKED OTA_Sync_s;
    """
    _pack_ = 1
    _fields_ = [
        ("fhssIndex", ctypes.c_uint8),
        ("nonce", ctypes.c_uint8),
        ("rfRateEnum", ctypes.c_uint8),
        # Bit-fields (LSB to MSB)
        ("switchEncMode", ctypes.c_uint8, 1),
        ("newTlmRatio", ctypes.c_uint8, 3),
        ("geminiMode", ctypes.c_uint8, 1),
        ("otaProtocol", ctypes.c_uint8, 2),
        ("free", ctypes.c_uint8, 1),
        ("UID4", ctypes.c_uint8),
        ("UID5", ctypes.c_uint8),
    ]

class OTA_LinkStats_s(ctypes.Structure):
    """
    typedef struct {
        uint8_t uplink_RSSI_1:7,
                antenna:1;
        uint8_t uplink_RSSI_2:7,
                modelMatch:1;
        uint8_t lq:7,
                tlmConfirm:1;
        int8_t SNR;
    } PACKED OTA_LinkStats_s;
    """
    _pack_ = 1
    _fields_ = [
        # Bit-fields (LSB to MSB)
        ("uplink_RSSI_1", ctypes.c_uint8, 7),
        ("antenna", ctypes.c_uint8, 1),
        ("uplink_RSSI_2", ctypes.c_uint8, 7),
        ("modelMatch", ctypes.c_uint8, 1),
        ("lq", ctypes.c_uint8, 7),
        ("tlmConfirm", ctypes.c_uint8, 1),
        ("SNR", ctypes.c_int8),
    ]

class OTA_Channels_4x10(ctypes.Structure):
    """
    typedef struct {
        uint8_t raw[5];
    } PACKED OTA_Channels_4x10;
    """
    _pack_ = 1
    _fields_ = [
        ("raw", ctypes.c_uint8 * 5),
    ]


# --- Main Packet Definition (OTA_Packet4_s) ---
# C uses anonymous structs and unions, which must be explicitly defined as
# named classes in ctypes before being nested.

# Nested struct for `rc` payload
class _OTA_Packet4_s_rc(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("ch", OTA_Channels_4x10),
        ("switches", ctypes.c_uint8, 7),
        ("isArmed", ctypes.c_uint8, 1),
    ]

# Nested struct for `dbg_linkstats` payload
class _OTA_Packet4_s_dbg_linkstats(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("packetNum", ctypes.c_uint32),
        ("free", ctypes.c_uint8 * 2),
    ]

# Nested struct for `msp_ul` payload
class _OTA_Packet4_s_msp_ul(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("packageIndex", ctypes.c_uint8, 7),
        ("tlmConfirm", ctypes.c_uint8, 1),
        ("payload", ctypes.c_uint8 * ELRS4_MSP_BYTES_PER_CALL),
    ]

# Nested items for `tlm_dl` payload
class _OTA_Packet4_s_tlm_dl_ul_link_stats(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("stats", OTA_LinkStats_s),
        ("trueDiversityAvailable", ctypes.c_uint8, 1),
        ("free", ctypes.c_uint8, 7),
    ]

class _OTA_Packet4_s_tlm_dl_payload(ctypes.Union):
    _pack_ = 1
    _fields_ = [
        ("ul_link_stats", _OTA_Packet4_s_tlm_dl_ul_link_stats),
        ("payload", ctypes.c_uint8 * ELRS4_TELEMETRY_BYTES_PER_CALL),
    ]

class _OTA_Packet4_s_tlm_dl(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("free", ctypes.c_uint8, 1),
        ("tlmConfirm", ctypes.c_uint8, 1),
        ("packageIndex", ctypes.c_uint8, 6),
        ("payload_union", _OTA_Packet4_s_tlm_dl_payload),
    ]

# Nested struct for `airport` payload
class _OTA_Packet4_s_airport(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("free", ctypes.c_uint8, 2),
        ("count", ctypes.c_uint8, 6),
        ("payload", ctypes.c_uint8 * ELRS4_TELEMETRY_BYTES_PER_CALL),
    ]

# The main payload union
class _OTA_Packet4_s_payload(ctypes.Union):
    _pack_ = 1
    _fields_ = [
        ("rc", _OTA_Packet4_s_rc),
        ("dbg_linkstats", _OTA_Packet4_s_dbg_linkstats),
        ("msp_ul", _OTA_Packet4_s_msp_ul),
        ("sync", OTA_Sync_s),
        ("tlm_dl", _OTA_Packet4_s_tlm_dl),
        ("airport", _OTA_Packet4_s_airport),
    ]

# The final, top-level packet structure
class OTA_Packet4_s(ctypes.Structure):
    """
    Main packet structure corresponding to OTA_Packet4_s.
    """
    _pack_ = 1
    _fields_ = [
        # First byte: type and crcHigh
        ("type", ctypes.c_uint8, 2),
        ("crcHigh", ctypes.c_uint8, 6),
        # Main payload union (6 bytes)
        ("payload", _OTA_Packet4_s_payload),
        # Last byte: crcLow
        ("crcLow", ctypes.c_uint8),
    ]

# --- Main Packet Definition (OTA_Packet8_s) ---

# Nested struct for `rc` payload
class _OTA_Packet8_s_rc(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        # Bit-fields (LSB to MSB)
        ("packetType", ctypes.c_uint8, 2),
        ("telemetryStatus", ctypes.c_uint8, 1),
        ("uplinkPower", ctypes.c_uint8, 3),
        ("isHighAux", ctypes.c_uint8, 1),
        ("isArmed", ctypes.c_uint8, 1),
        ("chLow", OTA_Channels_4x10),
        ("chHigh", OTA_Channels_4x10),
    ]

# Nested struct for `dbg_linkstats` payload
class _OTA_Packet8_s_dbg_linkstats(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("packetType", ctypes.c_uint8),
        ("packetNum", ctypes.c_uint32),
        ("free", ctypes.c_uint8 * 6),
    ]

# Nested struct for `msp_ul` payload
class _OTA_Packet8_s_msp_ul(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        # Bit-fields (LSB to MSB)
        ("packetType", ctypes.c_uint8, 2),
        ("packageIndex", ctypes.c_uint8, 5),
        ("tlmConfirm", ctypes.c_uint8, 1),
        ("payload", ctypes.c_uint8 * ELRS8_MSP_BYTES_PER_CALL),
    ]

# Nested struct for `sync` payload
class _OTA_Packet8_s_sync(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("packetType", ctypes.c_uint8),
        ("sync", OTA_Sync_s),
        ("free", ctypes.c_uint8 * 4),
    ]

# Nested items for `tlm_dl` payload
class _OTA_Packet8_s_tlm_dl_ul_link_stats(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("stats", OTA_LinkStats_s),
        # Bit-fields
        ("trueDiversityAvailable", ctypes.c_uint8, 1),
        ("free", ctypes.c_uint8, 7),
        # Payload size calc: total - sizeof(stats) - sizeof(bitfield byte)
        ("payload", ctypes.c_uint8 * (ELRS8_TELEMETRY_BYTES_PER_CALL - ctypes.sizeof(OTA_LinkStats_s) - 1)),
    ]

class _OTA_Packet8_s_tlm_dl_payload(ctypes.Union):
    _pack_ = 1
    _fields_ = [
        ("ul_link_stats", _OTA_Packet8_s_tlm_dl_ul_link_stats),
        ("payload", ctypes.c_uint8 * ELRS8_TELEMETRY_BYTES_PER_CALL),
    ]

class _OTA_Packet8_s_tlm_dl(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        # Bit-fields
        ("packetType", ctypes.c_uint8, 2),
        ("tlmConfirm", ctypes.c_uint8, 1),
        ("packageIndex", ctypes.c_uint8, 5),
        ("payload_union", _OTA_Packet8_s_tlm_dl_payload),
    ]

# Nested struct for `airport` payload
class _OTA_Packet8_s_airport(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        # Bit-fields
        ("packetType", ctypes.c_uint8, 2),
        ("free", ctypes.c_uint8, 1),
        ("count", ctypes.c_uint8, 5),
        ("payload", ctypes.c_uint8 * ELRS8_TELEMETRY_BYTES_PER_CALL),
    ]

# The main payload union for OTA_Packet8_s
class _OTA_Packet8_s_payload(ctypes.Union):
    _pack_ = 1
    _fields_ = [
        ("rc", _OTA_Packet8_s_rc),
        ("dbg_linkstats", _OTA_Packet8_s_dbg_linkstats),
        ("msp_ul", _OTA_Packet8_s_msp_ul),
        ("sync", _OTA_Packet8_s_sync),
        ("tlm_dl", _OTA_Packet8_s_tlm_dl),
        ("airport", _OTA_Packet8_s_airport),
    ]

# The final, top-level packet structure
class OTA_Packet8_s(ctypes.LittleEndianStructure):
    """
    Main packet structure corresponding to OTA_Packet8_s.
    Note: Inherits from LittleEndianStructure to handle the little-endian CRC field.
    """
    _pack_ = 1
    _fields_ = [
        # Main payload union (11 bytes)
        ("payload", _OTA_Packet8_s_payload),
        # Last two bytes: crc16 Little-Endian
        ("crc", ctypes.c_uint16),
    ]

OTA4_PACKET_SIZE = ctypes.sizeof(OTA_Packet4_s)
OTA4_CRC_CALC_LEN = OTA_Packet4_s.crcLow.offset
OTA8_PACKET_SIZE = ctypes.sizeof(OTA_Packet8_s)
OTA8_CRC_CALC_LEN = OTA_Packet8_s.crc.offset