"""
URL configuration for the NewsApp project.

Routes top-level URL prefixes to each app's own URLconf.
See `Django URL dispatcher
<https://docs.djangoproject.com/en/6.0/topics/http/urls/>`_ for details.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/',    admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('api/',      include('news.api_urls')),
    path('',          include('news.urls',     namespace='news')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
