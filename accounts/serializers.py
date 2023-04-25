from rest_framework import serializers
from django.core.validators import MinLengthValidator

from accounts.models import User
from accounts.validators import (
    validate_email,
    validate_password,
    validate_username,
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "email",
            "username",
            "name",
            "first_name",
            "last_name",
            "date_joined",
        )


class RegisterUserSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, validators=[validate_email])
    username = serializers.CharField(
        required=True, validators=[validate_username]
    )
    password = serializers.CharField(
        required=True, validators=[validate_password]
    )
    first_name = serializers.CharField(
        required=True,
        validators=[
            MinLengthValidator(
                limit_value=3,
                message="First name must be longer than 3 characters",
            )
        ],
    )
    last_name = serializers.CharField(
        required=True,
        validators=[
            MinLengthValidator(
                limit_value=3,
                message="Last name must be longer than 3 characters.",
            )
        ],
    )

    def create(self, **validated_data):
        return User.objects.create(**validated_data)


class PasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        required=True, validators=[validate_password]
    )

    def update(self, instance: User, validated_data):
        password = validated_data.get("password")
        instance.set_password(password)
        instance.save()
        return instance


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, validators=[validate_email])

    def update(self, instance: User, validated_data):
        email = validated_data.get("email")
        instance.email = email
        instance.save()
        return instance


class UsernameSerializer(serializers.Serializer):
    username = serializers.CharField(
        required=True, validators=[validate_username]
    )

    def update(self, instance: User, validated_data):
        username = validated_data.get("username")
        instance.username = username
        instance.save()
        return instance


class NameSerializer(serializers.Serializer):
    first_name = serializers.CharField(
        required=True,
        validators=[
            MinLengthValidator(
                limit_value=2,
                message="First name must be longer than two characters.",
            )
        ],
    )
    last_name = serializers.CharField(
        required=True,
        validators=[
            MinLengthValidator(
                limit_value=3,
                message="Last name must be longer than three characters.",
            )
        ],
    )

    def update(self, instance: User, validated_data):
        first_name = validated_data.get("first_name")
        last_name = validated_data.get("last_name")
        instance.first_name = first_name
        instance.last_name = last_name
        instance.save()


class ExchangeUsersConfigSerializer(serializers.Serializer):
    key = serializers.CharField(required=True)
    secret = serializers.CharField(required=True)
    exchange = serializers.CharField(required=True)
