"""Validate private PCIe local tuning records without applying hardware writes.

The record layout follows the local-tunable format used by m1n1. Register
window selection and whether a given record is safe remain hardware-specific.
"""
import struct

_RECORD = struct.Struct('<IIQQ')


def parse_local_tunables(blob, window_size):
    """Return validated (offset, width, mask, value) tuples for a mapped window."""
    if not isinstance(window_size, int) or window_size <= 0:
        raise ValueError('invalid register window size')
    if len(blob) % _RECORD.size:
        raise ValueError('truncated local-tunable record')
    records = []
    for offset, width, mask, value in _RECORD.iter_unpack(blob):
        if width not in (1, 2, 4, 8):
            raise ValueError('unsupported register width')
        if offset % width or offset + width > window_size:
            raise ValueError('unaligned or out-of-range register access')
        if mask >= 1 << (width * 8) or value >= 1 << (width * 8):
            raise ValueError('mask or value exceeds register width')
        records.append((offset, width, mask, value))
    return records
