#!/usr/bin/env python3
"""Report USB configuration attributes without claiming to measure power."""
import argparse
import json
import math
from pathlib import Path
import re


def report(device: Path) -> dict:
    power = (device / 'bMaxPower').read_text().strip()
    match = re.fullmatch(r'(\d+)mA', power)
    if not match:
        raise ValueError('invalid USB bMaxPower attribute')
    try:
        speed = float((device / 'speed').read_text().strip())
    except ValueError as exc:
        raise ValueError('invalid USB speed attribute') from exc
    if not math.isfinite(speed) or speed <= 0:
        raise ValueError('invalid USB speed attribute')
    return {
        'link_speed_mbps': speed,
        'device_configuration_max_ma': int(match.group(1)),
        'host_port_output_measured': False,
        'actual_device_input_measured': False,
        'note': 'bMaxPower is a device configuration descriptor, not a current measurement or host-port rating',
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('device', type=Path, help='USB device directory in /sys/bus/usb/devices')
    args = parser.parse_args()
    try:
        print(json.dumps(report(args.device), indent=2))
    except (OSError, ValueError) as exc:
        parser.exit(1, f'USB report unavailable: {exc}\n')


if __name__ == '__main__':
    main()
