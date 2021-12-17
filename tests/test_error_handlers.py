
import datetime
import os
import tempfile
from io import StringIO
import unittest
from views_schema import viewser as schema
from viewser.error_handling import FileErrorHandler, StreamHandler

class TestErrorHandlers(unittest.TestCase):
    def setUp(self):
        self.dump = schema.Dump(
                title = "test-dump",
                timestamp = datetime.datetime.now(),
                messages = [
                        schema.Message(content = "oh no!"),
                        schema.Message(content = "do something!", message_type = schema.MessageType.HINT),
                        schema.Message(content = "fgsfds",        message_type = schema.MessageType.DUMP)
                    ])

    def test_file_handler(self):
        with tempfile.TemporaryDirectory() as dir:
            handler  = FileErrorHandler(dir)
            handler.write(self.dump)

            self.assertTrue(len(os.listdir(dir)), 3)
            for file in os.listdir(dir):
                with open(dir + "/" + file) as f:
                    if schema.MessageType.HINT.name in file:
                        self.assertIn("do something", f.read())
                    elif schema.MessageType.DUMP.name in file:
                        self.assertIn("fgsfds", f.read())
                    elif schema.MessageType.MESSAGE.name in file:
                        self.assertIn("oh no!", f.read())

    def test_stream_handler(self):
        buffer = StringIO()
        handler = StreamHandler(buffer)
        handler.write(self.dump)
        content = buffer.getvalue()
        self.assertIn("oh no!", content)
        self.assertIn("do something!", content)
        self.assertNotIn("fgsfds", content)
