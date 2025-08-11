from OTA import OTA4_PACKET_SIZE, OTA8_PACKET_SIZE
from abc import ABC, abstractmethod
from enum import IntEnum
from time import time_ns
from radio import Radio
from hashlib import md5

from FHSS import FHSSHandler

OTA_VERSION_ID = 4
UID_LEN = 6

class RXTimerState(IntEnum):
    TIM_DISCONNECTED = 0
    TIM_TENTATIVE = 1
    TIM_LOCKED = 2

class ExpressLrsRfRates(IntEnum):
    RATE_LORA_900_25HZ = 0
    RATE_LORA_900_50HZ = 1
    RATE_LORA_900_100HZ = 2
    RATE_LORA_900_100HZ_8CH = 3
    RATE_LORA_900_150HZ = 4
    RATE_LORA_900_200HZ = 5
    RATE_LORA_900_200HZ_8CH = 6
    RATE_LORA_900_250HZ = 7
    RATE_LORA_900_333HZ_8CH = 8
    RATE_LORA_900_500HZ = 9
    RATE_LORA_900_50HZ_DVDA = 10

class ExpressLrsTlmRatio(IntEnum):
    TLM_RATIO_STD = 0       # Use suggested ratio from ModParams
    TLM_RATIO_NO_TLM = 1
    TLM_RATIO_1_128 = 2
    TLM_RATIO_1_64 = 3
    TLM_RATIO_1_32 = 4
    TLM_RATIO_1_16 = 5
    TLM_RATIO_1_8 = 6
    TLM_RATIO_1_4 = 7
    TLM_RATIO_1_2 = 8
    TLM_RATIO_DISARMED = 9  # TLM_RATIO_STD when disarmed, TLM_RATIO_NO_TLM when armed

class ConnectionState(IntEnum):
    # Standard connection lifecycle states
    connected = 0
    tentative = 1           # RX only
    awaitingModelId = 2     # TX only
    disconnected = 3
    # A marker to distinguish standard modes from special modes.
    MODE_STATES = 4
    # Special operational modes
    noCrossfire = 5
    bleJoystick = 6
    # A marker for states that should not be saved to configuration.
    NO_CONFIG_SAVE_STATES = 7
    wifiUpdate = 8
    serialUpdate = 9
    # A marker to distinguish normal/special states from failure states.
    FAILURE_STATES = 10
    # Failure states that should be displayed immediately.
    radioFailed = 11
    hardwareUndefined = 12

EXPRESSLRS_AIR_RATE_CONFIG = [
    {
        "index": 0,
        "enum_rate": ExpressLrsRfRates.RATE_LORA_900_200HZ,
        "bw": 500000,
        "sf": 6,
        "cr": 3,
        "preamble_len": 8,
        "tlm_interval": ExpressLrsTlmRatio.TLM_RATIO_1_64,
        "fhss_hop_interval": 4,
        "interval": 5000,
        "payload_length": OTA4_PACKET_SIZE,
        "num_of_sends": 1,
    },
    {
        "index": 1,
        "enum_rate": ExpressLrsRfRates.RATE_LORA_900_100HZ_8CH,
        "bw": 500000,
        "sf": 6,
        "cr": 4,
        "preamble_len": 8,
        "tlm_interval": ExpressLrsTlmRatio.TLM_RATIO_1_32,
        "fhss_hop_interval": 4,
        "interval": 10000,
        "payload_length": OTA8_PACKET_SIZE,
        "num_of_sends": 1,
    },
    {
        "index": 2,
        "enum_rate": ExpressLrsRfRates.RATE_LORA_900_100HZ,
        "bw": 500000,
        "sf": 7,
        "cr": 3,
        "preamble_len": 8,
        "tlm_interval": ExpressLrsTlmRatio.TLM_RATIO_1_32,
        "fhss_hop_interval": 4,
        "interval": 10000,
        "payload_length": OTA4_PACKET_SIZE,
        "num_of_sends": 1,
    },
    {
        "index": 3,
        "enum_rate": ExpressLrsRfRates.RATE_LORA_900_50HZ,
        "bw": 500000,
        "sf": 8,
        "cr": 3,
        "preamble_len": 10,
        "tlm_interval": ExpressLrsTlmRatio.TLM_RATIO_1_16,
        "fhss_hop_interval": 4,
        "interval": 20000,
        "payload_length": OTA4_PACKET_SIZE,
        "num_of_sends": 1,
    },
    {
        "index": 4,
        "enum_rate": ExpressLrsRfRates.RATE_LORA_900_25HZ,
        "bw": 500000,
        "sf": 9,
        "cr": 3,
        "preamble_len": 10,
        "tlm_interval": ExpressLrsTlmRatio.TLM_RATIO_1_8,
        "fhss_hop_interval": 2,
        "interval": 40000,
        "payload_length": OTA4_PACKET_SIZE,
        "num_of_sends": 1,
    },
    {
        "index": 5,
        "enum_rate": ExpressLrsRfRates.RATE_LORA_900_50HZ_DVDA,
        "bw": 500000,
        "sf": 6,
        "cr": 3,
        "preamble_len": 8,
        "tlm_interval": ExpressLrsTlmRatio.TLM_RATIO_1_64,
        "fhss_hop_interval": 2,
        "interval": 5000,
        "payload_length": OTA4_PACKET_SIZE,
        "num_of_sends": 4,
    },
]

CURR_MODULATION_SETTINGS = None

class RxTxBase(ABC):
    def __init__(self, binding_method, domain):
        if isinstance(binding_method, str):
            self.uid = md5(str(f'-DMY_BINDING_PHRASE="{binding_method}"').encode('utf-8')).digest()[:6]
        elif isinstance(binding_method, bytes):
            if len(binding_method) == 6:
                self.uid = binding_method
            else:
                raise ValueError('UID must be bytes of length 6')
        else:
            raise TypeError('\'binding_method\' must be binding phrase str or UID bytes')
        
        self.radio = Radio()
        self.fhss_handler = FHSSHandler(domain, self._uid_mac_seed_get())
        self.connection_state = ConnectionState.connected
        self.next_air_rate_index = 0
        self.rx_timer_state = RXTimerState.TIM_DISCONNECTED
        self.got_connection_millis = 0
        self.already_fhss = False
        self.in_binding_mode = False
        self.invert_IQ = False

    def _uid_mac_seed_get(self) -> int:
        return ((self.uid[2] << 24) + (self.uid[3] << 16) + (self.uid[4] << 8) + (self.uid[5] ^ OTA_VERSION_ID)) & 0xFFFFFFFF

    @abstractmethod
    def run(self):
        pass  

class Receiver(RxTxBase):
    def __init__(self, binding_method, domain):
        super().__init__(binding_method, domain)
        self.binding_mode = False

    def _set_rf_link_rate(self, index, bind_mode) -> None:
        CURR_MODULATION_SETTINGS = EXPRESSLRS_AIR_RATE_CONFIG[index]
        invert_IQ = bind_mode or self.uid[5] & 0x01
        self.radio.config(CURR_MODULATION_SETTINGS['bw'], CURR_MODULATION_SETTINGS['sf'], CURR_MODULATION_SETTINGS['cr'], self.fhss_handler.fhss_sequence[0], CURR_MODULATION_SETTINGS['preamble_len'], invert_IQ, CURR_MODULATION_SETTINGS['payload_len'])

    def _lost_conection(self, resume_rx) -> None:
        self.connection_state = ConnectionState.disconnected
        self.got_connection_millis = 0
        self.already_fhss = False
        
        if self.in_binding_mode:
            pass


    def run(self):
        now = time_ns()

        # Pull data from somewhere

        if self.connection_state != ConnectionState.disconnected and CURR_MODULATION_SETTINGS['index'] != self.next_air_rate_index:
            pass


class Transmitter(RxTxBase):
    def __init__(self, binding_method, domain):
        super().__init__(binding_method, domain)

    def run(self):
        return