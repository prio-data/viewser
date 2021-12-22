
from unittest import TestCase
import responses
from views_schema import viewser as schema
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
            self.assertIs(type(exc), schema.Dump)
            self.assertEqual(exc.title, "400 client error")
            self.assertIn(schema.MessageType.HINT, {m.message_type for m in exc.messages})

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
            self.assertIs(type(exc), schema.Dump)
            self.assertEqual(exc.title, "404 not found")
            self.assertIn(schema.MessageType.HINT, {m.message_type for m in exc.messages})

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
            self.assertIs(type(exc), schema.Dump)
            self.assertEqual(exc.title, "500 remote error")
            self.assertIn(schema.MessageType.HINT, {m.message_type for m in exc.messages})

        (remotes.request("http://www.foo.com","GET",[remotes.check_error],"bar")
                .either(validate, self.fail)
                )
