
from unittest import TestCase
from views_schema import ViewsDoc,DocumentationEntry
from viewser.tui.formatting.documentation import DocumentationDetailFormatter

class TestDocumentationFormatter(TestCase):
    def test_basic_formatting(self):
        doc = ViewsDoc(entry = DocumentationEntry(name = "foo"))
        formatted = DocumentationDetailFormatter().formatted(doc)
        for match in ("Foo"):
            self.assertRegex(formatted,match)
