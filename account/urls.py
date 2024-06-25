from django.urls import path, include
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', include('django.contrib.auth.urls')),
    path('', views.profile, name='profile'),
    path('register/', views.register, name='register'),
    # path('edit/', views.edit, name='edit'),
    path('edit/', views.EditProfileView.as_view(), name='edit'),
    path('account/', views.account, name='account'),
    path('download/', views.download_vcard, name='download_vcard'),
    # path('users/', views.user_list, name='user_list'),
    # path('connections/', views.connection_list, name='connection_list'),
    path('connections/<uuid:connection_id>/', views.connection_detail, name='connection_detail'),
]
