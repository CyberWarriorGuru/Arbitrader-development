from django.urls import path

from accounts import views


app_name = "user_accounts"


urlpatterns = [
    path(
        route="register",
        view=views.RegisterUserView.as_view(),
        name="user_register",
    ),
    path(
        route="user-info",
        view=views.ProfileView.as_view(),
        name="user_profile_info",
    ),
    path(
        route="update-username",
        view=views.ChangeUsernameView.as_view(),
        name="update_username",
    ),
    path(
        route="update-password",
        view=views.ChangePasswordView.as_view(),
        name="update_password",
    ),
    path(
        route="update-email",
        view=views.ChangeEmailView.as_view(),
        name="update_email",
    ),
    path(
        route="update-name",
        view=views.ChangeName.as_view(),
        name="update_name",
    ),
    path(
        route="add-config-to-user",
        view=views.AddConfigToUserConfigs.as_view(),
        name="add_config_to_user",
    ),
]
