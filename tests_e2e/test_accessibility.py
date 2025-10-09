import warnings

import pytest
from playwright.sync_api import Page
from axe_playwright_python.sync_playwright import Axe

from tests_e2e.conftest import BASE_URL


class TestAccessibility:
    @pytest.mark.parametrize(
        "url",
        [
            BASE_URL,
            f"{BASE_URL}/accounts/login/",
            f"{BASE_URL}/accounts/signup/",
        ],
    )
    def test_page_accessibility(self, page: Page, axe: Axe, url: str):
        page.goto(url)
        results = axe.run(page)

        if results.violations_count > 0:
            report = results.generate_report()
            warnings.warn(
                f"\n{results.violations_count} accessibility violations at {url}:\n{report}",
                UserWarning,
            )
