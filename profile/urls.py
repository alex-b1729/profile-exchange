from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.profile_list, name='profile_list'),
    path('new/', views.ProfileCreateUpdateView.as_view(), {'next': 'profile'}, name='profile_create'),
    path('content/order/', views.ContentOrderView.as_view(), name='content_order'),
    path('content/<int:related_content_pk>/order', views.ContentOrderView.as_view(), name='attachment_order'),
    path(
        'edit/<int:profile_pk>/',
        views.ProfileCreateUpdateView.as_view(),
        {'next': 'profile_list'},
        name='list_profile_edit'
    ),
    # consider [Sqids](https://sqids.org/) instead of pks
    path(
        '<int:profile_pk>/',
        include([
            path('', views.profile, name='profile'),
            path('edit/', views.ProfileCreateUpdateView.as_view(), {'next': 'profile'}, name='profile_edit'),
            path('delete/', views.profile_delete, name='profile_delete'),
            path('select/', views.ProfileSelectContentView.as_view(), name='profile_content_select', ),
            path('editdetail/', views.ProfileDetailEditView.as_view(), name='profile_detail_edit'),
            path('img/', views.update_profile_img, name='update_profile_img'),
            path('img/delete/', views.profile_img_delete, name='profile_img_delete'),
            path(
                'share/',
                include([
                    path('', views.share, name='share'),
                    path('<int:link_pk>/', views.share, name='link_share'),
                    path(
                        'links/',
                        include([
                            path('', views.profile_links, name='profile_links'),
                            path('new/', views.ProfileCreateLink.as_view(), name='profile_link_create'),
                            path('<pk>/', views.ProfileLinkDetail.as_view(), name='profile_link_detail'),
                            path('<pk>/delete/', views.profile_link_delete, name='profile_link_delete'),
                        ]),
                    ),
                ]),
            ),
            path(
                '<int:content_pk>/',
                include([
                    path('select/', views.ProfileSelectContentView.as_view(), name='content_content_select'),
                    path('delete/', views.content_delete, name='content_content_delete'),
                ])
            ),
            path(
                '<slug:model_name>/',
                include([
                    path('new/', views.ContentCreateUpdateView.as_view(), name='profile_content_create'),
                    path('<int:content_pk>/', views.ContentCreateUpdateView.as_view(), name='profile_content_update'),
                    path('<int:content_pk>/delete/', views.content_delete, name='profile_content_delete'),
                ]),
            ),
        ]),
    ),
    path(
        'links/',
        include([
            path('', views.profile_list, name='link_list'),
            path('<pk>/', views.ProfileLinkDetail.as_view(), name='link_detail'),
        ])
    ),

    # path('', views.profile_list, name='profile_list'),
    # path('<slug:slug>/', views.profile, name='profile'),
    # path('<slug:slug>/edit/', views.EditCardView.as_view(), name='edit'),

    # path('share/', views.share_card, name='share'),
    # path('share/<uuid:share_uuid>/', views.view_shared_profile, name='shared_profile'),
    # path('share/<uuid:share_uuid>/connect/', views.connect, name='connect'),

    # path('download/', views.download_card, name='download_card'),
    # path('connections/', views.connection_list, name='connection_list'),
    # path('connections/<uuid:connection_id>/', views.connection_detail, name='connection_detail'),
    # path('contactbook/', views.contact_book, name='contact_book'),
    # path('contactbook/import', views.import_cards, name='import_cards'),
    # path('contactbook/<int:card_id>', views.card_detail, name='card_detail'),
    # path('connections/edit/', views.edit_connection, name='edit_connection'),
    # path('connections/edit/<uuid:connection_id>/', views.edit_connection, name='edit_connection'),
    # path('connections/download/<uuid:connection_id>/', views.download_card, name='download_connection_card')
]
