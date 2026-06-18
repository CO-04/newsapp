"""
Unit tests for the news app.

Covers models, web views (access control + happy paths), signals,
and REST API endpoints.
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Article, Newsletter, Publisher

User = get_user_model()


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def make_user(username, role, password='Pass1234!'):
    """Create and return a CustomUser with the given role."""
    return User.objects.create_user(
        username=username,
        email=f'{username}@example.com',
        password=password,
        role=role,
    )


def make_publisher(name='Test Publisher'):
    """Create and return a Publisher."""
    return Publisher.objects.create(name=name)


def make_article(author, publisher=None, approved=False, title='Test Article'):
    """Create and return an Article."""
    return Article.objects.create(
        title=title,
        content='Some content for the article.',
        author=author,
        publisher=publisher,
        approved=approved,
    )


def make_newsletter(author, title='Test Newsletter'):
    """Create and return a Newsletter."""
    return Newsletter.objects.create(
        title=title,
        description='A newsletter description.',
        author=author,
    )


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class PublisherModelTests(TestCase):
    """Tests for the Publisher model."""

    def test_str_returns_name(self):
        """__str__ returns the publisher name."""
        pub = make_publisher('BBC News')
        self.assertEqual(str(pub), 'BBC News')


class ArticleModelTests(TestCase):
    """Tests for the Article model."""

    def setUp(self):
        """Create a journalist for use in article tests."""
        self.journalist = make_user('journalist1', 'journalist')

    def test_str_includes_title_and_author(self):
        """__str__ contains both the title and the author's username."""
        article = make_article(self.journalist, title='Breaking News')
        self.assertIn('Breaking News', str(article))
        self.assertIn('journalist1', str(article))

    def test_approved_defaults_to_false(self):
        """New articles are unapproved by default."""
        article = make_article(self.journalist)
        self.assertFalse(article.approved)


class NewsletterModelTests(TestCase):
    """Tests for the Newsletter model."""

    def setUp(self):
        """Create a journalist for newsletter tests."""
        self.journalist = make_user('j2', 'journalist')

    def test_str_includes_title_and_author(self):
        """__str__ contains both the title and the author's username."""
        nl = make_newsletter(self.journalist, title='Weekly Digest')
        self.assertIn('Weekly Digest', str(nl))
        self.assertIn('j2', str(nl))


# ---------------------------------------------------------------------------
# Article list view
# ---------------------------------------------------------------------------

class ArticleListViewTests(TestCase):
    """Tests for the public article list view."""

    def setUp(self):
        """Create one approved and one unapproved article."""
        self.journalist = make_user('j3', 'journalist')
        self.approved = make_article(
            self.journalist, approved=True, title='Approved',
        )
        self.pending = make_article(
            self.journalist, approved=False, title='Pending',
        )
        self.url        = reverse('news:article_list')

    def test_article_list_returns_200(self):
        """Public home page returns HTTP 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_only_approved_articles_shown(self):
        """Unapproved articles are not shown on the public list."""
        response = self.client.get(self.url)
        self.assertContains(response, 'Approved')
        self.assertNotContains(response, 'Pending')


# ---------------------------------------------------------------------------
# Access control: decorator tests
# ---------------------------------------------------------------------------

class DecoratorAccessTests(TestCase):
    """Tests that role decorators block wrong roles with 403."""

    def setUp(self):
        """Create one user of each role."""
        self.reader     = make_user('reader1',     'reader')
        self.journalist = make_user('journalist1', 'journalist')
        self.editor     = make_user('editor1',     'editor')

    def test_journalist_required_blocks_reader(self):
        """A reader hitting a journalist-only URL gets 403."""
        self.client.force_login(self.reader)
        response = self.client.get(reverse('news:create_article'))
        self.assertEqual(response.status_code, 403)

    def test_journalist_required_allows_journalist(self):
        """A journalist can access the create-article page."""
        self.client.force_login(self.journalist)
        response = self.client.get(reverse('news:create_article'))
        self.assertEqual(response.status_code, 200)

    def test_editor_required_blocks_journalist(self):
        """A journalist hitting an editor-only URL gets 403."""
        self.client.force_login(self.journalist)
        response = self.client.get(reverse('news:editor_queue'))
        self.assertEqual(response.status_code, 403)

    def test_editor_required_allows_editor(self):
        """An editor can access the review queue."""
        self.client.force_login(self.editor)
        response = self.client.get(reverse('news:editor_queue'))
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_user_redirected_to_login(self):
        """An anonymous user is redirected to the login page."""
        response = self.client.get(reverse('news:create_article'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])


# ---------------------------------------------------------------------------
# Article approval + signal
# ---------------------------------------------------------------------------

class ArticleApprovalTests(TestCase):
    """Tests for the editor approval workflow and signal side-effects."""

    def setUp(self):
        """Create an editor and a pending article."""
        self.editor     = make_user('editor2', 'editor')
        self.journalist = make_user('j4', 'journalist')
        self.article    = make_article(self.journalist)

    @patch('news.utils.send_mail')
    @patch('news.utils.tweet_approved_article')
    def test_approve_sets_approved_flag(self, mock_tweet, mock_mail):
        """POSTing to approve_article sets article.approved = True."""
        self.client.force_login(self.editor)
        approve_url = reverse(
            'news:approve_article', args=[self.article.pk],
        )
        self.client.post(approve_url)
        self.article.refresh_from_db()
        self.assertTrue(self.article.approved)

    @patch('news.utils.send_mail')
    @patch('news.utils.tweet_approved_article')
    def test_approve_sends_email_to_subscribers(self, mock_tweet, mock_mail):
        """Approving an article triggers send_mail for subscribed readers."""
        reader = make_user('reader2', 'reader')
        reader.subscribed_journalists.add(self.journalist)

        self.client.force_login(self.editor)
        approve_url = reverse(
            'news:approve_article', args=[self.article.pk],
        )
        self.client.post(approve_url)

        mock_mail.assert_called_once()


# ---------------------------------------------------------------------------
# REST API: articles
# ---------------------------------------------------------------------------

class ArticleAPITests(TestCase):
    """Tests for the /api/articles/ endpoints."""

    def setUp(self):
        """Create users and an approved article; set up APIClient."""
        self.journalist = make_user('j5', 'journalist')
        self.reader     = make_user('reader3', 'reader')
        self.editor     = make_user('editor3', 'editor')
        self.article = make_article(
            self.journalist, approved=True, title='API Article',
        )
        self.client     = APIClient()

    def test_list_returns_approved_articles(self):
        """GET /api/articles/ returns approved articles to anonymous users."""
        response = self.client.get('/api/articles/')
        self.assertEqual(response.status_code, 200)
        # Accept paginated or plain list responses
        data = (
            response.data.get('results', response.data)
            if isinstance(response.data, dict)
            else response.data
        )
        self.assertTrue(any(a['title'] == 'API Article' for a in data))

    def test_unauthenticated_cannot_create_article(self):
        """Unauthenticated POST to /api/articles/ returns 401 or 403."""
        response = self.client.post('/api/articles/', {
            'title': 'Hack', 'content': 'content',
        })
        self.assertIn(response.status_code, [401, 403])

    def test_journalist_can_create_article(self):
        """Authenticated journalist can POST a new article."""
        self.client.force_authenticate(user=self.journalist)
        response = self.client.post('/api/articles/', {
            'title': 'New Via API',
            'content': 'Content here.',
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Article.objects.filter(title='New Via API').exists())

    def test_reader_cannot_create_article(self):
        """A reader POSTing to /api/articles/ gets 403."""
        self.client.force_authenticate(user=self.reader)
        response = self.client.post('/api/articles/', {
            'title': 'Reader hack', 'content': 'content',
        })
        self.assertEqual(response.status_code, 403)


# ---------------------------------------------------------------------------
# REST API: approval endpoint
# ---------------------------------------------------------------------------

class ArticleApproveAPITests(TestCase):
    """Tests for PATCH /api/articles/<pk>/approve/."""

    def setUp(self):
        """Create editor, journalist, and a pending article."""
        self.editor     = make_user('editor4', 'editor')
        self.journalist = make_user('j6', 'journalist')
        self.article    = make_article(self.journalist)
        self.client     = APIClient()

    @patch('news.utils.send_mail')
    @patch('news.utils.tweet_approved_article')
    def test_editor_can_approve_via_api(self, mock_tweet, mock_mail):
        """An editor PATCHing the approve endpoint sets approved=True."""
        self.client.force_authenticate(user=self.editor)
        approve_url = f'/api/articles/{self.article.pk}/approve/'
        response = self.client.patch(approve_url)
        self.assertEqual(response.status_code, 200)
        self.article.refresh_from_db()
        self.assertTrue(self.article.approved)

    def test_non_editor_cannot_approve_via_api(self):
        """A journalist PATCHing the approve endpoint gets 403."""
        self.client.force_authenticate(user=self.journalist)
        approve_url = f'/api/articles/{self.article.pk}/approve/'
        response = self.client.patch(approve_url)
        self.assertEqual(response.status_code, 403)


# ---------------------------------------------------------------------------
# REST API: publishers
# ---------------------------------------------------------------------------

class PublisherAPITests(TestCase):
    """Tests for the /api/publishers/ endpoints."""

    def setUp(self):
        """Create users and a publisher."""
        self.editor     = make_user('editor5', 'editor')
        self.journalist = make_user('j7', 'journalist')
        self.publisher  = make_publisher('Test Outlet')
        self.client     = APIClient()

    def test_list_publishers_is_public(self):
        """GET /api/publishers/ returns 200 for anonymous users."""
        response = self.client.get('/api/publishers/')
        self.assertEqual(response.status_code, 200)

    def test_editor_can_create_publisher(self):
        """An editor can POST a new publisher."""
        self.client.force_authenticate(user=self.editor)
        response = self.client.post('/api/publishers/', {'name': 'New Outlet'})
        self.assertEqual(response.status_code, 201)

    def test_journalist_cannot_create_publisher(self):
        """A journalist POSTing to /api/publishers/ gets 403."""
        self.client.force_authenticate(user=self.journalist)
        response = self.client.post(
            '/api/publishers/', {'name': 'Bad Outlet'},
        )
        self.assertEqual(response.status_code, 403)


# ---------------------------------------------------------------------------
# REST API: subscribed articles
# ---------------------------------------------------------------------------

class ArticleSubscribedAPITests(TestCase):
    """Tests for GET /api/articles/subscribed/."""

    def setUp(self):
        """Create users, articles, and subscriptions."""
        self.journalist = make_user('j_sub', 'journalist')
        self.publisher  = make_publisher('Sub Publisher')
        self.reader     = make_user('r_sub', 'reader')
        self.j_article  = make_article(
            self.journalist,
            approved=True,
            title='Journalist Article',
        )
        self.p_article = make_article(
            self.journalist,
            publisher=self.publisher,
            approved=True,
            title='Publisher Article',
        )
        other_j = make_user('other_j', 'journalist')
        self.other_article = make_article(
            other_j, approved=True, title='Other Article',
        )
        self.reader.subscribed_journalists.add(self.journalist)
        self.reader.subscribed_publishers.add(self.publisher)
        self.client = APIClient()

    def test_reader_gets_subscribed_articles(self):
        """Authenticated reader sees only their subscribed content."""
        self.client.force_authenticate(user=self.reader)
        response = self.client.get('/api/articles/subscribed/')
        self.assertEqual(response.status_code, 200)
        titles = [a['title'] for a in response.data]
        self.assertIn('Journalist Article', titles)
        self.assertIn('Publisher Article', titles)
        self.assertNotIn('Other Article', titles)

    def test_unauthenticated_cannot_access_subscribed(self):
        """Unauthenticated GET /api/articles/subscribed/ is rejected."""
        response = self.client.get('/api/articles/subscribed/')
        self.assertIn(response.status_code, [401, 403])


# ---------------------------------------------------------------------------
# REST API: newsletters
# ---------------------------------------------------------------------------

class NewsletterAPITests(TestCase):
    """Tests for the /api/newsletters/ endpoints."""

    def setUp(self):
        """Create journalist, reader, article, and newsletter."""
        self.journalist = make_user('j_nl', 'journalist')
        self.reader     = make_user('r_nl', 'reader')
        self.article    = make_article(
            self.journalist, approved=True, title='NL Article',
        )
        self.newsletter = make_newsletter(
            self.journalist, title='Weekly Digest',
        )
        self.newsletter.articles.add(self.article)
        self.client = APIClient()

    def test_list_newsletters_is_public(self):
        """GET /api/newsletters/ returns 200 for anonymous users."""
        response = self.client.get('/api/newsletters/')
        self.assertEqual(response.status_code, 200)

    def test_journalist_can_create_newsletter(self):
        """Authenticated journalist can POST a new newsletter."""
        self.client.force_authenticate(user=self.journalist)
        response = self.client.post(
            '/api/newsletters/',
            {
                'title':       'New NL',
                'description': 'A description.',
                'article_ids': [self.article.pk],
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)

    def test_reader_cannot_create_newsletter(self):
        """A reader POSTing to /api/newsletters/ gets 403."""
        self.client.force_authenticate(user=self.reader)
        response = self.client.post(
            '/api/newsletters/',
            {'title': 'NL', 'description': 'x'},
        )
        self.assertEqual(response.status_code, 403)


# ---------------------------------------------------------------------------
# REST API: editor delete
# ---------------------------------------------------------------------------

class ArticleDeleteAPITests(TestCase):
    """Tests for DELETE /api/articles/<pk>/."""

    def setUp(self):
        """Create editor, journalist, and a published article."""
        self.editor     = make_user('editor_del', 'editor')
        self.journalist = make_user('j_del', 'journalist')
        self.article    = make_article(
            self.journalist, approved=True,
        )
        self.client = APIClient()

    def test_editor_can_delete_article(self):
        """An editor can DELETE an article."""
        self.client.force_authenticate(user=self.editor)
        url = f'/api/articles/{self.article.pk}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            Article.objects.filter(pk=self.article.pk).exists()
        )

    def test_reader_cannot_delete_article(self):
        """A reader cannot DELETE an article."""
        reader = make_user('reader_del', 'reader')
        self.client.force_authenticate(user=reader)
        url = f'/api/articles/{self.article.pk}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)
