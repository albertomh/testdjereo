import os

import responses
from django.test.runner import DiscoverRunner
from django.test.utils import override_settings

TEST_SETTINGS = {
    "DEBUG": False,
}

# Global placeholder for the active responses mocker
ACTIVE_RESPONSES = None


class TestRunner(DiscoverRunner):
    """Custom test runner to apply test-specific settings & mock out requests.

    Override settings per-test with a decorator:
    ```
    @override_settings(DEBUG=False)
    def test_unit(self):
        ...
    ```

    Intercept and mock out requests in tests with:
    ```
    from testdjereo.test import ACTIVE_RESPONSES

    class ViewTests(SimpleTestCase):
        def test_view(self):
            ACTIVE_RESPONSES.add(
                responses.GET,
                "https://example.com/api/resource",
                json={"key": "value"},
            )
            ...
    ```
    """

    def __init__(self, *args, exclude_tags=None, **kwargs):
        # exclude tests tagged 'slow' when running locally
        is_ci = os.getenv("GITHUB_ACTIONS") == "true"
        if exclude_tags is None and not is_ci:
            exclude_tags = ["slow"]
        super().__init__(*args, exclude_tags=exclude_tags, **kwargs)

    def run_tests(self, *args, **kwargs):
        global ACTIVE_RESPONSES

        with responses.RequestsMock() as rsps, override_settings(**TEST_SETTINGS):
            ACTIVE_RESPONSES = rsps
            return super().run_tests(*args, **kwargs)

        ACTIVE_RESPONSES = None
