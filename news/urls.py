"""
URL configuration for the news app web views.

API endpoints are in news/api_urls.py and registered under /api/ in
newsapp/urls.py.
"""

from django.urls import path

from . import views

app_name = 'news'

urlpatterns = [
    # Home / article list
    path('', views.article_list, name='article_list'),

    # Article CRUD + approval
    path('articles/create/', views.create_article, name='create_article'),
    path('articles/<int:pk>/', views.article_detail, name='article_detail'),
    path(
        'articles/<int:pk>/edit/',
        views.edit_article,
        name='edit_article',
    ),
    path(
        'articles/<int:pk>/delete/',
        views.delete_article,
        name='delete_article',
    ),
    path(
        'articles/<int:pk>/approve/',
        views.approve_article,
        name='approve_article',
    ),
    path(
        'articles/<int:pk>/reject/',
        views.reject_article,
        name='reject_article',
    ),

    # Editor queue
    path('editor/queue/', views.editor_queue, name='editor_queue'),

    # Journalist dashboard
    path(
        'journalist/dashboard/',
        views.journalist_dashboard,
        name='journalist_dashboard',
    ),

    # Newsletter CRUD
    path('newsletters/', views.newsletter_list, name='newsletter_list'),
    path(
        'newsletters/create/',
        views.create_newsletter,
        name='create_newsletter',
    ),
    path(
        'newsletters/<int:pk>/',
        views.newsletter_detail,
        name='newsletter_detail',
    ),
    path(
        'newsletters/<int:pk>/edit/',
        views.edit_newsletter,
        name='edit_newsletter',
    ),
    path(
        'newsletters/<int:pk>/delete/',
        views.delete_newsletter,
        name='delete_newsletter',
    ),

    # Publisher CRUD & journalist profiles
    path(
        'publishers/create/',
        views.create_publisher,
        name='create_publisher',
    ),
    path(
        'publishers/<int:pk>/',
        views.publisher_detail,
        name='publisher_detail',
    ),
    path(
        'publishers/<int:pk>/edit/',
        views.edit_publisher,
        name='edit_publisher',
    ),
    path(
        'publishers/<int:pk>/delete/',
        views.delete_publisher,
        name='delete_publisher',
    ),
    path(
        'journalists/<int:pk>/',
        views.journalist_profile,
        name='journalist_profile',
    ),

    # Reader subscriptions
    path(
        'subscribe/publisher/<int:pk>/',
        views.subscribe_publisher,
        name='subscribe_publisher',
    ),
    path(
        'subscribe/journalist/<int:pk>/',
        views.subscribe_journalist,
        name='subscribe_journalist',
    ),
]
