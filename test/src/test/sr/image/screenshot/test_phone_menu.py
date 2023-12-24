import unittest

import test
from basic import i18_utils
from sr.image.en_ocr_matcher import EnOcrMatcher
from sr.image.sceenshot import phone_menu


class TestOperation(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

    def test_in_phone_menu(self):
        i18_utils.update_default_lang('en')
        ocr = EnOcrMatcher()
        img = self._get_test_image('en_1')

        self.assertTrue(phone_menu.in_phone_menu(img, ocr))

