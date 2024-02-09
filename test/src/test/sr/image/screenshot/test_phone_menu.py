import unittest

import test
from basic import i18_utils
from sr.image.en_ocr_matcher import EnOcrMatcher
from sr.image.sceenshot import phone_menu


class TestOperation(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_in_phone_menu(self):
        i18_utils.update_default_lang('en')
        ocr = EnOcrMatcher()
        img = self.get_test_image('en_1')

        self.assertTrue(phone_menu.in_phone_menu(img, ocr))

