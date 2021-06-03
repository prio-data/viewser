
import os
import webbrowser
import logging
from urllib import parse
import toml
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
    def __init__(self,url,paths=None):
        self._base_url = url
        self.paths = paths

    def url(self,*args,**kwargs):
        url = os.path.join(self._base_url,*args)

        kwargs = {k:v for k,v in kwargs.items() if v is not None}
        if kwargs:
            url += "?" + parse.urlencode(kwargs)
        return url

    @staticmethod
    def check_response(response):
        if response.status_code == 202:
            raise OperationPending

        if str(response.status_code)[0] == "2":
            pass
        elif str(response.status_code)[0] == "5":
            raise RemoteError(
                    f"HTTP {response.status_code}: Something went wrong on the server! "
                    f"Call to {response.url} returned '{response.content.decode()}'"
                    )
        else:
            raise requests.HTTPError(
                    f"HTTP {response.status_code}! "
                    f"Call to {response.url} returned '{response.content.decode()}'"
                    )

    def http(self,method,path,parameters,*args,**kwargs):
        url = self.url(*path,**parameters)
        logger.debug("Requesting url %s",url)
        rsp = requests.request(method,url,*args,**kwargs)
        self.check_response(rsp)
        return rsp

def browser(base,*args,**kwargs):
    webbrowser.open(Api(base).url(*args,**kwargs))

def latest_pyproject_version(repo_url):
    """
    Gets the latest version of the CLI from Github
    """
    repo_path = parse.urlparse(repo_url).path
    url = parse.urljoin("https://raw.githubusercontent.com/",repo_path)
    url = os.path.join(url,"master/pyproject.toml")

    rsp = requests.get(url)
    Api.check_response(rsp)
    pyproject = toml.loads(rsp.content.decode())
    version = pyproject["tool"]["poetry"]["version"]
    logger.debug("Latest version from github: %s",version)
    return version

