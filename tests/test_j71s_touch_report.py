import plistlib
import unittest

from tools.j71s_touch_report import report


def profile():
    payload = b'\x01\x02\x03\x04'
    fields = (1).to_bytes(2, 'big') + bytes(4)
    packet = (bytes.fromhex('18e13001') + fields + sum(fields).to_bytes(2, 'big')
              + payload + sum(payload).to_bytes(2, 'big') + bytes(2))
    return {'C1F15,1': {'PreconstructedBootloadPacketType': 'Z2',
                        'Constructed Firmware Version': 'synthetic',
                        'Constructed Firmware': packet}}


class J71sTouchReportTests(unittest.TestCase):
    def test_valid_synthetic_packet(self):
        result = report(plistlib.dumps(profile()))
        self.assertTrue(result['checksums_valid'])
        self.assertEqual(result['payload_bytes'], 4)
        self.assertEqual(result['destination'], 0)

    def test_corrupt_packet_is_rejected(self):
        data = profile()
        packet = bytearray(data['C1F15,1']['Constructed Firmware'])
        packet[12] ^= 1
        data['C1F15,1']['Constructed Firmware'] = bytes(packet)
        with self.assertRaisesRegex(ValueError, 'payload checksum'):
            report(plistlib.dumps(data))

    def test_other_profile_is_rejected(self):
        data = profile()
        data['other'] = data.pop('C1F15,1')
        with self.assertRaisesRegex(ValueError, 'profile set'):
            report(plistlib.dumps(data))
