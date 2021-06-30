
from unittest import TestCase
from views_schema import ViewsDoc,DocumentationEntry
from viewser.formatting import DocumentationFormatter

class TestDocumentationFormatter(TestCase):
    def test_basic_formatting(self):
        doc = ViewsDoc(entry = DocumentationEntry(name = "foo"))
        formatted = DocumentationFormatter().formatted(
            doc,
            [
                ("Test",lambda x: x.heading)
            ]
        )
        for match in ("Test", "Foo"):
            self.assertRegex(formatted,match)
