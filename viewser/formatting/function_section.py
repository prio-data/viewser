from typing import Optional
from viewser.formatting import section, wrapped_views_doc


class FunctionSection(section.Section):
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

            modelstring = model.data["modelstring"] if model.data["modelstring"] is not None else "..."

            return "\n".join((
                "Docstring:",
                "\""+modelstring+"\"",
                " ",
                *signature_lines,
                " ",
                type_note
            ))
        except KeyError:
            return None
