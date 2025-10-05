import ast

from bs4 import BeautifulSoup
from django.test import Client, SimpleTestCase, TestCase


class HtmxTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_body_has_htmx_csrftoken_header(self):
        res = self.client.get("/")
        html = BeautifulSoup(res.content, features="html.parser")
        body = html.find("body")
        try:
            hx_headers = body.attrs["hx-headers"]
            hx_headers_val = ast.literal_eval(hx_headers)
            x_csrftoken = hx_headers_val["X-CSRFToken"]
            self.assertEqual(len(x_csrftoken), 64)
        except KeyError:
            self.fail("No 'hx-headers' attribute found on <body> when one was expected")


class CustomErrorViewTemplates(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def test_403_template(self):
        res = self.client.get("/403/")
        path_to_template = res.templates[0].origin.name.split("/")[-3:]

        expected_path = ["testdjereo", "templates", "403.html"]
        self.assertEqual(path_to_template, expected_path)

    def test_404_template(self):
        res = self.client.get("/404/")
        path_to_template = res.templates[0].origin.name.split("/")[-3:]

        expected_path = ["testdjereo", "templates", "404.html"]
        self.assertEqual(path_to_template, expected_path)

    # Cannot test 500 since raising an Exception in a view triggers the debugger (ipdb).
    # def test_500_template(self): ...
