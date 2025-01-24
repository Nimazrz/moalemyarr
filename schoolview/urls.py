from django.urls import path
from schoolview import views
from django.contrib.auth import views as auth_views
app_name = 'schoolview'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', views.logged_out, name='logout'),

]