from unittest import mock

from django.test import RequestFactory, SimpleTestCase

from testdjereo.context_processors import metadata


@mock.patch("testdjereo.context_processors.__version__", "1.2.3-test")
class MetadataContextProcessorTest(SimpleTestCase):
    def setUp(self):
        self.request_factory = RequestFactory()

    def test_metadata_returns_version(self):
        request = self.request_factory.get("/")
        context = metadata(request)

        self.assertIn("testdjereo", context)
        self.assertIn("meta", context["testdjereo"])
        self.assertEqual(context["testdjereo"]["meta"]["version"], "1.2.3-test")
