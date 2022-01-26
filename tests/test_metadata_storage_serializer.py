
from datetime import datetime
import unittest
from viewser.storage import metadata_storage_serializer

class TestMetadataStorageSerializer(unittest.TestCase):
    def test_data_simplification(self):
        should_be_the_same = [
                [1,2,3],
                "a",
                1,
                1.1,
                True,
            ]
        for value in should_be_the_same:
            self.assertEqual(
                    metadata_storage_serializer.simplify_value(value),
                    value)

        is_stringified = [
                datetime.now()
            ]

        for value in is_stringified:
            self.assertEqual(
                    metadata_storage_serializer.simplify_value(value),
                    str(value)
                    )

