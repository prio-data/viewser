import re
import textwrap
from contextlib import contextmanager
from typing import Dict, List, Any, Optional, Callable, Tuple
from toolz.functoolz import reduce, partial, curry
from click import HelpFormatter
import tabulate
import colorama
from views_schema import ViewsDoc

MAX_CONTENT_WIDTH = 48

wrapped_lines = curry(textwrap.wrap,width=MAX_CONTENT_WIDTH)

def str_str_dict(any_dict: Dict[Any,Any])-> Dict[str,str]:
    return {k:v for k,v in any_dict.items() if isinstance(k,str) and isinstance(v,str)}

def add_line(a:str,b:str)->str:
    return a + "\n" + b

def bold(str)->str:
    return colorama.Style.BRIGHT + str + colorama.Style.RESET_ALL

lines = partial(reduce,add_line)

def help_string(string: str)->Callable[["WrappedViewsDoc"],str]:
    turn_off_message = (
            "Run viewser config unset VERBOSE to "
            "turn off these help messages."
        )

    def inner(doc: "WrappedViewsDoc")->str:
        return lines((
                f"Help for {doc.name}:",
                " ",
                *wrapped_lines(string),
                " ",
                *wrapped_lines(turn_off_message),
            ))
    return inner


def title(doc: "WrappedViewsDoc")->str:
    return lines((
            "> "+bold(doc.heading),
            " ",
        ))

def description(doc: "WrappedViewsDoc")->Optional[str]:
    if doc.has_page:
        return lines((
                *wrapped_lines(doc.description),
                " ",
                doc.author + "@" + doc.date_updated,
                " ",
            ))
    else:
        return None

def function_sig(doc: "WrappedViewsDoc")->str:
    try:
        signature = doc.data["arguments"]

        arguments = ["- " + a["name"] + " (" + a["type"] + ")" for a in signature][1:]
        if arguments:
            sig_description = f"{doc.heading} takes {len(arguments)} argument(s):"
            signature_lines = [sig_description] + arguments
        else:
            signature_lines = [f"{doc.heading} takes no arguments"]

        if doc.data["level_of_analysis"] == "any":
            type_note = "This transform can be applied to any kind of data."
        else:
            type_note = (
                    "This transform can only be applied to "
                    f"data of type {doc.data['level_of_analysis']}"
                )

        docstring = doc.data["docstring"] if doc.data["docstring"] is not None else "..."

        return lines((
            "Docstring:",
            *wrapped_lines("\""+docstring+"\""),
            " ",
            *signature_lines,
            " ",
            *wrapped_lines(type_note)
        ))
    except KeyError:
        return None

def entry_table(doc: "WrappedViewsDoc")->str:
    data = []
    for entry in doc.sub_entries:
        row = str_str_dict(entry.dict())
        row.update(str_str_dict(entry.data))
        data.append(row)
    return tabulate.tabulate(data, headers="keys") + "\n"

class WrappedViewsDoc:
    def __init__(self, doc: ViewsDoc):
        self.doc = doc

    @property
    def name(self):
        return self.doc.entry.name

    @property
    def heading(self):
        return self.name.capitalize()

    @property
    def has_page(self):
        return self.doc.page is not None

    @property
    def description(self):
        return self.doc.page.content if self.has_page else "No description added"

    @property
    def author(self):
        return self.doc.page.author if self.has_page else None

    @property
    def date_updated(self):
        return str(self.doc.page.last_edited.date()) if self.has_page else None

    @property
    def sub_entries(self):
        return self.doc.entry.entries

    @property
    def data(self):
        return self.doc.entry.data

    def json(self):
        return self.doc.json()

NamedFormatting = Tuple[str, Callable[["WrappedViewsDoc"], str]]

class DocumentationFormatter(HelpFormatter):
    _max_data_len = 150
    _divider_length = 32
    _divider_char = "-"
    SEPARATOR = "{{SEP}}"

    def __init__(self):
        colorama.init()
        super().__init__()

    def indented(self, str) -> str:
        return "\n".join([(" "*self.current_indent)+ ln for ln in str.split("\n")])

    def divider(self) -> str:
        return self.indented(self.SEPARATOR)

    def formatted(self, doc: ViewsDoc, formatters: List[Optional[NamedFormatting]]):
        doc = WrappedViewsDoc(doc)
        self.write("\n")
        self.indent()

        formatters = (fmt for fmt in formatters if fmt is not None)

        for name, formatter in formatters:
            output = formatter(doc)
            if output:
                with self.section(name):
                    self.write(self.indented(output))

        rendered = self.getvalue()

        longest_line = max([len(l) for l in rendered.split("\n")])
        return re.sub(self.SEPARATOR,"-"*longest_line,rendered)

    def write_heading(self, heading: str):
        self.write(self.indented(
                colorama.Style.BRIGHT + heading.capitalize() + colorama.Style.RESET_ALL + "\n"
            ))
        self.write("\n")

    @contextmanager
    def section(self, name: Optional[str] = None):
        if name:
            self.write(self.indented(">> "+ name)+"\n\n")
        try:
            yield
        finally:
            self.write("\n"+self.indented(self.SEPARATOR)+"\n")
