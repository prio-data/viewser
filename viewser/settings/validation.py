
import re
from toolz.functoolz import curry,compose

validate_key = compose(
        curry(re.sub, "[^A-Z_]",""),
        curry(re.sub, "-","_"),
        lambda s: s.upper()
    )
