import os
from io import BytesIO
import requests
import pandas as pd

from viewser import settings

def fetch_variable_year(loa:str,variable:str,year:int):
    url = os.path.join(
            settings.DATA_ROUTER_URL,
            loa,"base",variable,str(year)
        )+"/"
    data = requests.get(url)
    bio = BytesIO(data.content)
    try:
        df = pd.read_parquet(BytesIO(data.content))
    except:
        raise Exception(url+" "+data.content.decode()+" "+str(data.status_code))
    return df 

if __name__=="__main__":
    print(fetch_variable_year("priogrid_month","priogrid_month.ged_best_ns",2010).head())
