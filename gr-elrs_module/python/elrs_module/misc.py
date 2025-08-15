PACKET_RATE_LIMIT = 1000
OTA_VERSION_ID = 4

def uid_mac_seed_get(uid: bytes) -> int:
    uid_list = list(uid)
    return ((uid_list[2] << 24) + (uid_list[3] << 16) + (uid_list[4] << 8) + (uid_list[5] ^ OTA_VERSION_ID)) & 0xFFFFFFFF