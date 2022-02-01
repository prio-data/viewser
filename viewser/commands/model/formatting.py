
from views_schema import ModelMetadata
from viewser.tui.formatting import abc
from viewser.tui.formatting import conventions

class ModelMetadataSection(abc.Section[ModelMetadata]):
    TITLE = "Model"
    def compile_output(self, model: ModelMetadata) -> str:
        return conventions.tabulate([
            ("Author",        model.author),
            ("Queryset name", model.queryset_name),
            ("Training interval", f"{model.train_start} to {model.train_end}"),
            ("Steps", ", ".join([str(s) for s in model.steps])),
            ("Trained at", str(model.training_date))
            ])

class ModelMetadataFormatter(abc.Formatter[ModelMetadata]):
    SECTIONS = [
            ModelMetadataSection
        ]
