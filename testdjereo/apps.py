from django.apps import AppConfig
from django.core import checks


class TestdjereoConfig(AppConfig):
    name = "testdjereo"

    def ready(self) -> None:
        from testdjereo.checks import check_dev_mode, check_model_names

        checks.register(check_dev_mode)
        checks.register(check_model_names)
