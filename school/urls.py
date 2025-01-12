from django.urls import path
from . import views
app_name = "school"

urlpatterns = [
    path("signup/", views.SignupAPIView.as_view(), name="signup"),
    path("login/", views.LoginAPIView.as_view(), name="login"),
    path("loggout/", views.LoggoutAPIViwe.as_view(), name="loggout")

]