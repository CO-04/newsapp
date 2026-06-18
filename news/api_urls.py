"""
API URL configuration for the news app.

Registered under /api/ in newsapp/urls.py.
JWT token endpoints are included here so all API routes share the /api/ prefix.
"""

from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from . import api_views

urlpatterns = [
    # JWT auth
    path(
        'token/',
        TokenObtainPairView.as_view(),
        name='api_token_obtain',
    ),
    path(
        'token/refresh/',
        TokenRefreshView.as_view(),
        name='api_token_refresh',
    ),

    # Publishers
    path(
        'publishers/',
        api_views.PublisherListCreateView.as_view(),
        name='api_publisher_list',
    ),
    path(
        'publishers/<int:pk>/',
        api_views.PublisherDetailView.as_view(),
        name='api_publisher_detail',
    ),

    # Articles
    path(
        'articles/',
        api_views.ArticleListCreateView.as_view(),
        name='api_article_list',
    ),
    path(
        'articles/subscribed/',
        api_views.ArticleSubscribedListView.as_view(),
        name='api_article_subscribed',
    ),
    path(
        'articles/<int:pk>/',
        api_views.ArticleDetailView.as_view(),
        name='api_article_detail',
    ),
    path(
        'articles/<int:pk>/approve/',
        api_views.ArticleApproveView.as_view(),
        name='api_article_approve',
    ),

    # Newsletters
    path(
        'newsletters/',
        api_views.NewsletterListCreateView.as_view(),
        name='api_newsletter_list',
    ),
    path(
        'newsletters/<int:pk>/',
        api_views.NewsletterDetailView.as_view(),
        name='api_newsletter_detail',
    ),
]
