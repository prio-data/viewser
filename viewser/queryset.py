from copy import deepcopy
import logging

from . import models, operations

logger = logging.getLogger(__name__)

def deepcopy_self(fn):
    def inner(self, *args,**kwargs):
        return fn(deepcopy(self), *args, **kwargs)
    return inner

class Transform():
    def __init__(self, column, namespace, name):
        self.namespace = namespace
        self.name = name
        self.column = column

    def __call__(self, *arguments):
        op = models.TransformOperation(
                name = self.namespace + "." + self.name,
                arguments = arguments)

        column = self.column.copy()
        column._add_trf(op)
        return column

class TransformNamespace():
    def __init__(self, column, name: str):
        self.name = name
        self.column = column

    def __getattribute__(self, name):
        if not name in ["column","name"]:
            return Transform(self.column, self.name, name)
        else:
            return super().__getattribute__(name)

class TransformNamespaces():
    def __init__(self, column):
        self.column = column

    def __getattribute__(self, name):
        if not name == "column":
            return TransformNamespace(self.column, name)
        else:
            return super().__getattribute__(name)

def col_copy_self(fn):
    def inner(self, *args, **kwargs):
        return fn(self.copy(), *args, **kwargs)
    return inner

class Column():
    def __init__(self, name: str, from_table: str, from_column: str, _inject = None ):

        self._name = name
        self._from_table = from_table
        self._from_column = from_column

        inject = list() if not _inject else _inject

        self.operations = [
                models.RenameOperation(arguments=[name]),
                *inject,
                models.DatabaseOperation(
                    name = from_table+"."+from_column, arguments = ["values"]
                    )
            ]

        self.namespaces = TransformNamespaces(self)

    def _add_trf(self, transform):
        self.operations.insert(1, transform)

    @col_copy_self
    def aggregate(self, aggregation):
        self.set_aggregation(aggregation)
        return self

    def set_aggregation(self, agg):
        self.operations[-1].arguments[0] = agg

    @property
    def aggregation(self):
        return self.operations[-1].arguments[0]

    @property
    def transform(self):
        return self.namespaces

    def copy(self):
        to_inject = self.operations[1:len(self.operations)-1]
        new = Column(self._name, self._from_table, self._from_column, _inject = to_inject)
        new.set_aggregation(self.aggregation)
        return new


class Queryset(models.Queryset):

    def __init__(self, name, at):
        super().__init__(name = name, loa = at, operations = [])

    @deepcopy_self
    def with_column(self, column: Column):
        self.operations.append(column.operations)
        return self

    @deepcopy_self
    def describe(self, description: str):
        self.description = description
        return self

    @deepcopy_self
    def with_theme(self, theme):
        self.themes.append(theme)
        return self

    def publish(self, *args, **kwargs):
        logger.info(f"Publishing queryset {self.name}")
        operations.publish(self, *args, **kwargs)
        return self

    def fetch(self, *args, **kwargs):
        logger.info(f"Fetching queryset {self.name}")
        return operations.fetch(self.name, *args, **kwargs)
