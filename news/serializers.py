"""
DRF serializers for the news app.

Each serializer maps one model to its JSON representation used by the API.
Read (list/detail) and write (create/update) serializers are kept in the same
class where possible; author is always set from the request in the view, never
accepted from the client.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Article, Newsletter, Publisher

User = get_user_model()


class PublisherSerializer(serializers.ModelSerializer):
    """
    Serializer for the Publisher model.

    Exposes all public-facing fields.  Creation and updates are restricted to
    editors via the API view's permission class.
    """

    class Meta:
        """Serializer configuration."""

        model  = Publisher
        fields = ['id', 'name', 'description', 'logo', 'website', 'created_at']
        read_only_fields = ['id', 'created_at']


class ArticleSerializer(serializers.ModelSerializer):
    """
    Serializer for the Article model.

    ``author_username`` is a read-only convenience field so API consumers can
    display the author's name without a separate request.  ``author`` (PK) is
    set automatically by the view and is excluded from writeable input.
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
    """
    Serializer for the Newsletter model.

    ``article_ids`` exposes the M2M relation as a list of primary keys.
    ``author_username`` is a convenience read-only field.
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
