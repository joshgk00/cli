"""Synthetic tests only: no device tree contents or hardware accesses."""
import struct
import unittest
from tools.j71s_pcie_tunables import parse_local_tunables


def record(offset, width, mask=0, value=0):
    return struct.pack('<IIQQ', offset, width, mask, value)


class LocalTunableValidation(unittest.TestCase):
    def test_supported_widths_and_boundary(self):
        blob = record(0, 1, 0xff, 0x10) + record(2, 2, 0xffff, 7) + record(4, 4, 1, 1) + record(8, 8, 1, 2)
        self.assertEqual([x[:2] for x in parse_local_tunables(blob, 16)], [(0, 1), (2, 2), (4, 4), (8, 8)])
        self.assertEqual(parse_local_tunables(b'', 16), [])

    def test_rejects_invalid_records_before_any_caller_can_apply_them(self):
        bad = [b'x', record(0, 3), record(3, 4), record(16, 4),
               record(0, 1, 0x100), record(0, 1, 0, 0x100)]
        for blob in bad:
            with self.subTest(blob=blob), self.assertRaises(ValueError):
                parse_local_tunables(blob, 16)
        with self.assertRaises(ValueError):
            parse_local_tunables(b'', 0)
