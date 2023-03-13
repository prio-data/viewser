
from views_schema import queryset_manager as schema
from . import transform, util

class Column():
    """
    Column
    ======

    parameters:
        name (str): Name to give to the resulting column
        from_table (str): Name of table from which to fetch this column
        from_column (str): Name of column in table to fetch

    description
    -----------

    Columns are used when defining querysets. They are defined as lists of
    operations, following a database retrieval operation, that represent
    various transformations of the data.

    help
    ----

    These CLI commands give lists of available columns and transforms:

    Tables and columns:
    ```
    viewser tables list / viewser tables show $TABLE_NAME
    ```

    Transforms:
    ```
    viewser transforms list / viewser transforms show $TRANSFORM_NAME
    ```
    """
    def __init__(self, name: str, from_loa: str, from_column: str, _inject = None ):

        self._name = name
        self._from_loa = from_loa
        self._from_column = from_column

        inject = [] if not _inject else _inject

        self.operations = [
                schema.RenameOperation(arguments=[name]),
                *inject,
                schema.DatabaseOperation(
                    name = from_loa+"."+from_column, arguments = ["values"]
                    )
            ]

        self.namespaces = transform.TransformNamespaces(self)

    def _add_trf(self, trf):
        self.operations.insert(1, trf)

    def aggregate(self, aggregation: str):
        """
        aggregate
        =========

        parameters:
            aggregation (str)

        Choice of aggregation function, if column must be aggregated on
        retrieval: If a column is fetched to a higher level of analysis, such
        as from subnational to national level.

        Valid aggregation functions are:
            - sum
            - max
            - avg
            - min
        """
        cp = self.copy()
        cp.set_aggregation(aggregation)
        return cp 

    def set_aggregation(self, agg):
        self.operations[-1].arguments[0] = agg

    @property
    def aggregation(self):
        return self.operations[-1].arguments[0]

    @property
    def transform(self):
        """
        transform
        =========

        Add a transform to the column. This is done by issuing this kind of
        call, which returns a transformed column:

        ```
        column.transform.namespace.function(*args)
        ```

        `namespace` and `function` must correspond to a valid namespace and a
        valid function name in that namespace. For a list of functions and
        namespaces, run this command on the command line:

        ```
        viewser transforms list
        ```
        """
        return self.namespaces

    def copy(self):
        to_inject = self.operations[1:len(self.operations)-1]
        new = Column(self._name, self._from_loa, self._from_column, _inject = to_inject)
        new.set_aggregation(self.aggregation)
        return new

