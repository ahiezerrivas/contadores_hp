from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Usuario del sistema con rol administrador o invitado."""

    ROLE_CHOICES = [
        ("admin", "Administrador"),
        ("guest", "Invitado"),
    ]
    role = models.CharField("Rol", max_length=20, choices=ROLE_CHOICES, default="guest")

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    @property
    def is_admin(self):
        return self.role == "admin" or self.is_superuser

    def __str__(self):
        return self.username
