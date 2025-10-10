from datetime import timedelta

from django.test import TestCase
from django.utils.timezone import now

from testdjereo.tests.test_app.models import (
    TestModelCreatedAt,
    TestModelDeletedAt,
    TestModelUpdatedAt,
)


class ModelTestCase(TestCase):
    def test_created_at_field_on_creation(self):
        obj = TestModelCreatedAt.objects.create()
        self.assertIsNotNone(obj.created_at)
        self.assertAlmostEqual(obj.created_at, now(), delta=timedelta(seconds=1))

    def test_updated_at_field_on_save(self):
        obj = TestModelUpdatedAt.objects.create()
        initial_updated_at = obj.updated_at
        obj.save()
        self.assertGreater(obj.updated_at, initial_updated_at)

    def test_deleted_at_model_soft_delete(self):
        obj = TestModelDeletedAt.objects.create()
        self.assertIsNone(obj.deleted_at)

        obj.soft_delete()
        self.assertIsNotNone(obj.deleted_at)
        self.assertAlmostEqual(obj.deleted_at, now(), delta=timedelta(seconds=1))

    def test_deleted_at_model_restore(self):
        obj = TestModelDeletedAt.objects.create()
        obj.soft_delete()
        obj.restore()
        self.assertIsNone(obj.deleted_at)
