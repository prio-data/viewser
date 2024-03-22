import logging
from views_schema import queryset_manager as schema
from viewser.commands.queryset.operations import QuerysetOperations
from viewser import settings
from viewser.settings import defaults
from . import column, util

logger = logging.getLogger(__name__)
queryset_operations = QuerysetOperations(
        settings.QUERYSET_URL,
        defaults.default_error_handler())

class Queryset(schema.Queryset):
    """
    Queryset
    ========

    parameters:
        name (str): Unique name
        to_loa (str): desired level of analysis

    example:
        queryset = (Queryset("my-queryset", "country_month")
            .with_column(Column("a", "from-loa-a", "column-a", "agg-fn-a")
                .transform.functions.my_function())
            .with_column(Column("b", "from-loa-b", "column-b", "agg-fn-b"))

        dataset = queryset.publish().fetch()

    description
    -----------

    A queryset is a data definition that can be used to fetch dynamically
    defined data from views3. Querysets are collections of Column objects,
    combined with a level of analysis definition, that define what data is
    fetched.

    Most methods can be chained, allowing for concise, readable queryset
    definitions.
    """
    def __init__(self, name, loa):
        super().__init__(name=name, loa=loa, operations=[])

    @classmethod
    def from_merger(cls, querysets, name, theme=None, description=None, verbose=False):

        def rename_to_string(column):
            rename_string = ''.join([column[0].namespace, column[0].name, str(column[0].arguments)])
            return rename_string

        def database_to_string(column):
            database_string = ''.join([column[-1].namespace, column[-1].name, str(column[-1].arguments)])
            return database_string

        def transform_to_string(column):
            transform_string = ''.join(
                [column[i].namespace + column[i].name + str(column[i].arguments) for i in range(1, len(column) - 1)])
            return transform_string

        loas = [queryset.loa for queryset in querysets]

        if len(set(loas)) > 1:
            raise RuntimeError(f'querysets cannot be merged - they are defined at different loas {loas}')

        columns = []
        rename_strings = []
        database_strings = []
        transform_strings = []

        for queryset in querysets:
            for column in queryset.operations:

                rename_string = rename_to_string(column)
                database_string = database_to_string(column)
                transform_string = transform_to_string(column)

                if len(rename_strings) == 0:
                    rename_strings.append(rename_string)
                    database_strings.append(database_string)
                    transform_strings.append(transform_string)
                    columns.append(column)
                else:
                    if rename_string in rename_strings:
                        idx = rename_strings.index(rename_string)

                        if database_string != database_strings[idx]:
                            raise RuntimeError(
                                f'querysets cannot be merged - two columns named {column[0].arguments[0]} '
                                f'with different raw data')

                        if transform_string != transform_strings[idx]:
                            raise RuntimeError(
                                f'querysets cannot be merged - two columns named {column[0].arguments[0]} '
                                f'with different xforms')
                        if verbose:
                            print(f'Merging querysets: omitting copy of identically-defined '
                                  f'column {column[0].arguments[0]}')
                    else:
                        rename_strings.append(rename_string)
                        database_strings.append(database_string)
                        transform_strings.append(transform_string)
                        columns.append(column)

        qs_merged = cls(name=name, loa=loas[0])

        qs_merged.operations = columns
        qs_merged.themes = [] if theme is None else [theme,]
        qs_merged.description = description

        return qs_merged

    @util.deepcopy_self
    def with_column(self, col: column.Column):
        """
        with_column
        ===========

        parameters:
            col (viewser.Column)
        returns:
            self

        Add a column to the queryset
        """
        self.operations.append(col.operations)
        return self

    @util.deepcopy_self
    def describe(self, description: str):
        """
        describe
        ========

        parameters:
            description (str): Long-form description of the queryset

        returns:
            self
        """
        self.description = description
        return self

    @util.deepcopy_self
    def with_theme(self, theme):
        """
        with_theme
        ==========

        parameters:
            theme (str): A theme-name to associate with the queryset

        returns:
            self

        Associate the queryset with a theme, which can be any semantically
        meaningful string.
        """
        self.themes.append(theme)
        return self

    def publish(self, *args, **kwargs):
        """
        publish
        =======

        returns:
            self

        Publish the queryset to ViEWS 3, making it available to yourself and
        other users.
        """
        logger.info(f"Publishing queryset {self.name}")
        queryset_operations.publish(self, *args, **kwargs)
        return self

    def fetch(self, *args, **kwargs):
        """
        fetch
        =====

        returns:
            pandas.DataFrame

        Fetch the dataset corresponding to this queryset in its current state.
        Requires a self.push first.
        """
        logger.info(f"Fetching queryset {self.name}")
        dataset = queryset_operations.fetch(self.name)
        return dataset
