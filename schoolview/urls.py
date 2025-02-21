from django.urls import path
from schoolview import views
from django.contrib.auth import views as auth_views
app_name = 'schoolview'

urlpatterns = [
    #registrations
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', views.logged_out, name='logout'),
    path('register/', views.register, name='register'),
    # 
    path('', views.index, name='index'),
    path('exam/', views.exam, name='exam'),
    path('worksheet/', views.make_worksheet, name='worksheet'),
    path('save_worksheet/', views.save_worksheet, name='save_worksheet'),
    path('leitner/', views.LeitnerView.as_view(), name='leitner'),
    path('student_profile/<int:user_id>/', views.student_profile, name='student_profile'),
    path('designer_profile/<int:user_id>/', views.designer_profile, name='designer_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<int:user_id>/questions/', views.questions, name='questions'),
    path('profile/subquestion_list/', views.subquestion_create_view,
         name='subquestion_list'),
]