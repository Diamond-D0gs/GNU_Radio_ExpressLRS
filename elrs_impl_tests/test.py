from OTA import OTA_Packet4_s, ELRS_CRC16_POLY
from crc_2_byte import Crc2Byte
import ctypes

if __name__ == '__main__':
    crc2Byte = Crc2Byte(16, ELRS_CRC16_POLY)

    # --- Example 1: Creating a packet from scratch ---
    print("--- Example 1: Creating an RC Data Packet ---")
    
    rc_packet = OTA_Packet4_s()
    
    # Set packet header fields
    rc_packet.type = 0  # 0 corresponds to PACKET_TYPE_RCDATA
    rc_packet.crcHigh = 0b110101 # Some 6-bit value
    
    # Access the 'rc' member of the payload union and populate it
    rc_packet.payload.rc.ch.raw[0] = 100
    rc_packet.payload.rc.ch.raw[1] = 150
    rc_packet.payload.rc.switches = 0b0110101
    rc_packet.payload.rc.isArmed = 1
    
    # Set the final CRC byte
    rc_packet.crcLow = 0xFE
    
    # Verify the values
    print(f"Packet type: {rc_packet.type}")
    print(f"Is Armed: {rc_packet.payload.rc.isArmed}")
    print(f"Switches: {bin(rc_packet.payload.rc.switches)}")
    print(f"Channel 0 Raw: {rc_packet.payload.rc.ch.raw[0]}")
    print(f"Total size of OTA_Packet4_s: {ctypes.sizeof(rc_packet)} bytes\n") # Should be 8

    # --- Example 2: Interpreting a bytes buffer ---
    print("--- Example 2: Interpreting a Sync Packet from bytes ---")
    
    # A sample 8-byte buffer representing a sync packet
    # type=3, crcHigh=0, payload=sync{...}, crcLow=0xFF
    sync_byte_data = b'\x03\x01\x02\x03\x80\x05\x06\xFF'
    
    # Create a packet structure from the byte buffer
    sync_packet = OTA_Packet4_s.from_buffer_copy(sync_byte_data)
    
    # Access the 'sync' member of the payload union and read values
    # The fourth byte of the payload is 0x80 = 10000000b. This sets the 'free'
    # bit-field to 1, as it is the most significant bit.
    print(f"Packet type: {sync_packet.type}")
    print(f"FHSS Index: {sync_packet.payload.sync.fhssIndex}")
    print(f"Nonce: {sync_packet.payload.sync.nonce}")
    print(f"OTA Protocol: {sync_packet.payload.sync.otaProtocol}")
    print(f"Gemini Mode: {sync_packet.payload.sync.geminiMode}")
    print(f"Free bit: {sync_packet.payload.sync.free}")
    print(f"CRC Low: {sync_packet.crcLow}")