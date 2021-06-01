
import json
from importlib.metadata import version
from unittest import TestCase
import httpretty
from viewser import checks,remotes

class TestChecks(TestCase):
    @httpretty.activate()
    def test_check_remote_version(self):

        current_version = version("viewser")
        maj, min, pat = (int(v) for v in current_version.split("."))

        httpretty.register_uri(httpretty.GET, "http://test/", body = json.dumps({
                "viewser_version": f"{maj-1}.{min}.{pat}"
            }))

        self.assertRaises(
                checks.WrongVersion,
                checks.check_remote_version(remotes.Api("http://test",{}))(lambda: None)
            )

        httpretty.register_uri(httpretty.GET, "http://test/", body = json.dumps({
                "viewser_version": f"{maj+1}.{min}.{pat}"
            }))

        self.assertRaises(
                checks.WrongVersion,
                checks.check_remote_version(remotes.Api("http://test",{}))(lambda: None)
            )

        httpretty.register_uri(httpretty.GET, "http://test/", body = json.dumps({
                "viewser_version": f"{maj}.{min}.{pat}"
            }))

        checks.check_remote_version(remotes.Api("http://test",{}))(lambda: None)()
