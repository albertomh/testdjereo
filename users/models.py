from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from testdjereo.models import UpdatedAtModel, UuidModel


class AuthUserManager(UserManager["AuthUser"]):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The 'email' field must be set")
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, password, **extra_fields)


class AuthUser(UpdatedAtModel, UuidModel, AbstractUser):
    username = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=False, unique=True)

    USERNAME_FIELD = "email"
    # field names that will be prompted for when `createsuperuser` mgmt. command is called
    REQUIRED_FIELDS = []

    objects = AuthUserManager()

    class Meta:
        verbose_name = "auth user"

    def __str__(self):
        return self.email


class UserProfile(UuidModel):
    user: models.OneToOneField["UserProfile", AuthUser] = models.OneToOneField(
        "users.AuthUser",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"Profile for {self.user}"


@receiver(post_save, sender=AuthUser)
def create_or_update_user_profile(
    sender, instance, created, **kwargs
):  # pragma: no cover
    UserProfile.objects.update_or_create(user=instance)
