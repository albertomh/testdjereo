"""
Credit to Adam Johnson's 'Boost Your Django DX' book.
"""

import sys
from types import SimpleNamespace
from unittest import mock

from django.db import models
from django.test import SimpleTestCase, override_settings
from django.test.utils import isolate_apps

from testdjereo.checks import check_dev_mode, check_model_names


def mock_dev_mode(value):
    return mock.patch.object(
        sys,
        "flags",
        SimpleNamespace(dev_mode=value),
    )


class TestDevModeCheck(SimpleTestCase):
    def test_success_dev_mode(self):
        with override_settings(DEBUG=True), mock_dev_mode(True):
            result = check_dev_mode()

        self.assertEqual(result, [])

    def test_success_not_debug(self):
        with override_settings(DEBUG=False), mock_dev_mode(False):
            result = check_dev_mode()

        self.assertEqual(result, [])

    def test_fail_not_dev_mode(self):
        with override_settings(DEBUG=True), mock_dev_mode(False):
            result = check_dev_mode()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "testdjereo.W001")


@isolate_apps("testdjereo", attr_name="apps")
class CheckModelNamesTests(SimpleTestCase):
    def test_success(self):
        class Single(models.Model):
            pass

            class Meta:
                app_label = "testdjereo"

        result = check_model_names(
            app_configs=self.apps.get_app_configs(),
        )

        self.assertEqual(result, [])

    def test_fail(self):
        class Plurals(models.Model):
            pass

            class Meta:
                app_label = "testdjereo"

        result = check_model_names(
            app_configs=self.apps.get_app_configs(),
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "testdjereo.E001")
        self.assertEqual(
            result[0].hint,
            (
                "Rename to the singular form, like “Plural”, or mark the name "
                "as allowed by adding 'Plurals' to "
                "testdjereo.checks.SAFE_MODEL_NAMES."
            ),
        )
        self.assertEqual(result[0].obj, Plurals)

    def test_success_allowed_plural(self):
        class Plurals(models.Model):
            pass

            class Meta:
                app_label = "testdjereo"

        mock_safe_names = mock.patch(
            "testdjereo.checks.SAFE_MODEL_NAMES",
            new={"Plurals"},
        )

        with mock_safe_names:
            result = check_model_names(
                app_configs=self.apps.get_app_configs(),
            )

        self.assertEqual(result, [])
