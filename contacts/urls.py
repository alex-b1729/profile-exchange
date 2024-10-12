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
    path('account/', include('django.contrib.auth.urls')),
    path('account/register/', prof_views.register, name='register'),
    path(
        'content/',
        include([
            path('', prof_views.user_content_view, name='content'),
            path('new/', prof_views.add_item, name='add_item'),
            path(  # for single models like Email or WorkExperience
                '<slug:model_name>/',
                include([
                    path('new/', prof_views.ContentCreateUpdateView.as_view(), name='item_create'),
                    path('<int:content_pk>/', prof_views.ContentCreateUpdateView.as_view(), name='item_update'),
                    path('<int:content_pk>/delete/', prof_views.content_delete, name='item_delete'),
                ])
            ),
            path(  # for models with a choice variable like Link, GitHub
                '<slug:model_name>/<slug:model_type>/',
                include([
                    path('new/', prof_views.ContentCreateUpdateView.as_view(), name='item_create'),
                    path('<int:content_pk>/', prof_views.ContentCreateUpdateView.as_view(), name='item_update'),
                    path('<int:content_pk>/delete/', prof_views.content_delete, name='item_delete'),
                ])
            ),
        ]),
    ),

    path('admin/', admin.site.urls),
    path('profile/', include('profile.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
