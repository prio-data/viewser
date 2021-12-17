from typing import Dict, Any
import tabulate
from viewser.formatting import wrapped_views_doc, section


class DocumentationTableSection(section.Section):
    def str_str_dict(self, any_dict: Dict[Any,Any])-> Dict[str,str]:
        return {k:v for k,v in any_dict.items() if isinstance(k,str) and isinstance(v,str)}

    def compile_output(self, model: wrapped_views_doc.WrappedViewsDoc)-> str:
        data = []
        for entry in model.sub_entries:
            row = self.str_str_dict(entry.dict())
            row.update(self.str_str_dict(entry.data))
            data.append(row)
        return tabulate.tabulate(data, headers="keys") + "\n"
