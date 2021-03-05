import fire
from viewser.calls import fetch_variable_year

class Viewser():
    @staticmethod
    def fetch_var(outfile:str,loa:str,variable:str,year:int):
        data = fetch_variable_year(loa,variable,year)
        data.to_csv(outfile)
        return f"Fetched {data.shape[0]} rows"

def cli():
    fire.Fire(Viewser)


