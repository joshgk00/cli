import json
import plistlib
import struct
import unittest

from tools.j71s_n1_inputs import report


def node(name, props=(), children=()):
    def encode(key, value):
        return key.encode().ljust(32, b'\0') + struct.pack('<I', len(value)) + value + b'\0' * (-len(value) % 4)
    records = [('name', name.encode() + b'\0'), *props]
    return struct.pack('<II', len(records), len(children)) + b''.join(encode(*r) for r in records) + b''.join(children)


def fixture(calibration=b'private' * 146 + b'xx', target=b'J71s\0'):
    touch = node('multi-touch', [('compatible', b'multi-touch,j72\0'), ('multi-touch-calibration', calibration)])
    spi = node('spi3', children=[touch])
    return node('device-tree', [('model', b'iPad6,11\0'), ('target-type', target)], [node('arm-io', children=[spi])])


def firmware():
    payload = bytes(57000)
    fields = (len(payload) // 4).to_bytes(2, 'big') + bytes(4)
    packet = bytes.fromhex('18e13001') + fields + sum(fields).to_bytes(2, 'big') + payload + bytes(4)
    return plistlib.dumps({'C1F15,1': {'PreconstructedBootloadPacketType': 'Z2',
                                      'Constructed Firmware Version': 'synthetic',
                                      'Constructed Firmware': packet}})


class N1InputsTests(unittest.TestCase):
    def test_valid_inputs_do_not_expose_calibration(self):
        result = report(fixture(), firmware())
        self.assertEqual(result['calibration_bytes'], 1024)
        self.assertTrue(result['firmware_checksums_valid'])
        self.assertNotIn('private', json.dumps(result))

    def test_wrong_board_and_blank_calibration_are_rejected(self):
        for tree in (fixture(target=b'J71t\0'), fixture(calibration=bytes(1024)),
                     fixture(calibration=b'\xff' * 1024), fixture(calibration=b'x')):
            with self.subTest(tree_size=len(tree)), self.assertRaises(ValueError):
                report(tree, firmware())

    def test_corrupted_firmware_is_rejected(self):
        data = plistlib.loads(firmware())
        packet = bytearray(data['C1F15,1']['Constructed Firmware'])
        packet[12] ^= 1
        data['C1F15,1']['Constructed Firmware'] = bytes(packet)
        with self.assertRaisesRegex(ValueError, 'payload checksum'):
            report(fixture(), plistlib.dumps(data))
