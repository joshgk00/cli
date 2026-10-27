"""Synthetic J71s reports must never emit identities or calibration blobs."""
import json
import struct
import unittest

from tools.j71s_adt_report import report


def node(name, props=(), children=()):
    records = [('name', name.encode() + b'\0'), *props]
    def prop(key, data):
        return key.encode().ljust(32, b'\0') + struct.pack('<I', len(data)) + data + b'\0' * (-len(data) % 4)
    return struct.pack('<II', len(records), len(children)) + b''.join(prop(k, v) for k, v in records) + b''.join(children)


def fixture(model=b'iPad6,11\0', provider=1):
    word = lambda n: struct.pack('<I', n)
    touch = node('multi-touch', [('compatible', b'multi-touch,j72\0'),
                                ('interrupts', word(65) + word(0)),
                                ('function-reset', word(provider) + b'OIPG' + word(75) + word(65537)),
                                ('multi-touch-calibration', b'PRIVATE_CALIBRATION_SENTINEL')])
    spi = node('spi3', [('compatible', b'spi-1,samsung\0'), ('reg', word(1)),
                        ('interrupts', word(191)), ('spi-version', word(1)),
                        ('clock-ids', word(304))], [touch])
    gpio = node('gpio', [('AAPL,phandle', word(1))])
    chosen = node('chosen', [('unique-chip-id', b'IDSECRET')])
    return node('device-tree', [('model', model)], [chosen, node('arm-io', children=[gpio, spi])])


class J71sReport(unittest.TestCase):
    def test_reports_only_allowed_hardware_data(self):
        result = report(fixture())
        self.assertEqual(result['spi3']['interrupt_words'], [191])
        self.assertEqual(result['touch']['functions']['function-reset']['provider'], 'gpio')
        self.assertEqual(result['touch']['functions']['function-reset']['arguments'], [75, 65537])
        output = json.dumps(result)
        self.assertNotIn('IDSECRET', output)
        self.assertNotIn('PRIVATE_CALIBRATION_SENTINEL', output)
        self.assertNotIn('unique-chip-id', output)

    def test_rejects_wrong_model_and_unknown_provider(self):
        for blob in (fixture(model=b'iPad7,5\0'), fixture(provider=99), fixture()[:-3]):
            with self.subTest(size=len(blob)), self.assertRaises(ValueError):
                report(blob)


if __name__ == '__main__':
    unittest.main()
