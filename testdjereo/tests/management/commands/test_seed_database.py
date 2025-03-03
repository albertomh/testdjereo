from io import StringIO

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase


class SeedDatabaseTests(TestCase):
    def call_command(self, *args, **kwargs):
        out = StringIO()
        err = StringIO()
        call_command(
            "seed_database",
            *args,
            stdout=out,
            stderr=err,
            **kwargs,
        )
        return out.getvalue(), err.getvalue()

    def test_error_data_exists(self):
        get_user_model().objects.create_user(email="user@example.com")
        expected_msg = (
            "This command cannot be run when any users exist to guard "
            + "against accidental use on production."
        )

        with self.assertRaisesMessage(CommandError, expected_msg):
            self.call_command()

    def test_success(self):
        out, err = self.call_command()

        self.assertTrue("Seeding database..." in out)
        self.assertTrue("Done." in out)
        self.assertEqual(err, "")

        expected_models = {
            ("auth", "Permission"),
            ("contenttypes", "ContentType"),
            ("users", "AuthUser"),
            ("users", "UserProfile"),
        }
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                model_name = model.__name__
                if (app_config.label, model_name) not in expected_models:
                    with self.subTest(f"{app_config.label}.{model_name}"):
                        self.assertFalse(
                            model.objects.exists(),
                            f"{model_name} is not populated by seed_database",
                        )
