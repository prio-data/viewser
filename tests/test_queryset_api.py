
from unittest import TestCase
from viewser.commands.queryset.models import Queryset, Column

class TestQuerysetApi(TestCase):
    def test_api(self):
        queryset = (Queryset("my-queryset", "country_month")
            .with_theme("conflict history")
            .describe("""API testing queryset

                For testing purposes

                """)

            .with_column(
                Column("ged_sum","priogrid_month","ged_best_ns")
                    .aggregate("sum")
                    .transform.bool.gte(25)
                )
            .with_column(
                Column("dummy","priogrid_month","ged_best_ns")
                    .aggregate("sum")
                )
            )

        chain = queryset.operations[0]

        self.assertEqual(chain[0].namespace, "trf")
        self.assertEqual(chain[0].name, "util.rename")
        self.assertEqual(chain[0].arguments[0], "ged_sum")

        self.assertEqual(chain[1].namespace, "trf")
        self.assertEqual(chain[1].name, "bool.gte")
        self.assertEqual(chain[1].arguments[0], "25")

        self.assertEqual(chain[2].namespace, "base")
        self.assertEqual(chain[2].name, "priogrid_month.ged_best_ns")
        self.assertEqual(chain[2].arguments[0], "sum")

        self.assertEqual(len(queryset.operations), 2)

    def test_immutable(self):
        col_base = Column("column", "priogrid_month", "ged_best_ns")

        col_a = Column("column", "priogrid_month", "ged_best_ns")

        col_b = col_a.aggregate("sum")

        self.assertEqual(col_base.operations[-1].arguments, col_a.operations[-1].arguments)
        self.assertNotEqual(col_base.operations[-1].arguments, col_b.operations[-1].arguments)
