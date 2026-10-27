#!/usr/bin/env python3
"""Inspect one candidate D2365 rail descriptor in a matching local kernelcache.

This is offline research, not a PMU driver or a register-access tool. The
relationship between the Apple tree function argument and this descriptor is
inferred from another PMU and requires confirmation for D2365.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

KERNEL_SHA256 = '4242a4d2cc20e08bc6abe69546c540a884209e6c85a0638841e592ca1f1e57a2'
TABLE_OFFSET = 0xff2092
ROW_SIZE = 12
CANDIDATE_INDEX = 31


def decode_candidate_row(row: bytes) -> dict:
    if len(row) != ROW_SIZE:
        raise ValueError('invalid D2365 descriptor length')
    minimum, step, max_selector, voltage_mask, extra, voltage_reg, enable_reg, enable_mask, reserved = struct.unpack('<HBBBBHHBB', row)
    return {'candidate_index': CANDIDATE_INDEX,
            'raw_minimum': minimum, 'raw_step': step,
            'max_selector': max_selector, 'voltage_mask': voltage_mask,
            'raw_extra': extra, 'raw_voltage_register': voltage_reg,
            'candidate_enable_register': enable_reg,
            'candidate_enable_mask': enable_mask, 'raw_reserved': reserved}


def report(kernel: bytes) -> dict:
    if hashlib.sha256(kernel).hexdigest() != KERNEL_SHA256:
        raise ValueError('kernelcache does not match the researched iPadOS build')
    start = TABLE_OFFSET + CANDIDATE_INDEX * ROW_SIZE
    result = decode_candidate_row(kernel[start:start + ROW_SIZE])
    result['note'] = ('Offline candidate only. The tree argument, descriptor layout, '
                      'rail identity, voltage and safe register access are not validated.')
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kernelcache', type=Path, help='locally extracted matching kernelcache')
    args = parser.parse_args()
    try:
        print(json.dumps(report(args.kernelcache.read_bytes()), indent=2))
    except (OSError, ValueError) as exc:
        parser.exit(1, f'PMU report unavailable: {exc}\n')


if __name__ == '__main__':
    main()
