from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from testdjereo.models import UpdatedAtModel, UuidModel


class AuthUser(UpdatedAtModel, UuidModel, AbstractUser):
    class Meta:
        verbose_name = "auth user"

    def __str__(self):
        return self.email


class UserProfile(UuidModel):
    user = models.OneToOneField(
        "users.AuthUser",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"Profile for {self.user}"


@receiver(post_save, sender=AuthUser)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    UserProfile.objects.update_or_create(user=instance)
