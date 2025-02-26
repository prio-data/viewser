import pytest
from viewser.commands.queryset.models import Queryset, Column


def test_api():
    qsname = "viewser_test_queryset"

    queryset = (Queryset("viewser_test_queryset", "country_month")
                .with_theme("conflict history")
                .describe("""API testing queryset

                    For testing purposes

                     """)

                .with_column(Column("ged_sum", "priogrid_month", "ged_ns_best_sum_nokgi")
                .aggregate("sum")
                .transform.bool.gte(25)
                                 )

                .with_column(Column("dummy", "priogrid_month", "ged_ns_best_sum_nokgi")
                .aggregate("sum")
                )
            )

    queryset_two = (Queryset("viewser_test_queryset_two", "country_month")
                    .with_theme("conflict history")
                    .describe("""API testing queryset

                        For testing purposes

                         """)

                    .with_column(Column("ged_sum", "priogrid_month", "ged_ns_best_sum_nokgi")
                                 .aggregate("sum")
                                 .transform.bool.gte(25)
                                 )

                    .with_column(Column("dummy", "priogrid_month", "ged_os_best_sum_nokgi")
                                 .aggregate("sum")
                                 )
                    )

    queryset_three = (Queryset("viewser_test_queryset_three", "country_month")
                      .with_theme("conflict history")
                      .describe("""API testing queryset

                            For testing purposes

                             """)

                      .with_column(Column("ged_sum", "priogrid_month", "ged_ns_best_sum_nokgi")
                                   .aggregate("sum")
                                   .transform.bool.gte(25)
                                   )

                      .with_column(Column("dummy_three", "priogrid_month", "ged_os_best_sum_nokgi")
                                   .aggregate("sum")
                                   )
                      )

    queryset_four = (Queryset("viewser_test_queryset_four", "priogrid_month")
                      .with_theme("conflict history")
                      .describe("""API testing queryset

                                For testing purposes

                                 """)

                      .with_column(Column("ged_sum", "priogrid_month", "ged_ns_best_sum_nokgi")
                                   .aggregate("sum")
                                   .transform.bool.gte(25)
                                   )

                      .with_column(Column("dummy_three", "priogrid_month", "ged_os_best_sum_nokgi")
                                   .aggregate("sum")
                                   )
                      )

    chain = queryset.operations[0]

    assert chain[0].namespace == "trf"
    assert chain[0].name == "util.rename"
    assert chain[0].arguments[0] == "ged_sum"

    assert chain[1].namespace == "trf"
    assert chain[1].name == "bool.gte"
    assert chain[1].arguments[0] == "25"

    assert chain[2].namespace == "base"
    assert chain[2].name == "priogrid_month.ged_ns_best_sum_nokgi"
    assert chain[2].arguments[0] == "sum"

    assert len(queryset.operations) == 2

    queryset.publish()

    data = queryset.fetch()

    assert "month_id" in data.index.names
    assert "country_id" in data.index.names
    assert "ged_sum" in data.columns

    queryset_from_storage = queryset.from_storage(qsname)

    data_from_storage = queryset_from_storage.publish().fetch()

    assert data_from_storage.equals(data)

    with pytest.raises(Exception) as e_info:
        queryset_from_merged = Queryset.from_merger([queryset, queryset_two],
                                                    name='viewser_test_queryset_merged')

    with pytest.raises(Exception) as e_info:
        queryset_from_merged = Queryset.from_merger([queryset, queryset_four],
                                                    name='viewser_test_queryset_merged')

    queryset_from_merged = Queryset.from_merger([queryset, queryset_three],
                                                name='viewser_test_queryset_merged')

    assert len(queryset_from_merged.operations) == 3

    data_merged = queryset_from_merged.publish().fetch()

    assert "month_id" in data_merged.index.names
    assert "country_id" in data_merged.index.names
    assert "ged_sum" in data_merged.columns
    assert "dummy" in data_merged.columns
    assert "dummy_three" in data_merged.columns


if __name__ == '__main__':
    test_api()
