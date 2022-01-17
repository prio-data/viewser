"""
transform
=========

These classes are used to provide an ergonomic API for end-users, via some
delegation and copying magic. The idea is just to allow users to do this:

    my_column.transform.my_namespace.my_transform(*args)

This returns a new column with the my_namespace.my_transform(*args) transform
appended to the list of column operations.

Not for human consumption.

"""
from views_schema import queryset_manager as schema


class Transform():
    """
    Transform
    =========

    parameters:
        column (viewser.Column): The column to add the transform to
        namespace (str): A prospective transform namespace name
        name (str): A prospective transform name

    Represents a prospective transform. Can be called to return the column with
    the transform operation appended.
    """
    def __init__(self, column, namespace, name):
        self.namespace = namespace
        self.name = name
        self.column = column

    def __call__(self, *arguments):
        op = schema.TransformOperation(
                name = self.namespace + "." + self.name,
                arguments = arguments)

        column = self.column.copy()
        column._add_trf(op)
        return column

class TransformNamespace():
    """
    TransformNamespace
    ==================

    parameters:
        column (viewser.Column): The column to add the transform to
        name (str): A prospective transform namespace name

    Represents a transform namespace

    """
    def __init__(self, column, name: str):
        self.name = name
        self.column = column

    def __getattribute__(self, name):
        if not name in ["column","name"]:
            return Transform(self.column, self.name, name)
        else:
            return super().__getattribute__(name)

class TransformNamespaces():
    """
    TransformNamespaces
    ===================

    parameters:
        column (viewser.Column): The column to add the transform to

    Represents the set of possible transform namespaces.
    """
    def __init__(self, column):
        self.column = column

    def __getattribute__(self, name):
        if not name == "column":
            return TransformNamespace(self.column, name)
        else:
            return super().__getattribute__(name)
