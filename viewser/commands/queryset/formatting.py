
import tabulate
from views_schema import queryset_manager as schema
from viewser.tui.formatting import abc
from . import queryset_list

class QuerysetListTable(abc.Section[queryset_list.QuerysetList]):
    TITLE = "Querysets"
    def compile_output(self, model: queryset_list.QuerysetList) -> str:
        return tabulate.tabulate([(m,) for m in model.querysets], ("name",), tablefmt = "pipe")

class QuerysetTableFormatter(abc.Formatter[queryset_list.QuerysetList]):
    SECTIONS = [
            QuerysetListTable,
        ]

class QuerysetName(abc.Section[schema.DetailQueryset]):
    def compile_output(self, model: schema.DetailQueryset):
        return f"{model.name} at {model.loa}"

class QuerysetDescription(abc.Section[schema.DetailQueryset]):
    TITLE = "Description"

    def compile_output(self, model: schema.DetailQueryset):
        return model.description

class QuerysetSummary(abc.Section[schema.DetailQueryset]):
    TITLE = "Summary"

    def compile_output(self, model: schema.DetailQueryset):
        return f"Queryset has {len(model.operations)} operations"

class QuerysetDetailFormatter(abc.Formatter[schema.DetailQueryset]):
    SECTIONS = [
            QuerysetName,
            QuerysetDescription,
            QuerysetSummary,
        ]

