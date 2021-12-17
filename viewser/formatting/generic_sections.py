
from typing import Optional
from viewser.formatting import section, wrapped_views_doc, styles

class Title(section.Section):
    def compile_output(self, model: wrapped_views_doc.WrappedViewsDoc)-> str:
        return "> "+ styles.bold(model.heading)

class Description(section.Section):
    TITLE = "Description"

    def compile_output(self, model: wrapped_views_doc.WrappedViewsDoc)-> Optional[str]:
        if model.has_page:
            return "\n".join((
                    model.description,
                    " ",
                    model.author + "@" + model.date_updated,
                    " ",
                ))
        else:
            return None
