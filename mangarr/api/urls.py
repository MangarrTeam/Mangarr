from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    #path('', views.index, name="index"),
    path('manager/users/<int:user_id>/staff/', views.toggle_staff_user, name='toggle_user_staff'),
    path('manager/users/<int:user_id>/permissions/', views.get_user_permissions, name='get_user_permissions'),
    path('manager/users/<int:user_id>/permissions/update/', views.update_user_permissions, name='update_user_permissions'),
    path('manager/users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('manager/tokens/register/delete/<int:token_id>/', views.delete_token, name='delete_token'),
]