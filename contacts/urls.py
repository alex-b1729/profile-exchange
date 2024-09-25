"""
URL configuration for contacts project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static

from profile import views as prof_views

urlpatterns = [
    path('', prof_views.home, name='home'),
    path('account/', prof_views.account, name='account'),
    path('account/', include('django.contrib.auth.urls')),
    path('account/register/', prof_views.register, name='register'),

    path('content/', prof_views.user_content_view, name='content'),
    path('content/order/', prof_views.ContentOrderView.as_view(), name='content_order'),
    path(
        'content/<model_name>/create/',
        prof_views.ItemCreateUpdateView.as_view(),
        name='item_create'
    ),
    path(
        'content/<model_name>/<item_pk>/',
        prof_views.ItemCreateUpdateView.as_view(),
        name='item_update'
    ),
    path(
        'content/<model_name>/<item_pk>/delete',
        prof_views.item_delete,
        name='item_delete'
    ),

    path('admin/', admin.site.urls),
    path('profile/', include('profile.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
