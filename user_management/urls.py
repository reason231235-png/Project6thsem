from django.urls import path
from django.contrib.auth.views import LoginView

from user_management.views import RegisterView, LogoutView, IndexView
from user_management.forms import LoginForm

app_name = "user_management"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("register/", RegisterView.as_view(), name="register"),
    path(
        "login/",
        LoginView.as_view(
            template_name="user_management/login.html", authentication_form=LoginForm
        ),
        name="login",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
]
