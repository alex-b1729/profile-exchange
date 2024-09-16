from django.urls import path, include
from django.contrib.auth import views as auth_views

from profile.forms import UserRegistrationForm,CardNameForm

from . import views

urlpatterns = [
    path('', include('django.contrib.auth.urls')),
    # todo: profile urls should be /profile/{profile_name}/
    # path('', views.profile, name='profile'),
    path('', views.profile_list, name='profile_list'),
    # todo: would rather this not be /protile/account/
    path('account/', views.account, name='account'),
    path('<slug:slug>/', views.profile, name='profile'),
    path('<slug:slug>/edit/', views.EditCardView.as_view(), name='edit'),
    path('<slug:slug>/edit/profileimg/', views.update_profile_img, name='update_profile_img'),

    path('share/', views.share_card, name='share'),
    path('share/<uuid:share_uuid>/', views.view_shared_profile, name='shared_profile'),
    path('share/<uuid:share_uuid>/connect/', views.connect, name='connect'),
    # path('register/', views.register, name='register'),
    path('register/',
         views.RegisterWizard.as_view([UserRegistrationForm, CardNameForm]),
         name='register'),
    path('download/', views.download_card, name='download_card'),
    path('connections/', views.connection_list, name='connection_list'),
    path('connections/<uuid:connection_id>/', views.connection_detail, name='connection_detail'),
    path('contactbook/', views.contact_book, name='contact_book'),
    path('contactbook/import', views.import_cards, name='import_cards'),
    path('contactbook/<int:card_id>', views.card_detail, name='card_detail'),
    # path('connections/edit/', views.edit_connection, name='edit_connection'),
    # path('connections/edit/<uuid:connection_id>/', views.edit_connection, name='edit_connection'),
    # path('connections/download/<uuid:connection_id>/', views.download_card, name='download_connection_card')
]
