#!/usr/bin/env python3
"""Report selected J71s wiring from a private ADT; never emit calibration or IDs.

This is an offline bring-up aid, not a device adapter or a claim of support.
Apple function arguments are raw values and must be interpreted independently.
"""
import argparse
import json
from pathlib import Path
import struct

from orchard_cli.apple.adt_tree import parse, u32s
from orchard_hardware.apple.adt import validate

ROOT = '/device-tree/arm-io'
PROVIDERS = {
    ROOT + '/gpio': 'gpio',
    ROOT + '/pmgr': 'pmgr',
    ROOT + '/i2c0/pmu': 'pmu',
}
FUNCTIONS = ('function-clock_enable', 'function-power_ana', 'function-display_sync',
             'function-power_ldo', 'function-reset', 'function-enable_cs')


def report(blob):
    validate(blob)  # Reject malformed trees and ambiguous/missing device identity.
    tree = parse(blob)
    if tree.properties.get('model', b'').rstrip(b'\0') != b'iPad6,11':
        raise ValueError('Expected an iPad6,11 Apple device tree')
    nodes = dict(tree.walk())
    handles = {}
    for path, label in PROVIDERS.items():
        node = nodes.get(path)
        value = node.properties.get('AAPL,phandle') if node else None
        if value is not None:
            if len(value) != 4:
                raise ValueError('Invalid provider handle')
            handle = struct.unpack('<I', value)[0]
            if handle in handles:
                raise ValueError('Ambiguous provider handle')
            handles[handle] = label

    def node(path):
        try:
            return nodes[ROOT + path]
        except KeyError as error:
            raise ValueError('Missing required hardware node: ' + path) from error

    spi, touch = node('/spi3'), node('/spi3/multi-touch')
    if spi.properties.get('compatible', b'').rstrip(b'\0') != b'spi-1,samsung':
        raise ValueError('Unexpected SPI controller compatible')
    if touch.properties.get('compatible', b'').rstrip(b'\0') != b'multi-touch,j72':
        raise ValueError('Unexpected touchscreen compatible')
    wiring = {}
    for name in FUNCTIONS:
        value = touch.properties.get(name)
        if value is None:
            continue
        if len(value) < 8 or len(value) % 4:
            raise ValueError('Invalid hardware function: ' + name)
        handle = struct.unpack('<I', value[:4])[0]
        if handle not in handles:
            raise ValueError('Unknown hardware function provider: ' + name)
        wiring[name] = {'provider': handles[handle], 'operation_hex': value[4:8].hex(),
                        'arguments': u32s(value[8:])}
    return {
        'model': 'iPad6,11',
        'note': 'Raw Apple-tree values; interpretation and address translation need independent verification.',
        'spi3': {'reg_words': u32s(spi.properties['reg']),
                 'interrupt_words': u32s(spi.properties['interrupts']),
                 'version_words': u32s(spi.properties['spi-version']),
                 'clock_id_words': u32s(spi.properties['clock-ids'])},
        'touch': {'interrupt_words': u32s(touch.properties['interrupts']), 'functions': wiring,
                  'calibration_bytes': len(touch.properties.get('multi-touch-calibration', b'')),
                  'calibration_nonzero': any(touch.properties.get('multi-touch-calibration', b''))},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('adt', type=Path, help='private Apple device tree captured from the iPad')
    args = parser.parse_args()
    print(json.dumps(report(args.adt.read_bytes()), indent=2))


if __name__ == '__main__':
    main()
