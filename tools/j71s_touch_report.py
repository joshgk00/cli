#!/usr/bin/env python3
"""Check a local J71s touch profile's legacy Z2 packet without accessing hardware.

Packet length and checksums follow the legacy Z2 inspection in
https://github.com/landrucode/a6-handheld-linux/blob/main/scripts/inspect-a6-touch-firmware.py.
Valid checksums do not establish a safe boot or calibration sequence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib


def report(blob):
    if not 0 < len(blob) <= 1024 * 1024:
        raise ValueError('Unexpected profile size')
    props = plistlib.loads(blob)
    if not isinstance(props, dict) or set(props) != {'C1F15,1'}:
        raise ValueError('Unexpected J71s profile set')
    profile = props['C1F15,1']
    if not isinstance(profile, dict) or profile.get('PreconstructedBootloadPacketType') != 'Z2':
        raise ValueError('Unexpected packet type')
    packet = profile.get('Constructed Firmware')
    if not isinstance(packet, bytes) or len(packet) < 16 or packet[:4] != bytes.fromhex('18e13001'):
        raise ValueError('Invalid firmware packet')
    payload_size = int.from_bytes(packet[4:6], 'big') * 4
    if len(packet) != payload_size + 16:
        raise ValueError('Firmware packet length mismatch')
    if int.from_bytes(packet[10:12], 'big') != sum(packet[4:10]):
        raise ValueError('Firmware header checksum mismatch')

    def word32(value):
        return int.from_bytes(value[:2], 'big') | int.from_bytes(value[2:4], 'big') << 16

    if word32(packet[-4:]) != sum(packet[12:-4]):
        raise ValueError('Firmware payload checksum mismatch')
    version = profile.get('Constructed Firmware Version')
    if not isinstance(version, str) or len(version) > 100:
        raise ValueError('Invalid firmware version')
    return {'profile': 'C1F15,1', 'packet_type': 'Z2', 'firmware_version': version,
            'profile_sha256': hashlib.sha256(blob).hexdigest(), 'packet_bytes': len(packet),
            'payload_bytes': payload_size, 'destination': word32(packet[6:10]),
            'checksums_valid': True,
            'note': 'Offline integrity only; hardware initialization remains unverified.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mtprops', type=Path, help='local J71s.mtprops from verified firmware')
    args = parser.parse_args()
    print(json.dumps(report(args.mtprops.read_bytes()), indent=2))


if __name__ == '__main__':
    main()
