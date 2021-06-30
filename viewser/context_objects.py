from typing import List
import views_schema
from . import formatting, crud

class DocumentationContext():
    def __init__(self,
            documentation_operations: crud.DocumentationCrudOperations,
            formatter: formatting.DocumentationFormatter):
        self.operations = documentation_operations
        self.formatter = formatter

    def format(self,
            doc: views_schema.ViewsDoc,
            formatters: List[formatting.NamedFormatting]):
        return self.formatter.formatted(doc, formatters)

