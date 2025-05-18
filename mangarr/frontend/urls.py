from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('manager/users/', views.manager_user_list, name='manager_user_list'),
    path('manager/tokens/register/create', views.create_register_token, name='create_register_token'),


    path("accounts/register/", views.register, name="register"),
    path("accounts/login/", views.login_view, name="login"),
    path("accounts/logout/", views.my_logout, name="logout"),
    path("accounts/profile/", views.profile, name="profile"),
    path("accounts/change_password/", views.change_password, name="change_password"),
    path('', views.index, name="index"),


    path("settings/", views.settings_view, name="settings"),
]