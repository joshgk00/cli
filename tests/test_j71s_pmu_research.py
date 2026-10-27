import struct
import unittest

from tools.j71s_pmu_research import decode_candidate_row, report


class PmuResearchTests(unittest.TestCase):
    def test_synthetic_row_fields(self):
        row = struct.pack('<HBBBBHHBB', 1000, 25, 8, 15, 0, 0x123, 0x456, 4, 0)
        result = decode_candidate_row(row)
        self.assertEqual(result['candidate_enable_register'], 0x456)
        self.assertEqual(result['candidate_enable_mask'], 4)
        self.assertEqual(result['raw_minimum'], 1000)

    def test_invalid_inputs_rejected(self):
        with self.assertRaises(ValueError):
            decode_candidate_row(b'bad')
        with self.assertRaisesRegex(ValueError, 'does not match'):
            report(b'not a matching kernelcache')
