"""
news.api_views
==============

Django REST Framework API views for the NewsApp news module.

Endpoints
---------
Publishers
    ``GET/POST /api/publishers/`` — list or create publishers.
    ``GET/PUT/PATCH/DELETE /api/publishers/<pk>/`` — detail, update, delete.

Articles
    ``GET/POST /api/articles/`` — list (role-filtered) or create.
    ``GET /api/articles/subscribed/`` — reader's subscription feed.
    ``GET/PUT/PATCH/DELETE /api/articles/<pk>/`` — detail, update, delete.
    ``PATCH /api/articles/<pk>/approve/`` — editor approval.

Newsletters
    ``GET/POST /api/newsletters/`` — list or create.
    ``GET/PUT/PATCH/DELETE /api/newsletters/<pk>/`` — detail, update, delete.

JWT Auth
    ``POST /api/token/`` — obtain access + refresh tokens.
    ``POST /api/token/refresh/`` — refresh access token.
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
    """List all publishers or create a new one.

    - ``GET`` — public; returns all publishers ordered by name.
    - ``POST`` — editors only; creates a new publisher.

    :permission_classes: :class:`IsEditorOrReadOnly`
    """

    queryset           = Publisher.objects.order_by('name')
    serializer_class   = PublisherSerializer
    permission_classes = [IsEditorOrReadOnly]


class PublisherDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a single publisher.

    - ``GET`` — public; returns publisher detail.
    - ``PUT`` / ``PATCH`` / ``DELETE`` — editors only.

    :permission_classes: :class:`IsEditorOrReadOnly`
    """

    queryset           = Publisher.objects.all()
    serializer_class   = PublisherSerializer
    permission_classes = [IsEditorOrReadOnly]


# ---------------------------------------------------------------------------
# Article endpoints
# ---------------------------------------------------------------------------

class ArticleListCreateView(generics.ListCreateAPIView):
    """List articles (role-filtered) or create a new article.

    - ``GET`` — approved articles for anonymous/readers; editors see
      all; journalists see approved plus their own drafts.
    - ``POST`` — journalists only; author is set from the request.

    :permission_classes: :class:`IsJournalistOrReadOnly`
    """

    serializer_class   = ArticleSerializer
    permission_classes = [IsJournalistOrReadOnly]

    def get_queryset(self):
        """Return articles visible to the requesting user.

        :returns: Queryset of articles filtered by the user's role.
        :rtype: QuerySet
        """
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
        """Set the author to the logged-in journalist before saving.

        :param serializer: The validated article serializer instance.
        :type serializer: ArticleSerializer
        """
        serializer.save(author=self.request.user)


class ArticleSubscribedListView(generics.ListAPIView):
    """Return approved articles from a reader's subscriptions.

    ``GET /api/articles/subscribed/`` — authenticated readers only.
    Returns articles from the reader's subscribed publishers and
    journalists. Non-readers receive an empty list.

    :permission_classes: :class:`IsAuthenticated`
    """

    serializer_class   = ArticleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return articles the requesting reader subscribes to.

        :returns: Queryset of approved articles from subscribed sources,
            or an empty queryset for non-readers.
        :rtype: QuerySet
        """
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
    """Retrieve, update, or delete a single article.

    - ``GET`` — unapproved articles visible to their author or editors.
    - ``PUT`` / ``PATCH`` — author or editor only.
    - ``DELETE`` — author or editor only.

    :permission_classes: :class:`IsApprovedOrAuthorOrEditor`,
        :class:`IsAuthorOrEditor`
    """

    queryset           = Article.objects.select_related('author', 'publisher')
    serializer_class   = ArticleSerializer
    permission_classes = [IsApprovedOrAuthorOrEditor, IsAuthorOrEditor]


class ArticleApproveView(APIView):
    """Approve a submitted article.

    ``PATCH /api/articles/<pk>/approve/`` — editors only.
    Sets ``approved=True`` and fires the ``_just_approved`` signal so
    notification emails are sent to subscribed readers.

    :permission_classes: :class:`IsEditorOrReadOnly`
    """

    permission_classes = [IsEditorOrReadOnly]

    def patch(self, request, pk):
        """Approve the article identified by ``pk``.

        :param request: The incoming HTTP request.
        :type request: HttpRequest
        :param pk: Primary key of the article to approve.
        :type pk: int
        :returns: Serialized article data on success, or a 400 error
            if the article is already approved.
        :rtype: Response
        """
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
    """List all newsletters or create a new one.

    - ``GET`` — public; returns all newsletters ordered by newest first.
    - ``POST`` — journalists only; author is set from the request.

    :permission_classes: :class:`IsJournalistOrReadOnly`
    """

    queryset = (
        Newsletter.objects
        .select_related('author')
        .order_by('-created_at')
    )
    serializer_class   = NewsletterSerializer
    permission_classes = [IsJournalistOrReadOnly]

    def perform_create(self, serializer):
        """Set the author to the logged-in journalist before saving.

        :param serializer: The validated newsletter serializer instance.
        :type serializer: NewsletterSerializer
        """
        serializer.save(author=self.request.user)


class NewsletterDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a single newsletter.

    - ``GET`` — public; returns newsletter detail with articles.
    - ``PUT`` / ``PATCH`` / ``DELETE`` — author or editor only.

    :permission_classes: :class:`IsAuthorOrEditor`
    """

    queryset = (
        Newsletter.objects
        .select_related('author')
        .prefetch_related('articles')
    )
    serializer_class   = NewsletterSerializer
    permission_classes = [IsAuthorOrEditor]
