
from viewser.tui.formatting import generic_models, abc, conventions

class ListSection(abc.Section[generic_models.ListModel]):
    def compile_output(self, model: generic_models.ListModel):
        return conventions.tabulate([(v,) for v in model.values])

class DictSection(abc.Section[generic_models.DictModel]):
    def compile_output(self, model: generic_models.DictModel):
        return conventions.tabulate(list(model.values.items()))
