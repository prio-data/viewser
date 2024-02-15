from contextlib import contextmanager
import re
from typing import Optional, List, Generic, TypeVar, Callable
from abc import ABC, abstractmethod
import click
import colorama

T = TypeVar("T")

class Section(ABC, Generic[T]):
    """
    Section
    =======

    An output section. Subclass this to create sections that can be written as
    output via a formatter. Subclass, and override the compile_output method,
    which should turn a model T into a string. Override TITLE to add a section
    title.

    example:

        class MyModel(pydantic.BaseModel):
            name: str
            value: int

        class MySection(abc.Section[MyModel]):
            TITLE = "My Model"
            def compile_output(self, model: MyModel):
                return f"{model.name}: {model.value}"
    """

    TITLE: str = ""

    def add_section(self, model: T, formatter: "Formatter")-> None:
        compiled = self.compile_output(model)
        if compiled:
            with formatter.text_in_section(self.TITLE):
                formatter.write(formatter.indented(compiled))

    @abstractmethod
    def compile_output(self, model: T) -> Optional[str]:
        pass

class Formatter(click.HelpFormatter, ABC, Generic[T]):
    """
    Formatter
    =========

    An ABC that can be used to create Formatter classes, which can be used to
    print nice, consistent output across various commands.

    To create a subclass, overwrite the SECTIONS class property with a list of
    Section subclasses. Sections are written as output sequentially.

    example:

        class MyFormatter(abc.Formatter):
            SECTIONS = [
                    HeaderSection,
                    SectionA,
                    SectionB,
                    FooterSection
                ]
    """

    _max_data_len = 150
    _divider_length = 32
    _divider_char = "-"
    SEPARATOR = "{{SEP}}"

    @property
    @abstractmethod
    def SECTIONS(self)-> List[Callable[[], Section[T]]]:
        pass

    def __init__(self):
        self.SECTIONS = [s() for s in self.SECTIONS]
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

    def _format(self, model: T):
        for s in self.SECTIONS:
            s.add_section(model, self)

    def formatted(self, model: T) -> str:
        self.write("\n")
        self.indent()
        self._format(model)
        rendered = self.getvalue()
        longest_line = max([len(l) for l in rendered.split("\n")])
        return re.sub(self.SEPARATOR,"-"*longest_line,rendered)
