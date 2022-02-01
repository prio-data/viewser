
from . import sections, generic_models, abc

class ListFormatter(abc.Formatter[generic_models.ListModel]):
    SECTIONS = [
            sections.ListSection
        ]

class DictFormatter(abc.Formatter[generic_models.DictModel]):
    SECTIONS = [
            sections.DictSection
        ]
