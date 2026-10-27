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


def fixture(model=b'iPad6,11\0', provider=1, calibration=b'PRIVATE_CALIBRATION_SENTINEL',
            battery=False, storage=False, pcie_compatible=b'apcie,s8000\0',
            tuning=b'PRIVATE_TUNABLE_SENTINEL', charging=False):
    word = lambda n: struct.pack('<I', n)
    touch = node('multi-touch', [('compatible', b'multi-touch,j72\0'),
                                ('interrupts', word(65) + word(0)),
                                ('function-reset', word(provider) + b'OIPG' + word(75) + word(65537)),
                                ('multi-touch-calibration', calibration)])
    spi = node('spi3', [('compatible', b'spi-1,samsung\0'), ('reg', word(1)),
                        ('interrupts', word(191)), ('spi-version', word(1)),
                        ('clock-ids', word(304)), ('clock-gates', word(77))], [touch])
    gpio = node('gpio', [('AAPL,phandle', word(1))])
    chosen = node('chosen', [('unique-chip-id', b'IDSECRET')])
    children = [gpio, spi]
    if battery:
        function = word(provider) + b'OIPG' + word(2) + word(258)
        gauge = node('gas-gauge', [('compatible', b'gas-gauge,bq27540\0gas-gauge,hdq\0'),
                                   ('function-battery_swi', function),
                                   ('battery-id-block', b'PRIVATE_BATTERY_ID')])
        children.append(node('uart5', [('compatible', b'uart-1,samsung\0'),
                                       ('reg', word(1)), ('interrupts', word(197)),
                                       ('clock-ids', word(280)), ('function-tx', function)], [gauge]))
    if storage:
        children.append(node('apcie', [('compatible', pcie_compatible), ('reg', word(1)),
                                      ('interrupts', word(244)),
                                      ('apcie-common-tunables', tuning)]))
        children.append(node('nvme-mmu0', [('compatible', b'nvme-mmu,s8000\0'), ('reg', word(2)),
                                          ('interrupts', word(246))]))
    root_children = [chosen]
    if charging:
        children.append(node('i2c0', children=[node('tristar', [('compatible', b'tristar,cbtl1610\0'),
                                                               ('esn', b'PRIVATE_ESN')])]))
        root_children.append(node('charger', [('compatible', b'charger,k48\0'),
                                              ('battery-id', b'PRIVATE_BATTERY_ID'),
                                              ('function-set_charger', b'PRIVATE_FUNCTION')]))
    root_children.append(node('arm-io', children=children))
    return node('device-tree', [('model', model)], root_children)


class J71sReport(unittest.TestCase):
    def test_reports_only_allowed_hardware_data(self):
        result = report(fixture())
        self.assertEqual(result['spi3']['interrupt_words'], [191])
        self.assertEqual(result['spi3']['clock_gate_words'], [77])
        self.assertEqual(result['touch']['functions']['function-reset']['provider'], 'gpio')
        self.assertEqual(result['touch']['functions']['function-reset']['arguments'], [75, 65537])
        self.assertEqual(result['touch']['calibration_bytes'], len(b'PRIVATE_CALIBRATION_SENTINEL'))
        self.assertTrue(result['touch']['calibration_nonzero'])
        output = json.dumps(result)
        self.assertNotIn('IDSECRET', output)
        self.assertNotIn('PRIVATE_CALIBRATION_SENTINEL', output)
        self.assertNotIn('unique-chip-id', output)

    def test_rejects_wrong_model_and_unknown_provider(self):
        for blob in (fixture(model=b'iPad7,5\0'), fixture(provider=99), fixture()[:-3]):
            with self.subTest(size=len(blob)), self.assertRaises(ValueError):
                report(blob)

    def test_zero_filled_calibration_is_not_reported_as_nonzero(self):
        touch = report(fixture(calibration=bytes(1024)))['touch']
        self.assertEqual(touch['calibration_bytes'], 1024)
        self.assertFalse(touch['calibration_nonzero'])

    def test_battery_report_omits_device_specific_properties(self):
        result = report(fixture(battery=True))
        self.assertEqual(result['battery']['uart_interrupt_words'], [197])
        self.assertEqual(result['battery']['gauge_functions']['function-battery_swi']['arguments'], [2, 258])
        self.assertNotIn('PRIVATE_BATTERY_ID', json.dumps(result))

    def test_storage_report_omits_unselected_properties(self):
        result = report(fixture(storage=True))
        self.assertEqual(result['storage']['pcie_interrupt_words'], [244])
        self.assertEqual(result['storage']['nvme_mmu_interrupt_words'], [246])
        self.assertEqual(result['storage']['pcie_common_tunable_records'], 1)
        self.assertNotIn('PRIVATE_TUNABLE_SENTINEL', json.dumps(result))

    def test_storage_rejects_unexpected_controller(self):
        with self.assertRaisesRegex(ValueError, 'Unexpected PCIe'):
            report(fixture(storage=True, pcie_compatible=b'apcie,t8010\0'))

    def test_storage_rejects_truncated_tuning(self):
        with self.assertRaisesRegex(ValueError, 'tunable record length'):
            report(fixture(storage=True, tuning=b'partial'))

    def test_charging_report_omits_device_specific_properties(self):
        result = report(fixture(charging=True))
        self.assertEqual(result['charging']['lightning_controller'], 'tristar,cbtl1610')
        self.assertTrue(result['charging']['set_charger_function_present'])
        encoded = json.dumps(result)
        for secret in ('PRIVATE_ESN', 'PRIVATE_BATTERY_ID', 'PRIVATE_FUNCTION'):
            self.assertNotIn(secret, encoded)


if __name__ == '__main__':
    unittest.main()
