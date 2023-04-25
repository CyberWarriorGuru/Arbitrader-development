import logging

from django.utils.translation import gettext_lazy as _
from rest_framework import status

from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import (
    CreateAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.response import Response

from accounts.models import ExchangeUserConfig
from accounts.mixins import CreateUserConfigMixin
from accounts.serializers import (
    ExchangeUsersConfigSerializer,
    EmailSerializer,
    NameSerializer,
    PasswordSerializer,
    RegisterUserSerializer,
    UsernameSerializer,
    UserSerializer,
)
from crypto_bot.models import Exchange


logger = logging.getLogger(__name__)


class ProfileView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer_class()
            data = serializer(request.user).data
            data = {"status": "success", "message": data}
        except Exception as error:
            logger.exception(str(error))
            data = {"status": "error", "message": "Unable to get user data"}
        return Response(data=data, status=status.HTTP_200_OK)


class RegisterUserView(CreateAPIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = RegisterUserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()
        serializer = serializer(data=request.data)

        if serializer.is_valid():
            serializer.create(**serializer.validated_data)
            username = serializer.validated_data.get("username")
            data = {"message": _("User %s created" % username)}
            return Response(data, status=status.HTTP_201_CREATED)

        data = {"error": serializer.errors}
        return Response(data, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        serializer = PasswordSerializer(data=request.data)

        if serializer.is_valid():
            user = request.user
            serializer.update(user, serializer.validated_data)
            data = {"message": _("Password updated")}
            return Response(data, status=status.HTTP_201_CREATED)

        data = {"error": serializer.errors}
        return Response(data, status=status.HTTP_400_BAD_REQUEST)


class ChangeEmailView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        serializer = EmailSerializer(data=request.data)

        if serializer.is_valid():
            user = request.user
            serializer.update(user, serializer.validated_data)
            email = serializer.data.get("email")
            data = {"message": _("Your email %s has been updated" % email)}
            return Response(data, status=status.HTTP_201_CREATED)

        data = {"error": serializer.errors}
        return Response(data, status=status.HTTP_400_BAD_REQUEST)


class ChangeUsernameView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        serializer = UsernameSerializer(data=request.data)

        if serializer.is_valid():
            user = request.user
            serializer.update(user, serializer.validated_data)
            data = {"message": _("Username details were updated.")}
            return Response(data, status=status.HTTP_201_CREATED)

        data = {"error": serializer.errors}
        return Response(data, status=status.HTTP_400_BAD_REQUEST)


class ChangeName(UpdateAPIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        serializer = NameSerializer(data=request.data)

        if serializer.is_valid():
            user = request.user
            serializer.update(user, serializer.validated_data)
            data = {"message": _("Name updated successfully.")}
            return Response(data, status=status.HTTP_201_CREATED)

        data = {"error": serializer.errors}
        return Response(data, status=status.HTTP_400_BAD_REQUEST)


class AddConfigToUserConfigs(UpdateAPIView, CreateUserConfigMixin):
    permission_classes = (IsAuthenticated,)

    def put(self, request, *args, **kwargs):
        serializer = ExchangeUsersConfigSerializer(data=request.data)

        if serializer.is_valid():
            self.user = request.user

            if not self.has_user_accounts_config():
                configs = self.create_user_accounts_config()
            else:
                configs = self.get_user_accounts_config()

            # Get Exchange if it exists, if it does not return an error
            exchange = Exchange.objects.filter(
                name=serializer.validated_data.get("exchange")
            )

            if not exchange.exists():
                data = {"message": "Exchange not supported"}
                return Response(data=data, status=status.HTTP_400_BAD_REQUEST)

            new_user_config = ExchangeUserConfig.objects.create(
                user=self.user,
                exchange=exchange.first(),
                key=serializer.validated_data.get("key"),
                secret=serializer.validated_data.get("secret"),
            )
            configs.configs.add(new_user_config)

            data = {"message": "User Config Created"}
            return Response(data, status=status.HTTP_201_CREATED)

        data = {"error": "Unable to create user config"}
        return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
