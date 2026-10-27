import json
import unittest

from tools.j71s_touch_personality import FIELDS, report


def fixture():
    personality = {key: 0 for key in FIELDS}
    personality.update({'IOClass': 'AppleMultitouchN1SPI',
                        'IONameMatch': ['multi-touch,j72'],
                        'mt-merge-personality': 'C1F15,1',
                        'private-property': 'PRIVATE_SENTINEL'})
    return [{'id': 'com.apple.driver.AppleMultitouchSPIC1F15',
             'io_kit_personalities': {'AppleMultitouchSPI - C1,J72': personality}}]


class TouchPersonalityTests(unittest.TestCase):
    def test_selected_fields_only(self):
        result = report(fixture())
        self.assertEqual(result['profile'], 'C1F15,1')
        self.assertEqual(set(result['metadata']), set(FIELDS))
        self.assertNotIn('PRIVATE_SENTINEL', json.dumps(result))

    def test_wrong_profile_and_duplicate_kext_are_rejected(self):
        data = fixture()
        data[0]['io_kit_personalities']['AppleMultitouchSPI - C1,J72']['mt-merge-personality'] = 'other'
        with self.assertRaises(ValueError):
            report(data)
        with self.assertRaises(ValueError):
            report(fixture() * 2)

    def test_invalid_numeric_metadata_is_rejected(self):
        data = fixture()
        data[0]['io_kit_personalities']['AppleMultitouchSPI - C1,J72']['fll-mval'] = True
        with self.assertRaises(ValueError):
            report(data)
