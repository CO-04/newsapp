"""
DRF API views for the news app.

Endpoints
---------
Publishers
  GET  /api/publishers/          – list all publishers
  POST /api/publishers/          – create a publisher (editor only)
  GET  /api/publishers/<pk>/     – publisher detail
  PUT/PATCH /api/publishers/<pk>/– update a publisher (editor only)
  DELETE    /api/publishers/<pk>/– delete a publisher (editor only)

Articles
  GET  /api/articles/       – list articles (filtered by role)
  POST /api/articles/            – create article (journalist only)
  GET  /api/articles/<pk>/       – article detail
  PUT/PATCH /api/articles/<pk>/  – update article (author or editor)
  DELETE    /api/articles/<pk>/  – delete article (author or editor)
  PATCH     /api/articles/<pk>/approve/ – approve article (editor only)

Newsletters
  GET  /api/newsletters/         – list all newsletters
  POST /api/newsletters/         – create newsletter (journalist only)
  GET  /api/newsletters/<pk>/    – newsletter detail
  PUT/PATCH /api/newsletters/<pk>/– update newsletter (author or editor)
  DELETE    /api/newsletters/<pk>/– delete newsletter (author or editor)

JWT Auth
  POST /api/token/               – obtain access + refresh tokens
  POST /api/token/refresh/       – refresh access token
"""

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Article, Newsletter, Publisher
from .permissions import (
    IsApprovedOrAuthorOrEditor,
    IsAuthorOrEditor,
    IsEditorOrReadOnly,
    IsJournalistOrReadOnly,
)
from .serializers import (
    ArticleApprovalSerializer,
    ArticleSerializer,
    NewsletterSerializer,
    PublisherSerializer,
)


# ---------------------------------------------------------------------------
# Publisher endpoints
# ---------------------------------------------------------------------------

class PublisherListCreateView(generics.ListCreateAPIView):
    """
    GET  – list all publishers (public).
    POST – create a publisher (editor only).
    """

    queryset           = Publisher.objects.order_by('name')
    serializer_class   = PublisherSerializer
    permission_classes = [IsEditorOrReadOnly]


class PublisherDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    – publisher detail (public).
    PUT / PATCH / DELETE – editor only.
    """

    queryset           = Publisher.objects.all()
    serializer_class   = PublisherSerializer
    permission_classes = [IsEditorOrReadOnly]


# ---------------------------------------------------------------------------
# Article endpoints
# ---------------------------------------------------------------------------

class ArticleListCreateView(generics.ListCreateAPIView):
    """
    GET  – list approved articles; authors and editors also see unapproved.
    POST – create an article (journalist only).
    """

    serializer_class   = ArticleSerializer
    permission_classes = [IsJournalistOrReadOnly]

    def get_queryset(self):
        """Return articles visible to the requesting user."""
        user = self.request.user
        qs = (
            Article.objects
            .select_related('author', 'publisher')
            .order_by('-created_at')
        )
        if user.is_authenticated and (
            user.is_editor() or user.is_journalist()
        ):
            # Editors see all; journalists see approved + own drafts
            if user.is_journalist():
                from django.db.models import Q
                return qs.filter(Q(approved=True) | Q(author=user))
            return qs
        return qs.filter(approved=True)

    def perform_create(self, serializer):
        """Set the author to the logged-in journalist."""
        serializer.save(author=self.request.user)


class ArticleSubscribedListView(generics.ListAPIView):
    """
    GET /api/articles/subscribed/

    Returns approved articles from the authenticated reader's
    subscribed publishers and journalists.

    Non-readers receive an empty list — subscriptions are a
    reader-only concept.
    """

    serializer_class   = ArticleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return articles the requesting reader subscribes to."""
        user = self.request.user
        if not user.is_reader():
            return Article.objects.none()
        from django.db.models import Q
        pub_ids = user.subscribed_publishers.values_list(
            'pk', flat=True,
        )
        journalist_ids = user.subscribed_journalists.values_list(
            'pk', flat=True,
        )
        return (
            Article.objects
            .filter(approved=True)
            .filter(
                Q(publisher__in=pub_ids)
                | Q(author__in=journalist_ids)
            )
            .order_by('-created_at')
        )


class ArticleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET          – article detail; unapproved visible to author/editor.
    PUT / PATCH  – update (author or editor).
    DELETE       – delete (author or editor).
    """

    queryset           = Article.objects.select_related('author', 'publisher')
    serializer_class   = ArticleSerializer
    permission_classes = [IsApprovedOrAuthorOrEditor, IsAuthorOrEditor]


class ArticleApproveView(APIView):
    """
    PATCH /api/articles/<pk>/approve/

    Set approved=True on an article.  Editor only.
    Fires the ``_just_approved`` signal so notification emails are sent.
    """

    permission_classes = [IsEditorOrReadOnly]

    def patch(self, request, pk):
        """Approve the article identified by ``pk``."""
        article = generics.get_object_or_404(Article, pk=pk)
        if article.approved:
            return Response(
                {'detail': 'Article is already approved.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        article._just_approved = True
        article.approved       = True
        article.save()
        return Response(ArticleApprovalSerializer(article).data)


# ---------------------------------------------------------------------------
# Newsletter endpoints
# ---------------------------------------------------------------------------

class NewsletterListCreateView(generics.ListCreateAPIView):
    """
    GET  – list all newsletters (public).
    POST – create a newsletter (journalist only).
    """

    queryset = (
        Newsletter.objects
        .select_related('author')
        .order_by('-created_at')
    )
    serializer_class   = NewsletterSerializer
    permission_classes = [IsJournalistOrReadOnly]

    def perform_create(self, serializer):
        """Set the author to the logged-in journalist."""
        serializer.save(author=self.request.user)


class NewsletterDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET          – newsletter detail (public).
    PUT / PATCH  – update (author or editor).
    DELETE       – delete (author or editor).
    """

    queryset = (
        Newsletter.objects
        .select_related('author')
        .prefetch_related('articles')
    )
    serializer_class   = NewsletterSerializer
    permission_classes = [IsAuthorOrEditor]
