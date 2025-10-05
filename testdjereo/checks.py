"""Static checks to validate a Django project and guard against pitfalls.

- Warn when DEBUG is true yet Python is not being run in Development Mode.
- Prevent naming models in the plural form.

Credit to Adam Johnson's 'Boost Your Django DX' book.
"""

import sys

from django.apps import apps
from django.conf import settings
from django.core.checks import Error
from django.core.checks import Warning as CheckWarning

SAFE_MODEL_NAMES: set[str] = set()


def check_dev_mode(**kwargs):
    errors = []

    if settings.DEBUG and not sys.flags.dev_mode:
        errors.append(
            CheckWarning(
                "Python Development Mode is not enabled yet DEBUG is true.",
                hint=(
                    "Set the environment variable PYTHONDEVMODE=1, or run "
                    + "with 'python -X dev'."
                ),
                id="testdjereo.W001",
            )
        )

    return errors


def check_model_names(*, app_configs, **kwargs):
    if app_configs is None:
        app_configs = apps.get_app_configs()

    errors = []

    for app_config in app_configs:
        # skip apps that aren’t part of the project
        if app_config.name.split(".", maxsplit=1)[0] != "testdjereo":
            continue

        for model in app_config.get_models():
            class_name = model.__name__

            if class_name.endswith("s") and class_name not in SAFE_MODEL_NAMES:
                error = Error(
                    "Model names should be singular.",
                    hint=(
                        "Rename to the singular form, like "
                        f"“{class_name.removesuffix('s')}”, or mark the "
                        f"name as allowed by adding {class_name!r} to "
                        f"{__name__}.SAFE_MODEL_NAMES."
                    ),
                    obj=model,
                    id="testdjereo.E001",
                )
                errors.append(error)

    return errors
