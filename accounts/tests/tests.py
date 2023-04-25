from cryptography.fernet import Fernet
from django.db.utils import IntegrityError
from django.conf import settings
from django.test import TestCase
from django.shortcuts import reverse
from rest_framework.test import APIRequestFactory, force_authenticate


from accounts import views
from accounts.models import User, ExchangeUserConfig, ExchangeUserConfigs
from crypto_bot.models import Exchange


class TestUserManagement(TestCase):
    fixtures = ["user-fixtures.json"]

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.exchange = Exchange.objects.get_or_create(name="Binance")
        self.fernet = Fernet(settings.FERNET_KEY[1:].encode())
        self.key = "scrambled-eggz"
        self.secret = "crispy-hashbaked-potatoes"
        self.user_config = ExchangeUserConfig.objects.create(
            user=self.user,
            exchange=self.exchange[0],
            key=self.key,
            secret=self.secret,
        )

    def test_user_config_storage(self):
        self.assertTrue(self.user_config.key != self.key)
        exp = self.user_config.plain_text(self.user_config.key) == self.key
        self.assertTrue(exp)

    def test_exchange_user_configs(self):
        user_configs = ExchangeUserConfigs.objects.create(user=self.user)
        user_configs.configs.add(self.user_config)
        user_config_exchange = user_configs.configs.get(
            exchange__name="Binance"
        )
        self.assertTrue(user_config_exchange.exchange == self.exchange[0])

        # Test no user can have two ExchangeUserConfigs because it will
        # not make sense since a single instance can add as many
        # supported configs as we support, via
        # ExchangeUserConfig__Exchange.

        with self.assertRaises(IntegrityError):
            user_configs = ExchangeUserConfigs.objects.create(user=self.user)


class TestUserManagementViews(TestCase):
    fixtures = ["user-fixtures.json"]

    def setUp(self):
        self.user = User.objects.get(pk=1)
        self.factory: APIRequestFactory = APIRequestFactory()

    def test_a_get_profile_data(self):
        user_profile = views.ProfileView().as_view()
        url = reverse("user_accounts:user_profile_info")
        request = self.factory.get(url)
        force_authenticate(request, self.user)
        response = user_profile(request)
        self.assertTrue(response.status_code == 200)
        self.assertEquals(response.data["message"]["email"], self.user.email)

    def test_b_change_username(self):
        view = views.ChangeUsernameView().as_view()
        url = reverse("user_accounts:update_username")
        request = self.factory.put(url, data={"username": "new_username"})
        force_authenticate(request, self.user)
        response = view(request)
        self.assertTrue(response.status_code == 201)

    def test_c_change_password(self):
        view = views.ChangePasswordView().as_view()
        url = reverse("user_accounts:update_password")
        request = self.factory.put(url, data={"password": "TestP@assw0rd"})
        force_authenticate(request, self.user)
        response = view(request)
        self.assertTrue(response.status_code == 201)

    def test_d_change_name(self):
        view = views.ChangeName().as_view()
        url = reverse("user_accounts:update_name")
        request = self.factory.put(
            url, data={"first_name": "test", "last_name": "test"}
        )
        force_authenticate(request, self.user)
        response = view(request)
        self.assertTrue(response.status_code == 201)

    def test_e_register(self):
        view = views.RegisterUserView().as_view()
        url = reverse("user_accounts:user_register")
        request = self.factory.post(
            url,
            data={
                "email": "new_user@mail.com",
                "username": "new_username",
                "password": "nEw_passw0rd",
                "first_name": "test",
                "last_name": "test",
            },
        )
        force_authenticate(request, self.user)
        response = view(request)
        self.assertTrue(response.status_code == 201)

    def test_f_add_config_to_user(self):
        Exchange.objects.create(name="Binance")
        view = views.AddConfigToUserConfigs.as_view()
        url = reverse("user_accounts:add_config_to_user")
        request = self.factory.put(
            url,
            data={
                "key": "test-api-key",
                "secret": "test-secret-key",
                "exchange": "Binance",
            },
        )
        force_authenticate(request, self.user)
        response = view(request)
        self.assertTrue(response.status_code == 201)
