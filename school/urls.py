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
    path("logout/", views.LogoutAPIView.as_view(), name="logout"),
    path('api_token_auth/', views.CustomAuthToken.as_view(), name='api_token_auth'),

    path('filter_exam/', views.get_exam_filter, name='filter_exam'),
    path('exam/', views.get_exam, name='get_exam'),
    path('leitner/', views.LeitnerAPIView.as_view(), name='leitner'),

    path('', include(router.urls)),

]