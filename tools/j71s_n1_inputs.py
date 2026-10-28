#!/usr/bin/env python3
"""Check private J71s touch inputs against the J71t N1 driver's packet rules.

This is an offline comparison, not a firmware extractor or hardware test.
Neither calibration bytes nor device identifiers are printed or written.
"""
import argparse
import json
from pathlib import Path

from orchard_cli.apple.adt_tree import parse
from tools.j71s_touch_report import report as firmware_report


def report(adt, mtprops):
    tree = parse(adt)
    if (tree.properties.get('model', b'').rstrip(b'\0') != b'iPad6,11'
            or tree.properties.get('target-type', b'').rstrip(b'\0') != b'J71s'):
        raise ValueError('Expected the J71s iPad6,11 device tree')
    touch = dict(tree.walk()).get('/device-tree/arm-io/spi3/multi-touch')
    if touch is None or touch.properties.get('compatible', b'').rstrip(b'\0') != b'multi-touch,j72':
        raise ValueError('Expected the J71s multi-touch node')
    calibration = touch.properties.get('multi-touch-calibration', b'')
    if len(calibration) != 1024 or not any(calibration) or all(x == 255 for x in calibration):
        raise ValueError('N1 calibration must be 1024 bytes and not blank')
    fw = firmware_report(mtprops)
    if fw['packet_bytes'] != 57016 or fw['destination'] != 0:
        raise ValueError('Firmware does not match the J71t N1 driver packet constraints')
    return {'device': 'J71s', 'calibration_bytes': len(calibration),
            'firmware_packet_bytes': fw['packet_bytes'],
            'firmware_checksums_valid': fw['checksums_valid'],
            'note': 'Offline checks only; hardware operation is unverified.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('adt', type=Path)
    parser.add_argument('mtprops', type=Path)
    args = parser.parse_args()
    print(json.dumps(report(args.adt.read_bytes(), args.mtprops.read_bytes()), indent=2))


if __name__ == '__main__':
    main()
