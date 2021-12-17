from typing import Any, Optional
from abc import ABC, abstractmethod

class Section(ABC):
    TITLE: str = ""

    def add_section(self, model: Any, formatter: "viewser.formatting.viewser_formatter.ViewserFormatter")-> None:
        compiled = self.compile_output(model)
        if compiled:
            with formatter.text_in_section(self.TITLE):
                formatter.write(formatter.indented(compiled))

    @abstractmethod
    def compile_output(self, model: Any)-> Optional[str]:
        pass
