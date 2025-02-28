from django.urls import path, include
from . import views
from rest_framework import routers
router = routers.DefaultRouter()

router.register(r'questions', views.QuestionViewSet)
router.register(r'subquestions', views.SubquestionViewSet)
router.register(r'courses', views.CourseViewSet)
router.register(r'books', views.BookViewSet)
router.register(r'seasons', views.SeasonViewSet)
router.register(r'lessons', views.LessonViewSet)
router.register(r'subjects', views.SubjectViewSet)
router.register(r'leitnerquestion', views.LeitnerQuestionViewSet)


app_name = "school"
urlpatterns = [
    path("signup/", views.SignupAPIView.as_view(), name="signup"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("logout/", views.LogoutAPIView.as_view(), name="logout"),
    path("check-auth/", views.CheckAuthView.as_view(), name="check-auth"),
    path("csrf-token/", views.CSRFTokenView.as_view(), name="csrf-token"),

    path('exam/', views.get_exam, name='get_exam'),
    path('leitner/', views.LeitnerAPIView.as_view(), name='leitner'),

    path('', include(router.urls)),

]