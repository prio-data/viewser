
from typing import List
from views_schema import viewser as schema
from . import abc

class ErrorSection(abc.Section[schema.Dump]):
    def _messages_of_kind(self, model: schema.Dump, kind: schema.MessageType) -> List[schema.Message]:
        return [m.content for m in model.messages if m.message_type is kind]

class ErrorMessages(ErrorSection):
    TITLE = "Error"

    def compile_output(self, model: schema.Dump) -> str:
        return "\n".join(self._messages_of_kind(model, schema.MessageType.MESSAGE))

class RecoveryHints(ErrorSection):
    TITLE = "Hints"

    def compile_output(self, model: schema.Dump) -> str:
        return "\n".join(self._messages_of_kind(model, schema.MessageType.HINT))

class ErrorFormatter(abc.Formatter[schema.Dump]):
    SECTIONS = [
        ErrorMessages,
        RecoveryHints,
        ]
