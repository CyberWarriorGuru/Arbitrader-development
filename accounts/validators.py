import re

from rest_framework.serializers import ValidationError

from accounts.models import User


def validate_email(value):
    if User.objects.filter(email=value).exists():
        raise ValidationError("User with similar credentials exists.")
    return value


def validate_username(value):
    if User.objects.filter(username=value).exists():
        raise ValidationError("User with similar credentials exists.")
    if len(value) < 6:
        raise ValidationError("Username is too short")
    if not re.match(r"^[a-z0-9_]+$", value):
        raise ValidationError("Only lowercase '_' and digits allowed.")
    return value


def validate_password(value):
    if not re.search("[0-9]", value):
        raise ValidationError("Password must include at least one number")
    if not re.search("[a-z]", value):
        raise ValidationError(
            "Password must include at least one lowercase letter"
        )
    if not re.search("[A-Z]", value):
        raise ValidationError(
            "Password must include at least one uppercase letter"
        )
    if not re.search("[@_!#$%^&*()<>?/\|}{~:]", value):
        raise ValidationError(
            "Password must inclide at least one special character"
        )
    return value
