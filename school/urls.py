from django.urls import path
from . import views
app_name = "school"

urlpatterns = [
    path("signup/", views.SignupAPIView.as_view(), name="signup"),
    path("login/", views.LoginAPIView.as_view(), name="login"),
    path("logout/", views.LogoutAPIView.as_view(), name="logout"),
    path("createquestion/", views.CreateQuestionAPIView.as_view(), name="createquestion"),
    path("educationstage/", views.EducationStageAPIView.as_view(), name="educationstage"),

]