
import logging
import os
from urllib.parse import urlencode
import requests

logger = logging.getLogger(__name__)

class OperationPending(Exception):
    pass

class RemoteError(Exception):
    pass

def check_response(response):
    if response.status_code == 200:
        pass
    elif response.status_code == 202:
        raise OperationPending
    else:
        raise requests.HTTPError(response=response)

class Api:
    def __init__(self,url,paths):
        self._base_url = url
        self.paths = paths

    def url(self,*args,**kwargs):
        url = os.path.join(self._base_url,*args)

        kwargs = {k:v for k,v in kwargs.items() if v is not None}
        if kwargs:
            url += "?" + urlencode(kwargs)
        return url

    @staticmethod
    def _check_response(response):
        if response.status_code == 200:
            pass
        elif response.status_code == 202:
            raise OperationPending
        elif str(response.status_code)[0] == "5":
            raise RemoteError(
                    f"{response.url} returned {response.status_code}: "
                    f"{response.content.decode()}"
                    )
        else:
            raise requests.HTTPError(response=response)

    def http(self,method,path,parameters,*args,**kwargs):
        url = self.url(*path,**parameters)
        logger.debug("Requesting url %s",url)
        rsp = requests.request(method,url,*args,**kwargs)
        self._check_response(rsp)
        return rsp
