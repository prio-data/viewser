from . import remotes, settings

class Docs:
    def __init__(self, remote_base_url: str):
        self._api = remotes.Api("docs
