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
    path('profile/subquestion_list/', views.subquestion_create_view, name='subquestion_list'),
    path('profile/right-answer/create/<int:subquestion_id>/', views.right_answer_create_view, name='right_answer_create'),
    path('profile/wrong-answer/create/<int:subquestion_id>/', views.wrong_answer_create_view, name='wrong_answer_create'),
    path('designer_profile/create-full-hierarchy/', views.create_full_hierarchy_view, name='create_full_hierarchy'),
    path('designer_profile/create_question/', views.create_question, name='create_question'),
    path('designer_profile/<int:user_id>/designer-subquestions/', views.designer_subquestions, name='designer_subquestions'),
    path('edit-subquestion/<int:subquestion_id>/', views.edit_subquestion, name='edit_subquestion'),
    path('designer_profile/<int:user_id>/designer-questions/', views.designer_questions, name='designer_questions'),
]