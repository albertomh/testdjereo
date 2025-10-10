from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase

from testdjereo.middleware import SecurityHeadersMiddleware


class SecurityHeadersMiddlewareTests(SimpleTestCase):
    def setUp(self):
        self.request_factory = RequestFactory()

    def test_middleware(self):
        middleware = SecurityHeadersMiddleware(get_response=lambda req: HttpResponse())
        request = self.request_factory.get("/")

        response = middleware(request)

        assert response["Cross-Origin-Embedder-Policy"] == "require-corp"
        assert response["Cross-Origin-Resource-Policy"] == "same-origin"
