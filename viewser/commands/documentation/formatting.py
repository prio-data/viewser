
import logging
from typing import Optional, Dict, Any

from views_schema import docs as schema

from viewser.tui.formatting import abc, styles, conventions
from . import wrapped_views_doc

logger = logging.getLogger(__name__)

DocumentationSection = abc.Section[wrapped_views_doc.WrappedViewsDoc]

class Title(DocumentationSection):
    def compile_output(self, model: wrapped_views_doc.WrappedViewsDoc) -> str:
        return "> "+ styles.bold(model.heading)

class Description(DocumentationSection):
    TITLE = "Description"

    def compile_output(self, model: wrapped_views_doc.WrappedViewsDoc) -> Optional[str]:
        if model.has_page:
            return "\n".join((
                    model.description,
                    " ",
                    model.author + "@" + model.date_updated,
                    " ",
                ))
        else:
            return None

class FunctionSection(DocumentationSection):
    TITLE = "Function description"

    def compile_output(self, model: wrapped_views_doc.WrappedViewsDoc) -> Optional[str]:
        try:
            signature = model.data["arguments"]

            arguments = ["- " + a["name"] + " (" + a["type"] + ")" for a in signature][1:]
            if arguments:
                sig_description = f"{model.heading} takes {len(arguments)} argument(s):"
                signature_lines = [sig_description] + arguments
            else:
                signature_lines = [f"{model.heading} takes no arguments"]

            if model.data["level_of_analysis"] == "any":
                type_note = "This transform can be applied to any kind of data."
            else:
                type_note = (
                        "This transform can only be applied to "
                        f"data of type {model.data['level_of_analysis']}"
                    )

            modelstring = model.data["docstring"] if model.data["docstring"] is not None else "..."

            return "\n".join((
                "Docstring:",
                "\""+modelstring+"\"",
                " ",
                *signature_lines,
                " ",
                type_note
            ))
        except KeyError:
            #logger.warning("Failed to parse returned documentation")
            return None

class DocumentationTableSection(DocumentationSection):
    def str_str_dict(self, any_dict: Dict[Any,Any])-> Dict[str,str]:
        return {k:v for k,v in any_dict.items() if isinstance(k,str) and isinstance(v,str)}

    def compile_output(self, model: wrapped_views_doc.WrappedViewsDoc)-> str:
        data = []
        for entry in model.sub_entries:
            row = self.str_str_dict(entry.dict())
            row.update(self.str_str_dict(entry.data))
            data.append(row)
        return conventions.tabulate(data, headers="keys", tablefmt = "pipe") + "\n"

class DocumentationFormatter(abc.Formatter[schema.ViewsDoc]):
    def formatted(self, model: schema.ViewsDoc)-> str:
        doc = wrapped_views_doc.WrappedViewsDoc(model)
        return super().formatted(doc)

class DocumentationDetailFormatter(DocumentationFormatter):
    SECTIONS = [
            Title,
            Description,
        ]

class DocumentationTableFormatter(DocumentationFormatter):
    SECTIONS = [
            Title,
            Description,
            DocumentationTableSection
        ]

class FunctionDetailFormatter(DocumentationFormatter):
    SECTIONS = [
            FunctionSection,
            Description
        ]
