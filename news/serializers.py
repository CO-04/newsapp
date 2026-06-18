"""
news.serializers
================

Django REST Framework serializers for the NewsApp news module.

Each serializer maps one model to its JSON representation used by
the API. Read (list/detail) and write (create/update) operations are
handled by the same class where possible. The ``author`` field is
always set from the request context in the view, never accepted from
the client.

Serializers
-----------
PublisherSerializer
    Full read/write serializer for Publisher.
ArticleSerializer
    Serializer for Article, with a read-only ``author_username`` field.
NewsletterSerializer
    Serializer for Newsletter, exposing articles as a list of PKs.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Article, Newsletter, Publisher

User = get_user_model()


class PublisherSerializer(serializers.ModelSerializer):
    """Serializer for the Publisher model.

    Exposes all public-facing fields. Creation and updates are
    restricted to editors via the API view's permission class.

    :ivar id: Auto-generated primary key (read-only).
    :vartype id: int
    :ivar name: Unique display name of the publisher.
    :vartype name: str
    :ivar description: Optional long-form description.
    :vartype description: str
    :ivar logo: URL path to the publisher's logo image.
    :vartype logo: str
    :ivar website: Optional external website URL.
    :vartype website: str
    :ivar created_at: ISO-8601 creation timestamp (read-only).
    :vartype created_at: str
    """

    class Meta:
        """Serializer configuration."""

        model  = Publisher
        fields = ['id', 'name', 'description', 'logo', 'website', 'created_at']
        read_only_fields = ['id', 'created_at']


class ArticleSerializer(serializers.ModelSerializer):
    """Serializer for the Article model.

    ``author_username`` is a read-only convenience field so API
    consumers can display the author's name without a separate request.
    ``author`` (PK) is set automatically by the view and excluded
    from writeable input.

    :ivar id: Auto-generated primary key (read-only).
    :vartype id: int
    :ivar title: Headline of the article.
    :vartype title: str
    :ivar content: Full body text of the article.
    :vartype content: str
    :ivar author: PK of the authoring journalist (read-only).
    :vartype author: int
    :ivar author_username: Username of the author (read-only).
    :vartype author_username: str
    :ivar publisher: PK of the associated publisher, or ``null``.
    :vartype publisher: int or None
    :ivar submitted: Whether the article has been submitted for review.
    :vartype submitted: bool
    :ivar approved: Whether the article has been approved (read-only).
    :vartype approved: bool
    :ivar image: URL path to the article image, if any.
    :vartype image: str
    :ivar created_at: ISO-8601 creation timestamp (read-only).
    :vartype created_at: str
    :ivar updated_at: ISO-8601 last-updated timestamp (read-only).
    :vartype updated_at: str
    """

    author_username = serializers.CharField(
        source='author.username', read_only=True,
    )

    class Meta:
        """Serializer configuration."""

        model  = Article
        fields = [
            'id', 'title', 'content', 'author', 'author_username',
            'publisher', 'submitted', 'approved',
            'image', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'author', 'author_username', 'approved',
                            'created_at', 'updated_at']


class NewsletterSerializer(serializers.ModelSerializer):
    """Serializer for the Newsletter model.

    ``article_ids`` exposes the M2M relation as a list of primary keys,
    restricted to approved articles only.
    ``author_username`` is a read-only convenience field.

    :ivar id: Auto-generated primary key (read-only).
    :vartype id: int
    :ivar title: Headline of the newsletter.
    :vartype title: str
    :ivar description: Optional summary of the newsletter's contents.
    :vartype description: str
    :ivar author: PK of the authoring journalist (read-only).
    :vartype author: int
    :ivar author_username: Username of the author (read-only).
    :vartype author_username: str
    :ivar article_ids: List of PKs of approved articles to include.
    :vartype article_ids: list[int]
    :ivar created_at: ISO-8601 creation timestamp (read-only).
    :vartype created_at: str
    :ivar updated_at: ISO-8601 last-updated timestamp (read-only).
    :vartype updated_at: str
    """

    author_username = serializers.CharField(
        source='author.username', read_only=True,
    )
    article_ids     = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Article.objects.filter(approved=True),
        source='articles',
    )

    class Meta:
        """Serializer configuration."""

        model  = Newsletter
        fields = [
            'id', 'title', 'description', 'author', 'author_username',
            'article_ids', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'author', 'author_username',
            'created_at', 'updated_at',
        ]


class ArticleApprovalSerializer(serializers.ModelSerializer):
    """
    Minimal serializer used by the editor approval endpoint.

    Only exposes the ``approved`` flag so that clients cannot
    accidentally overwrite other article fields via this endpoint.
    """

    class Meta:
        """Serializer configuration."""

        model  = Article
        fields = ['id', 'approved']
        read_only_fields = ['id']


class UserSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for the CustomUser model.

    Exposes safe public-facing fields only — the password hash
    is never included.
    """

    class Meta:
        """Serializer configuration."""

        model  = User
        fields = ['id', 'username', 'email', 'role', 'bio']
        read_only_fields = ['id', 'username', 'email', 'role']
