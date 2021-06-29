import re
import functools
from contextlib import contextmanager
from typing import Dict, List, Any, Optional
from click import HelpFormatter
import tabulate
import colorama
from views_schema import ViewsDoc

def str_str_dict(any_dict: Dict[Any,Any])-> Dict[str,str]:
    return {k:v for k,v in any_dict.items() if isinstance(k,str) and isinstance(v,str)}

def has_page(default=None):
    def wrapper(fn):
        def inner(self, *args,**kwargs):
            if self._views_doc.page is not None:
                return fn(self,*args,**kwargs)
            else:
                return default
        return inner
    return wrapper

class DocumentationFormatter(HelpFormatter):
    _max_data_len = 150
    _divider_length = 32
    _divider_char = "-"

    def __init__(self, views_doc: ViewsDoc, data_name: str = "Data"):
        colorama.init()
        self._views_doc: ViewsDoc = views_doc
        self._data_name = data_name
        super().__init__()

    def set_data_name(self,name):
        self._data_name = name

    @property
    def data(self):
        if self._views_doc.entry.entries:
            entries: List[Dict[str,str]] = []
            for e in self._views_doc.entry.entries:
                table_entry = str_str_dict(e.dict())
                table_entry.update(str_str_dict(e.data))
                entries.append(table_entry)
            entries = [{k:v for k,v in e.items() if len(v) < self._max_data_len} for e in entries]
            entries = [{k.capitalize():v for k,v in e.items()} for e in entries]
        else:
            data = str_str_dict(self._views_doc.entry.data)
            entries = [{"key":k,"value":v} for k,v in data.items()]
        return entries

    @property
    def heading(self):
        return self._views_doc.entry.name.capitalize()

    @property
    @has_page("No description added")
    def description(self):
        return self._views_doc.page.content

    @property
    @has_page("")
    def author(self):
        return self._views_doc.page.author

    @property
    @has_page("")
    def date_updated(self):
        return self._views_doc.page.last_edited.date()

    def table(self):
        table_string = tabulate.tabulate(self.data, headers="keys")
        lines = table_string.split("\n")
        lines = [(" "*self.current_indent) + l for l in lines]
        table_string = "\n".join(lines)
        self.write(table_string)

    def _divider(self):
        self.write_indented("{{SEP}}\n")

    def empty_line(self):
        self.write("\n")

    def formatted(self):
        self.empty_line()
        self.indent()
        self.write_heading(self.heading)
        try:
            with self.section():
                self.write_text(self.description)
                self._divider()
                self.write_text(f"{self.author} @ {self.date_updated}")
        except AttributeError as ae:
            pass

        with self.section(self._data_name):
            self.table()

        rendered = self.getvalue()
        longest_line = max([len(l) for l in rendered.split("\n")])
        return re.sub("{{SEP}}","-"*longest_line,rendered)

    def write_indented(self, str):
        self.write((" "*self.current_indent)+str)

    def write_heading(self, heading: str):
        self.write_indented(
                colorama.Style.BRIGHT + heading.capitalize() + colorama.Style.RESET_ALL + "\n"
            )
        self.empty_line()

    @contextmanager
    def section(self, name: Optional[str] = None):
        if name:
            self.write_heading(name)
        try:
            yield
        finally:
            self.empty_line()

