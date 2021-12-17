from . import viewser_formatter, generic_sections, documentation_table_section

class DocumentationFormatter(viewser_formatter.ViewserFormatter):
    SECTIONS = [
            generic_sections.Title(),
            generic_sections.Description(),
        ]

class DocumentationTableFormatter(viewser_formatter.ViewserFormatter):
    SECTIONS = [
            generic_sections.Title(),
            generic_sections.Description(),
            documentation_table_section.DocumentationTableSection()
        ]

