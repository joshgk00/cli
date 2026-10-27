#!/usr/bin/env python3
"""Summarize selected J71s touch metadata from an offline ipsw kext list.

This examines a locally generated `ipsw kernel kexts --json` report from the
matching, verified iPadOS kernelcache. It does not access hardware, emit
firmware or calibration, or establish that an initialization sequence is safe.
"""
import argparse
import json
from pathlib import Path


FIELDS = ('cal-dl-addr', 'clk32-clock-enable-addr', 'clk32-clock-enable-val',
          'fll-mval', 'fll-mval-addr', 'fw-execute-addr', 'parser-options',
          'parser-type', 'prox-cal-addr', 'reset-deassert-delay', 'touch-size-id')


def report(entries):
    if not isinstance(entries, list):
        raise ValueError('Expected a kext list')
    matches = [item for item in entries if isinstance(item, dict) and
               item.get('id') == 'com.apple.driver.AppleMultitouchSPIC1F15']
    if len(matches) != 1:
        raise ValueError('Expected one J71s touch personality kext')
    personalities = matches[0].get('io_kit_personalities')
    if not isinstance(personalities, dict):
        raise ValueError('Missing touch personalities')
    selected = personalities.get('AppleMultitouchSPI - C1,J72')
    if not isinstance(selected, dict):
        raise ValueError('Missing J72 touch personality')
    if (selected.get('IOClass') != 'AppleMultitouchN1SPI' or
            selected.get('IONameMatch') != ['multi-touch,j72'] or
            selected.get('mt-merge-personality') != 'C1F15,1'):
        raise ValueError('Unexpected touch personality identity')
    values = {}
    for name in FIELDS:
        value = selected.get(name)
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 0xffffffff:
            raise ValueError('Missing or invalid metadata field: ' + name)
        values[name] = value
    return {'class': 'AppleMultitouchN1SPI', 'profile': 'C1F15,1',
            'metadata': values,
            'note': 'Static iPadOS metadata only; runtime values and hardware behavior are unverified.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kext_json', type=Path, help='local ipsw kernel kexts --json output')
    args = parser.parse_args()
    if args.kext_json.stat().st_size > 64 * 1024 * 1024:
        parser.error('Kext list exceeds size limit')
    print(json.dumps(report(json.loads(args.kext_json.read_text())), indent=2))


if __name__ == '__main__':
    main()
