from .packet_rates import PACKET_RATES
from typing import Optional

FHSS_DOMAINS = {
    "AU915" : {
        "start_freq"  : 915500000,
        "stop_freq"    : 926900000,
        "center_freq" : 921000000,
        "freq_count"  : 20,
    },
    "FCC915" : {
        "start_freq"  : 903500000,
        "stop_freq"    : 926900000,
        "center_freq" : 915000000,
        "freq_count"  : 40,
    },
    "EU868" : {
        "start_freq"  : 865275000,
        "stop_freq"    : 869575000,
        "center_freq" : 868000000,
        "freq_count"  : 13,
    },
    "IN866" : {
        "start_freq"  : 865375000,
        "stop_freq"    : 866950000,
        "center_freq" : 866000000,
        "freq_count"  : 4,
    },
    "AU433" : {
        "start_freq"  : 433420000,
        "stop_freq"    : 434420000,
        "center_freq" : 434000000,
        "freq_count"  : 3,
    },
    "EU433" : {
        "start_freq"  : 433100000,
        "stop_freq"    : 434450000,
        "center_freq" : 434000000,
        "freq_count"  : 3,
    },
    "US433" : {
        "start_freq"  : 433250000,
        "stop_freq"    : 438000000,
        "center_freq" : 434000000,
        "freq_count"  : 8,
    },
    "US433W" : {
        "start_freq"  : 423500000,
        "stop_freq"    : 438000000,
        "center_freq" : 434000000,
        "freq_count"  : 20,
    },
    "ISM2G4" : {
        "start_freq"  : 2400400000,
        "stop_freq"    : 2479400000,
        "center_freq" : 2440000000,
        "freq_count"  : 80,
    }
}

def get_additional_domain_settings(domain: str, packet_rate: int) -> Optional[dict]:
    if domain not in FHSS_DOMAINS:
        raise ValueError('Invalid FHSS domain!')
    if packet_rate not in PACKET_RATES:
        raise ValueError('Invalid packet rate!')
    
    output = {}
    output['sync_pkt_connected'] = 5000
    output['sync_pkt_disconnected'] = 600
    if domain != "ISM2G4":
        output['coding_rate'] = 3
        output['bandwidth'] = 500_000

        match packet_rate:
            case 25:
                output['spread_factor'] = 9
                output['preamble_len'] = 10
                output['tlm_ratio'] = 8
                output['fhss_hop_interval'] = 2
                output['interval_us'] = 40000
            case 50:
                output['spread_factor'] = 8
                output['preamble_len'] = 10
                output['tlm_ratio'] = 16
                output['fhss_hop_interval'] = 4
                output['interval_us'] = 20000
            case 100:
                output['spread_factor'] = 7
                output['preamble_len'] = 8
                output['tlm_ratio'] = 32
                output['fhss_hop_interval'] = 4
                output['interval_us'] = 10000
            case 200:
                output['spread_factor'] = 6
                output['preamble_len'] = 8
                output['tlm_ratio'] = 64
                output['fhss_hop_interval'] = 4
                output['interval_us'] = 5000
            case _:
                return None
    else:
        output['bandwidth'] = 812_500
        
        match packet_rate:
            case 500:
                output['spread_factor'] = 5
                output['coding_rate'] = 2 
                output['preamble_len'] = 12
                output['tlm_ratio'] = 128
                output['fhss_hop_interval'] = 4
                output['interval_us'] = 2000
            case 250:
                output['spread_factor'] = 6
                output['coding_rate'] = 4
                output['preamble_len'] = 14
                output['tlm_ratio'] = 64
                output['fhss_hop_interval'] = 4
                output['interval_us'] = 4000
            case 150:
                output['spread_factor'] = 7
                output['coding_rate'] = 4
                output['preamble_len'] = 12
                output['tlm_ratio'] = 32
                output['fhss_hop_interval'] = 4
                output['interval_us'] = 6666
            case 50:
                output['spread_factor'] = 8
                output['coding_rate'] = 4
                output['preamble_len'] = 12
                output['tlm_ratio'] = 16
                output['fhss_hop_interval'] = 2
                output['interval_us'] = 20000
            case _:
                return None

    return output