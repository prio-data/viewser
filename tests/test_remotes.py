

import logging
from unittest import TestCase
import responses
from viewser import remotes

null = lambda _: None

class TestRemotes(TestCase):

    @responses.activate
    def test_check_4xx(self):
        responses.add(
                method = "GET",
                url = "http://www.foo.com/bar",
                body = "",
                status = 400,
                )

        def validate(exc):
            self.assertIs(type(exc), remotes.ClientError)

        (remotes.request("http://www.foo.com","GET",[remotes.check_4xx],"bar")
                .either(validate, self.fail)
                )

    @responses.activate
    def test_check_404(self):
        responses.add(
                method = "GET",
                url = "http://www.foo.com/bar",
                body = "",
                status = 404,
                )

        def validate(exc):
            self.assertIs(type(exc), remotes.NotFoundError)

        (remotes.request("http://www.foo.com","GET",[remotes.check_404],"bar")
                .either(validate, self.fail)
                )

    @responses.activate
    def test_check_error(self):
        responses.add(
                method = "GET",
                url = "http://www.foo.com/bar",
                body = "",
                status = 500,
                )

        def validate(exc):
            self.assertIs(type(exc), remotes.RemoteError)

        (remotes.request("http://www.foo.com","GET",[remotes.check_error],"bar")
                .either(validate, self.fail)
                )

    @responses.activate
    def test_check_pending(self):
        responses.add(
                method = "GET",
                url = "http://www.foo.com/bar",
                body = "It's pending",
                status = 202,
                )

        def validate(exc):
            self.assertIs(type(exc), remotes.OperationPending)

        (remotes.request("http://www.foo.com","GET",[remotes.check_pending],"bar")
                .either(validate, self.fail)
                )
