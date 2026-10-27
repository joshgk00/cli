import tempfile
import unittest
from pathlib import Path

from tools.usb_power_report import report


class UsbPowerReportTests(unittest.TestCase):
    def test_configuration_is_not_reported_as_measured_power(self):
        with tempfile.TemporaryDirectory() as directory:
            device = Path(directory)
            (device / 'bMaxPower').write_text('500mA\n')
            (device / 'speed').write_text('480\n')
            result = report(device)
            self.assertEqual(result['device_configuration_max_ma'], 500)
            self.assertEqual(result['link_speed_mbps'], 480)
            self.assertFalse(result['host_port_output_measured'])
            self.assertFalse(result['actual_device_input_measured'])

    def test_invalid_attributes_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            device = Path(directory)
            (device / 'bMaxPower').write_text('unknown')
            (device / 'speed').write_text('480')
            with self.assertRaises(ValueError):
                report(device)
            (device / 'bMaxPower').write_text('500mA')
            (device / 'speed').write_text('nan')
            with self.assertRaises(ValueError):
                report(device)
