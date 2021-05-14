from datetime import date
from typing import Optional
import logging
import json
import fire
from requests import HTTPError
from . import settings,crud,models,cli_utils

logger = logging.getLogger(__name__)
class Viewser():
    class queryset():
        @staticmethod
        def fetch(queryset_name:str,outfile:str,
                start_date:Optional[date]=None,end_date:Optional[date]=None):
            """
            Fetch data for a queryset, save it to outfile
            """
            try:
                data = crud.fetch_queryset(queryset_name,start_date,end_date)
            except crud.OperationPending:
                return f"{queryset_name} is being compiled"
            except HTTPError as httpe:
                logger.critical("GET return an error (%s): %s",
                        httpe.response.status_code,
                        httpe.response.content.decode())
                raise RuntimeError from httpe
            data.to_parquet(outfile,compression="gzip")
            return f"Fetched {data.shape[0]} rows, saved to {outfile}"

        @staticmethod
        def load(filename):
            """
            Load a queryset from a JSON file
            """
            with open(filename) as f:
                data = json.load(f)
                queryset = models.Queryset.parse_obj(data)
            try:
                crud.post_queryset(queryset)
            except HTTPError as httpe:
                logger.critical("POST return an error (%s): %s",
                        httpe.response.status_code,
                        httpe.response.content.decode())
                raise RuntimeError from httpe
            else:
                return cli_utils.pprint_json(queryset.json())

        @staticmethod
        def put(filename:str):
            """
            Update queryset
            """
            with open(filename) as f:
                data = json.load(f)
                queryset = models.Queryset.parse_obj(data)
            crud.put_queryset(queryset.name,queryset)
            return cli_utils.pprint_json(queryset.json())

        @staticmethod
        def list():
            """
            List remote querysets
            """
            querysets = crud.list_querysets()
            return querysets

        @staticmethod
        def show(name:str):
            """
            Show detailed information about a queryset
            """
            detail = crud.show_queryset(name)
            return detail

        @staticmethod
        def delete(name:str):
            """
            Show detailed information about a queryset
            """
            detail = crud.delete_queryset(name)
            return detail

    @staticmethod
    def configure():
        """
        Configure viewser
        """
        settings_dict = settings.DEFAULT_SETTINGS.copy()
        for setting in settings.REQUIRED_SETTINGS:
            pretty_setting = setting.replace("_"," ").lower()
            settings_dict[setting] = input(f"Enter {pretty_setting}:\n>> ")
        with open(settings.settings_file_path,"w") as f:
            json.dump(settings_dict,f)
        return json.dumps(settings_dict,indent=4)

def cli():
    fire.Fire(Viewser)
