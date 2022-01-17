
from unittest import TestCase
import datetime
import httpretty
from views_schema import viewser as schema
from viewser import remotes

class TestErrorPropagation(TestCase):
    @httpretty.activate()
    def test_error_propagation(self):
        error = schema.Dump(
                title = "my-remote-error",
                timestamp = datetime.datetime.now(),
                messages = [
                    schema.Message(content = "something went wrong!!", message_type = schema.MessageType.MESSAGE),
                    schema.Message(content= "this is how to fix it", message_type = schema.MessageType.HINT)])

        httpretty.register_uri(httpretty.GET, "http://httpretty.foo.com/api", body = lambda rq, uri, h: [400, h, error.json()])
        rsp = remotes.request("http://httpretty.foo.com", "GET", [remotes.check_4xx], "api")
        propagated_error = rsp.either(lambda x:x, lambda x:x)
        self.assertEqual(propagated_error,error)

        httpretty.register_uri(httpretty.GET, "http://httpretty.foo.com/api", body = lambda rq, uri, h: [500, h, error.json()])
        rsp = remotes.request("http://httpretty.foo.com", "GET", [remotes.check_error], "api")
        propagated_error = rsp.either(lambda x:x, lambda x:x)
        self.assertEqual(propagated_error,error)
