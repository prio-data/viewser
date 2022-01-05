
from typing import List
import pydantic

class QuerysetList(pydantic.BaseModel):
    """
    This is a temp fix, alleviating the fact that the queryset manager module doesn't return the right data
    """
    querysets: List[str]
