from typing import Optional
from enum import IntEnum

class SenderState(IntEnum):
    SENDER_IDLE = 0
    SEND_PENDING = 1
    SENDING = 2
    WAIT_UNTIL_NEXT_CONFIRM = 3
    RESYNC = 4
    RESYNC_THEN_SEND = 5

SENDER_MAX_MISSED_PACKETS = 20

class TelemetrySender:
    def __init__(self):
        self.data: Optional[bytes] = None
        self.length = 0
        self.bytes_last_payload = 0
        self.curr_offset = 0
        self.curr_package = 1
        self.max_package_index = 0
        self.telemetry_confirm_expected_val = True
        self.wait_count = 0
        self.max_wait_count = 80
        self.sender_state = SenderState.SENDER_IDLE

    def reset_state(self) -> None:
        self.bytes_last_payload = 0
        self.curr_offset = 0
        self.curr_package = 1
        self.max_package_index = 0
        self.telemetry_confirm_expected_val = True
        self.wait_count = 0
        self.max_wait_count = 80
        self.sender_state = SenderState.SENDER_IDLE

    def set_max_package_index(self, max_package_index: int) -> None:
        if self.max_package_index != max_package_index:
            self.max_package_index = max_package_index
            self.reset_state()

    def set_data_to_transmit(self, data_to_transmit: bytes, len_to_transmit: Optional[int] = None) -> None:
        self.length = len(data_to_transmit) if len_to_transmit is None else len_to_transmit
        self.data = data_to_transmit
        self.curr_offset = 0
        self.curr_package = 1
        self.wait_count = 0
        self.sender_state = SenderState.SEND_PENDING if self.sender_state == SenderState.SENDER_IDLE else SenderState.RESYNC_THEN_SEND

    def get_curr_payload(self, max_len: int) -> tuple[int, Optional[bytes]]:
        if self.data is None:
            raise TypeError('\'data\' is currently None')
        
        output_data = None
        package_index = 0

        bytes_last_payload = 0
        if self.sender_state == SenderState.RESYNC or self.sender_state == SenderState.RESYNC_THEN_SEND: 
            package_index = self.max_package_index
        elif self.sender_state == SenderState.SEND_PENDING or self.sender_state == SenderState.SENDING:
            if self.sender_state == SenderState.SEND_PENDING:
                self.sender_state = SenderState.SENDING

            bytes_last_payload = min(self.length - self.curr_offset, max_len)
            if self.curr_package > 1 and (self.curr_offset + bytes_last_payload) >= self.length:
                package_index = 0
            else:
                package_index = self.curr_package

            output_data = self.data[self.curr_offset : self.curr_offset + bytes_last_payload]

        return (package_index, output_data)
    
    def confirm_curr_payload(self, telemetry_confirm_val: bool) -> None:
        next_sender_state = self.sender_state

        if self.sender_state == SenderState.SENDING:
            if telemetry_confirm_val != self.telemetry_confirm_expected_val:
                self.wait_count += 1
                if self.wait_count > self.max_wait_count:
                    self.telemetry_confirm_expected_val = not telemetry_confirm_val
                    self.sender_state = SenderState.RESYNC
                    return

            self.curr_offset += self.bytes_last_payload
            if self.curr_offset >= self.length:
                if self.curr_package == 1:
                    next_sender_state = SenderState.WAIT_UNTIL_NEXT_CONFIRM
                else:
                    next_sender_state = SenderState.SENDER_IDLE

            self.curr_package += 1
            self.telemetry_confirm_expected_val = not telemetry_confirm_val
            self.wait_count = 0
        elif self.sender_state == SenderState.RESYNC or self.sender_state == SenderState.RESYNC_THEN_SEND or self.sender_state == SenderState.WAIT_UNTIL_NEXT_CONFIRM:
            if telemetry_confirm_val == self.telemetry_confirm_expected_val:
                next_sender_state = SenderState.SENDING if self.sender_state == SenderState.RESYNC_THEN_SEND else SenderState.SENDER_IDLE
                self.telemetry_confirm_expected_val = not telemetry_confirm_val
            elif self.sender_state == SenderState.WAIT_UNTIL_NEXT_CONFIRM:
                self.wait_count += 1
                if self.wait_count > self.max_wait_count:
                    self.telemetry_confirm_expected_val = not telemetry_confirm_val
                    next_sender_state = SenderState.RESYNC

        self.sender_state = next_sender_state

    def update_telemetry_ratio(self, tlm_ratio: int, tlm_burst: int) -> None:
        self.max_wait_count = (tlm_ratio * (1 + tlm_burst) // tlm_burst) * SENDER_MAX_MISSED_PACKETS

    def is_active(self) -> bool:
        return self.sender_state != SenderState.SENDER_IDLE
    
    def get_max_packets_before_resync(self) -> int:
        return self.max_wait_count
    
class TelemetryReceiver:
    def __init__(self):
        self.data: Optional[bytes] = None
        self.finished_data = False
        self.length = 0
        self.curr_offset = 0
        self.curr_package = 1
        self.telemetry_confirm = False
        self.max_package_index = 0

    def reset_state(self) -> None:
        self.curr_offset = 0
        self.curr_package = 1
        self.telemetry_confirm = False

    def set_max_package_index(self, max_package_index: int) -> None:
        if self.max_package_index != max_package_index:
            self.max_package_index = max_package_index
            self.reset_state()

    def get_current_confirm(self) -> bool:
        return self.telemetry_confirm
    
    def set_data_to_receive(self, max_length: int) -> None:
        self.length = max_length
        self.curr_package = 1
        self.curr_offset = 0
        self.finished_data = False

    def receive_data(self, package_index: int, receive_data: int, data_len: int) -> Optional[bytes]:
        if self.data is None:
            raise TypeError('\'data\' is currently None')

        if package_index == self.max_package_index:
            self.telemetry_confirm = not self.telemetry_confirm
            self.curr_package = 1
            self.curr_offset = 0
            self.finished_data = False
            return
        
        if self.finished_data:
            return
        
        accept_data = False
        if package_index == 0 and self.curr_package > 1:
            accept_data = True
            self.finished_data = True
        elif package_index == self.curr_package:
            accept_data = True
        elif package_index == 1 and self.curr_package > 1:
            self.curr_package = 1
            self.curr_offset = 0
            accept_data = True

        output = None
        if accept_data:
            accept_len = min(self.length - self.curr_offset, data_len)
            output = self.data[self.curr_offset : self.curr_offset + accept_len]
            self.curr_package += 1
            self.curr_offset += accept_len
            self.telemetry_confirm = not self.telemetry_confirm

        return output

    def has_finished_data(self) -> bool:
        return self.finished_data
    
    def unlock(self) -> None:
        if self.finished_data:
            self.curr_package = 1
            self.curr_offset = 0
            self.finished_data = False