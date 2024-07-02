from django.urls import path, include
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', include('django.contrib.auth.urls')),
    path('', views.profile, name='profile'),
    path('register/', views.register, name='register'),
    path('edit/', views.EditCardView.as_view(), name='edit'),
    path('account/', views.account, name='account'),
    path('download/', views.download_vcard, name='download_vcard'),
    path('connections/', views.connection_list, name='connection_list'),
    path('connections/<uuid:connection_id>/', views.connection_detail, name='connection_detail'),
    path('connections/edit/', views.edit_connection, name='edit_connection'),
    path('connections/edit/<uuid:connection_id>/', views.edit_connection, name='edit_connection'),
    path('connections/download/<uuid:connection_id>/', views.download_vcard, name='download_connection_vcard')
]
