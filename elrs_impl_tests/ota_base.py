from CRSF import CRSF_to_N, CRSF_to_UINT10, CRSF_to_SWITCH3b, UINT10_to_CRSF, BIT_TO_CRSF, N_TO_CRSF, SWITCH3b_to_CRSF, CRSF_CHANNEL_VALUE_MIN, CRSF_CHANNEL_VALUE_MAX, CRSF_NUM_CHANNELS
from OTA import OTA8_PACKET_SIZE, OTA8_CRC_CALC_LEN, OTA4_PACKET_SIZE, OTA4_CRC_CALC_LEN, ELRS_CRC16_POLY, ELRS_CRC14_POLY, OTA_Packet8_s, OTA_Packet4_s, OTA_Channels_4x10
from rx_tx import OTA_VERSION_ID, CURR_MODULATION_SETTINGS
from abc import ABC, abstractmethod
from crc_2_byte import Crc2Byte
from typing import Optional
from enum import IntEnum

PACKET_TYPE_DATA = 0b01
PACKET_TYPE_RCDATA = 0b00
PACKET_TYPE_SYNC = 0b10
PACKET_TYPE_LINKSTATS = 0b00

class OtaSwitchMode(IntEnum):
    smWideOr8ch = 0
    smHybridOr16ch = 1
    sm12ch = 2

def pack_uint11_to_channels_4x10(src: list, use_limit: bool = False) -> OTA_Channels_4x10:
    output = list()

    dest_shift = 0
    curr_index = 0
    output[curr_index] = 0
    for i in range(4):
        ch_val = CRSF_to_UINT10(min(max(src[i], CRSF_CHANNEL_VALUE_MIN), CRSF_CHANNEL_VALUE_MAX)) if use_limit else (src[i] & 0x7FF) >> 1
        
        output[curr_index] |= ch_val << dest_shift
        curr_index += 1

        src_bits_left = 2 + dest_shift
        output[curr_index] = ch_val >> (10 - src_bits_left)
        dest_shift = src_bits_left

    return OTA_Channels_4x10.from_buffer(bytes(output))

def pack_channel_data_hydrid_common(channel_data: list) -> OTA_Packet4_s:
    ota4 = OTA_Packet4_s()
    ota4.rc.type = PACKET_TYPE_RCDATA
    ota4.rc.ch = pack_uint11_to_channels_4x10(channel_data, True)
    ota4.rc.isArmed = True # Hard coded for now
    return ota4

def unpack_channels_4x10_to_uint11(src: OTA_Channels_4x10) -> list:
    output = list()
    
    payload = bytes(src)
    input_channel_mask = (1 << 10) - 1

    bits_merged = 0
    read_value = 0
    read_byte_index = 0
    for i in range(4):
        while bits_merged < 10:
            read_byte = payload[read_byte_index]
            read_byte_index += 1
            read_value |= read_byte << bits_merged
            bits_merged += 8
        
        output[i] = (read_value & input_channel_mask) << 1
        read_value >>= 10
        bits_merged -= 10

    return output

def unpack_channel_data_hybrid_common(ota4: OTA_Packet4_s) -> list:
    channels = unpack_channels_4x10_to_uint11(ota4.rc.ch)

    for i in range(4):
        channels[i] = UINT10_to_CRSF(channels[i] >> 1)

    channels[4] = BIT_TO_CRSF(ota4.rc.isArmed != 0)

    return channels

def hybrid_wide_switch_to_ota(channel_data: list, switch_index: int, low_res: bool) -> int:
    ch = CRSF_to_N(channel_data[switch_index + 4], 64 if low_res else 128)
    return ch & (0b111111 if low_res else 0b1111111)

def hybrid_wide_nonce_to_switch_index(nonce: int) -> int:
    return ((nonce & 0b111) + (nonce >> 3) & 0b1) % 8

class OTABase(ABC):
    def __init__(self, is_rx: bool):
        self.nonce = 0
        self.crc_init = 0
        self.is_rx = is_rx
        self.crc: Optional[Crc2Byte] = None
        self.is_full_res = False
        self.is_high_aux = False
        self.curr_switch_mode = 0
        self.hybrid_8_next_switch_index = 0
        self.telemetry_status = False
        self.is_armed = False

    def update_crc_init_from_uid(self, uid: bytes):
        if len(uid) != 6:
            raise ValueError('\'bytes\' must have length of 6.')
        else:
            self.crc_init = ((uid[4] << 8) | uid[5]) ^ OTA_VERSION_ID

    def update_serializers(self, switch_mode: OtaSwitchMode, packet_size: int):
        self.is_full_res = packet_size == OTA8_PACKET_SIZE
        self.crc = Crc2Byte(16, ELRS_CRC16_POLY) if self.is_full_res else Crc2Byte(14, ELRS_CRC14_POLY)
        self.curr_switch_mode = switch_mode
        self.hybrid_8_next_switch_index = 0
        self.telemetry_status = False
        self.is_armed = False

    def validate_packet_crc(self, ota_packet: OTA_Packet4_s | OTA_Packet8_s) -> bool:
        if self.crc is None:
            raise TypeError('\'crc\' members is of type None, OTA has likely not been configured.')
        
        if self.is_full_res and isinstance(ota_packet, OTA_Packet8_s):
            return self.crc.calc(bytes(ota_packet), self.crc_init) == OTA_Packet8_s(ota_packet).crc
        elif isinstance(ota_packet, OTA_Packet4_s):
            backup_crc_high = ota_packet.crcHigh
            in_crc = (ota_packet.crcHigh << 8) + ota_packet.crcLow
            
            if self.is_rx and ota_packet.type == PACKET_TYPE_RCDATA and self.curr_switch_mode == OtaSwitchMode.smWideOr8ch:
                ota_packet.crcHigh = (self.nonce % CURR_MODULATION_SETTINGS['fhss_hop_interval']) + 1
            else:
                ota_packet.crcHigh = 0

            calced_crc = self.crc.calc(bytes(ota_packet), self.crc_init)
            ota_packet.crcHigh = backup_crc_high

            return in_crc == calced_crc
        else:
            raise TypeError('\'ota_packet\' must be OTA_Packet4_s or OTA_Packet8_s.')
        
    def generate_packet_crc(self, ota_packet: OTA_Packet4_s | OTA_Packet8_s) -> list:
        if self.crc is None:
            raise TypeError('\'crc\' members is of type None, OTA has likely not been configured.')

        output = list()

        if self.is_full_res and isinstance(ota_packet, OTA_Packet8_s):
            output.append(self.crc.calc(bytes(ota_packet), self.crc_init))
        elif isinstance(ota_packet, OTA_Packet4_s):
            if self.is_rx and ota_packet.type == PACKET_TYPE_RCDATA and self.curr_switch_mode == OtaSwitchMode.smWideOr8ch:
                ota_packet.crcHigh = (self.nonce % CURR_MODULATION_SETTINGS['fhss_hop_interval']) + 1

            crc = self.crc.calc(bytes(ota_packet), self.crc_init)

            output.append((crc >> 8) & 0xFF)
            output.append(crc & 0xFF)
        else:
            raise TypeError('\'ota_packet\' must be OTA_Packet4_s or OTA_Packet8_s.')
        
        return output

    def generate_channel_data(self, channel_data: list, telemetry_status: bool, tlm_denom: int) -> OTA_Packet4_s | OTA_Packet8_s:
        if self.is_full_res:
            ota8 = OTA_Packet8_s()
            ota8.rc.packetType = PACKET_TYPE_RCDATA
            ota8.rc.telemetryStatus = telemetry_status
            ota8.rc.uplinkPower = 7 # Hard coded currently
            ota8.rc.isHighAux = self.is_high_aux
            ota8.rc.isArmed = False # Hard coded currently

            is_high_aux = False if self.curr_switch_mode == OtaSwitchMode.smWideOr8ch else self.is_high_aux

            ch_src_low = 0
            ch_src_high = 0
            if self.curr_switch_mode == OtaSwitchMode.smHybridOr16ch:
                if is_high_aux:
                    ch_src_low = 8
                    ch_src_high = 12
                else:
                    ch_src_high = 4
            elif is_high_aux:
                ch_src_high = 8
            else:
                ch_src_high = 4

            if self.curr_switch_mode == OtaSwitchMode.sm12ch:
                self.is_high_aux = not self.is_high_aux

            ota8.rc.chLow = pack_uint11_to_channels_4x10(channel_data[ch_src_low : ch_src_low + 4])
            ota8.rc.chHigh = pack_uint11_to_channels_4x10(channel_data[ch_src_high : ch_src_high + 4])

            return ota8
        elif self.curr_switch_mode == OtaSwitchMode.smWideOr8ch:
            ota4 = pack_channel_data_hydrid_common(channel_data)

            telem_bit = telemetry_status << 6
            next_switch_index = hybrid_wide_nonce_to_switch_index(self.nonce)

            value = 0
            if next_switch_index == 7:
                value = telem_bit
            else:
                telem_every_packet = tlm_denom > 1 and tlm_denom < 8
                value = hybrid_wide_switch_to_ota(channel_data, next_switch_index + 1, telem_every_packet)
                if telem_every_packet:
                    value |= telem_bit

            ota4.rc.switches = value

            return ota4
        else:
            ota4 = pack_channel_data_hydrid_common(channel_data)

            bit_cleared_switch_index = self.hybrid_8_next_switch_index

            value = CRSF_to_N(channel_data[11], 16) if bit_cleared_switch_index == 6 else CRSF_to_SWITCH3b(channel_data[bit_cleared_switch_index + 5])
            ota4.rc.switches = telemetry_status << 6 | bit_cleared_switch_index << 3 | value

            self.hybrid_8_next_switch_index = (bit_cleared_switch_index + 1) % 7

            return ota4
        
    def unpack_channel_data(self, ota_packet: OTA_Packet4_s | OTA_Packet8_s, tlm_denom: int) -> list:
        if self.is_full_res:
            ota8 = OTA_Packet8_s(ota_packet)

            self.is_armed = ota8.rc.isArmed != 0
            self.telemetry_status = ota8.rc.telemetryStatus != 0

            ch_dst_low = 0
            ch_dst_high = 0
            if self.curr_switch_mode == OtaSwitchMode.smHybridOr16ch:
                if ota8.rc.isHighAux:
                    ch_dst_low = 8
                    ch_dst_high = 12
                else:
                    ch_dst_high = 8
            elif ota8.rc.isHighAux:
                ch_dst_high = 8
            else:
                ch_dst_high = 4


            channels_low = unpack_channels_4x10_to_uint11(ota8.rc.chLow)
            channels_high = unpack_channels_4x10_to_uint11(ota8.rc.chHigh)

            channels = [0] * CRSF_NUM_CHANNELS
            channels[ch_dst_low : ch_dst_low + len(channels_low)] = channels_low
            channels[ch_dst_high : ch_dst_high + len(channels_high)] = channels_high

            return channels
        elif self.curr_switch_mode == OtaSwitchMode.smWideOr8ch:
            ota4 = OTA_Packet4_s(ota_packet)

            channels = unpack_channel_data_hybrid_common(ota4)

            switch_byte = ota4.rc.switches
            telem_every_packet = tlm_denom > 1 and tlm_denom < 8
            switch_index = hybrid_wide_nonce_to_switch_index(self.nonce)
            if telem_every_packet or switch_index == 7:
                self.telemetry_status = (switch_byte & 0b01000000) >> 6

            if switch_index != 7:
                bins = 0
                switch_value = 0
                if telem_every_packet:
                    bins = 63
                    switch_value = switch_byte & 0b111111 # 6-bit
                else:
                    bins = 127
                    switch_value = switch_byte & 0b1111111 # 7-bit

                channels[switch_index + 5] = N_TO_CRSF(switch_value, bins)

            return channels
        else:
            ota4 = OTA_Packet4_s(ota_packet)

            channels = unpack_channel_data_hybrid_common(ota4)

            switch_byte = ota4.rc.switches
            switch_index = (switch_byte & 0b111000) >> 3
            if switch_index >= 6:
                # Because AUX1 (index 0) is the low latency switch, the low bit
                # of the switchIndex can be used as data, and arrives as index "6"
                channels[11] = N_TO_CRSF(switch_byte & 0b1111, 15)
            else:
                channels[switch_index + 5] = SWITCH3b_to_CRSF(switch_byte & 0b111)

            self.telemetry_status = switch_byte & (1 << 6)

            return channels