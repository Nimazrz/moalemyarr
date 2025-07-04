from django.urls import path, include
from . import views
from rest_framework import routers
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView



router = routers.DefaultRouter()

router.register(r'questions', views.QuestionViewSet)
router.register(r'subquestions', views.SubquestionViewSet)
router.register(r'courses', views.CourseViewSet)
router.register(r'books', views.BookViewSet)
router.register(r'seasons', views.SeasonViewSet)
router.register(r'lessons', views.LessonViewSet)
router.register(r'subjects', views.SubjectViewSet)


app_name = "school"
urlpatterns = [
    path("signup/", views.SignupAPIView.as_view(), name="signup"),
    path("logout/", views.LogoutAPIView.as_view(), name="logout"),
    path('api_token_auth/', views.CustomAuthToken.as_view(), name='api_token_auth'),

    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('filter_exam/', views.get_exam_filter, name='filter_exam'),
    path('exam/', views.get_exam, name='get_exam'),
    path('leitner/', views.LeitnerAPIView.as_view(), name='leitner'),
    path('leitnerquestion/', views.LeitnerQuestionViewSet.as_view(), name='leitnerquestion'),

    path('followup/', views.FollowQuestionDesignerView.as_view(), name='followup'),

    # API schema views
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger/', SpectacularSwaggerView.as_view(url_name='school:schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='school:schema'), name='redoc'),

    path('', include(router.urls)),


]