from enum import IntEnum

class ConnectionState(IntEnum):
    NO_CONNECTION = 0
    ESTABLISHING_CONNECTION = 1
    CONNECTED = 2