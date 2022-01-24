
import unittest

from viewser.settings import validation

class TestConfigResolver(unittest.TestCase):
    def test_validation(self):
        self.assertEqual(validation.validate_key("Abcdef"), "ABCDEF")
        self.assertEqual(validation.validate_key("Abc-Def"), "ABC_DEF")
        self.assertEqual(validation.validate_key("abc123"), "ABC")
