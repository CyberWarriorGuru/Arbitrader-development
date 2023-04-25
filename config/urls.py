from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CryptoTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        return token


class CryptoTokenObtainPairView(TokenObtainPairView):
    serializer_class = CryptoTokenObtainPairSerializer


app_name = "arbitrage"

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        route="accounts/login",
        view=CryptoTokenObtainPairView.as_view(),
        name="login_token_obtain_pair",
    ),
    path(
        route="accounts/token/fresh",
        view=TokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path(
        "api/v1/arbitrage/",
        include("arbitrage.urls", namespace="bitcoin_arbitrage"),
        name="arbitrage",
    ),
    path(
        "api/v1/accounts/",
        include("accounts.urls", namespace="user_accounts"),
        name="user_accounts",
    ),
]
