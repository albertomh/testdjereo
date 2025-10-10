from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import SimpleTestCase

from testdjereo.admin import CustomAdminAuthenticationForm
from users.models import UserProfile


class CustomAdminAuthenticationFormTest(SimpleTestCase):
    def test_username_field_label_is_email(self):
        form = CustomAdminAuthenticationForm()
        self.assertEqual(form.fields["username"].label, "Email")


class AdminTest(SimpleTestCase):
    def test_custom_admin_model_registry(self):
        models = [k for k in admin.site._registry.keys()]

        self.assertTrue(get_user_model() in models)
        self.assertTrue(UserProfile in models)
        self.assertTrue(Group in models)
