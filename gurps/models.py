from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser


class RegisterUser(AbstractUser):

    created_date = models.DateField(default=timezone.now)

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="custom_user_set",  # Nome único para evitar conflitos
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="custom_user_permissions_set",  # Nome único para evitar conflitos
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )

    def __str__(self) -> str:
        return self.username
