from contextlib import contextmanager
import re
from typing import Optional, List
from abc import ABC, abstractmethod
import click
import colorama
from views_schema import docs as schema
from viewser.formatting import wrapped_views_doc, section

class ViewserFormatter(click.HelpFormatter, ABC):
    _max_data_len = 150
    _divider_length = 32
    _divider_char = "-"
    SEPARATOR = "{{SEP}}"

    @property
    @abstractmethod
    def SECTIONS(self)-> List[section.Section]:
        pass

    def __init__(self):
        colorama.init()
        super().__init__()

    def indented(self, str) -> str:
        return "\n".join([(" "*self.current_indent)+ ln for ln in str.split("\n")])

    def divider(self) -> str:
        return self.indented(self.SEPARATOR)

    def write_heading(self, heading: str):
        self.write(self.indented(
                colorama.Style.BRIGHT + heading.capitalize() + colorama.Style.RESET_ALL + "\n"
            ))
        self.write("\n")

    @contextmanager
    def text_in_section(self, name: Optional[str] = None):
        if name:
            self.write(self.indented(">> "+ name)+"\n\n")
        try:
            yield
        finally:
            self.write("\n"+self.indented(self.SEPARATOR)+"\n")

    def formatted(self, model: schema.ViewsDoc):
        doc = wrapped_views_doc.WrappedViewsDoc(model)
        self.write("\n")
        self.indent()

        for s in self.SECTIONS:
            s.add_section(doc, self)

        rendered = self.getvalue()

        longest_line = max([len(l) for l in rendered.split("\n")])
        return re.sub(self.SEPARATOR,"-"*longest_line,rendered)
