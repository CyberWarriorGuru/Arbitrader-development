"""
Account Models
"""
import logging

from cryptography.fernet import Fernet

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .manager import UserManager

from crypto_bot.models import Exchange


logger = logging.getLogger(__name__)


class User(AbstractBaseUser, PermissionsMixin):

    email = models.EmailField(max_length=254, unique=True)
    name = models.CharField(max_length=254, null=True, blank=True)
    username = models.CharField(
        max_length=254, null=True, blank=True, unique=True
    )
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"

    objects = UserManager()
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    def get_full_name(self):
        return self.name

    def __str__(self):
        return self.email


class ExchangeUserConfig(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    exchange = models.OneToOneField(Exchange, on_delete=models.CASCADE)
    key = models.TextField(default="")
    secret = models.TextField(default="")

    def save(self, *args, **kwargs):
        try:
            fernet = Fernet(settings.FERNET_KEY[1:].encode())
        except Exception:  # hardcode something here
            fernet = b"test-thing"
        key = self.key.encode()
        secret = self.secret.encode()
        self.key = fernet.encrypt(key)
        self.secret = fernet.encrypt(secret)
        super().save(*args, **kwargs)

    @classmethod
    def plain_text(cls, value):
        fernet = Fernet(settings.FERNET_KEY[1:].encode())
        try:
            value = fernet.decrypt(value).decode("utf-8")
        except Exception as error:
            logger.exception(str(error))
            value = None
        return value


class ExchangeUserConfigs(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    configs = models.ManyToManyField(ExchangeUserConfig)
