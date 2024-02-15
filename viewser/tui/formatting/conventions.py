
from toolz.functoolz import partial
from tabulate import tabulate as vanilla_tabulate

tabulate = partial(vanilla_tabulate, tablefmt = "pipe")
