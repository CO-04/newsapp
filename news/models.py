"""
news.models
===========

Database models for the NewsApp news module.

Models
------
Publisher
    A named publication that groups journalists and articles.
Article
    A news article written by a journalist, subject to editor approval.
Newsletter
    A curated collection of articles created by a journalist.
"""

from django.conf import settings
from django.db import models


class Publisher(models.Model):
    """
    A named publication affiliated with multiple journalists and editors.

    Journalists link via the reverse relation on CustomUser's
    subscribed_publishers M2M field, keeping the schema normalised.
    A Publisher is the optional parent of an Article.

    :ivar name: Unique display name of the publisher.
    :vartype name: str
    :ivar description: Optional long-form description of the publication.
    :vartype description: str
    :ivar logo: Optional logo image stored under ``publisher_logos/``.
    :vartype logo: ImageField
    :ivar website: Optional URL of the publisher's external website.
    :vartype website: str
    :ivar created_at: Timestamp set automatically when the record is created.
    :vartype created_at: datetime
    """

    name        = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    logo        = models.ImageField(upload_to='publisher_logos/', blank=True)
    website     = models.URLField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return the publisher name as a human-readable string.

        :returns: The publisher's unique name.
        :rtype: str
        """
        return self.name


class Article(models.Model):
    """
    A news article authored by a Journalist.

    An article is associated with EITHER a publisher (publisher-content) OR no
    publisher (independent).  It is visible to readers only once an Editor sets
    ``approved=True``.

    :ivar title: Headline of the article (max 300 characters).
    :vartype title: str
    :ivar content: Full body text of the article.
    :vartype content: str
    :ivar author: The journalist who wrote the article.
    :vartype author: CustomUser
    :ivar publisher: The publisher this article belongs to, or ``None`` for
        independent articles.
    :vartype publisher: Publisher or None
    :ivar created_at: Timestamp set automatically when the record is created.
    :vartype created_at: datetime
    :ivar updated_at: Timestamp updated automatically on every save.
    :vartype updated_at: datetime
    :ivar approved: ``True`` once an editor has approved the article for
        public viewing.
    :vartype approved: bool
    :ivar submitted: ``True`` when the journalist has submitted the article
        for editorial review.
    :vartype submitted: bool
    :ivar image: Optional article image stored under ``article_images/``.
    :vartype image: ImageField
    """

    title      = models.CharField(max_length=300)
    content    = models.TextField()
    author     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='articles',
        limit_choices_to={'role': 'journalist'},
    )
    publisher  = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved   = models.BooleanField(default=False)
    submitted  = models.BooleanField(default=False)  # ready for review
    image      = models.ImageField(upload_to='article_images/', blank=True)

    def __str__(self):
        """Return a human-readable representation of the article.

        :returns: A string in the format ``'<title> – <author username>'``.
        :rtype: str
        """
        return f'{self.title} – {self.author.username}'


class Newsletter(models.Model):
    """
    A curated collection of articles created by a Journalist.

    Readers can view newsletters; Journalists and Editors can create and edit
    them.  The many-to-many relation to Article allows the same article to
    appear in multiple newsletters.

    :ivar title: Headline of the newsletter (max 300 characters).
    :vartype title: str
    :ivar description: Optional summary of the newsletter's contents.
    :vartype description: str
    :ivar author: The user who created the newsletter.
    :vartype author: CustomUser
    :ivar articles: The articles included in this newsletter.
    :vartype articles: ManyToManyField(Article)
    :ivar created_at: Timestamp set automatically when the record is created.
    :vartype created_at: datetime
    :ivar updated_at: Timestamp updated automatically on every save.
    :vartype updated_at: datetime
    """

    title       = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    author      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='newsletters',
    )
    articles = models.ManyToManyField(
        Article, blank=True, related_name='newsletters',
    )
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    def __str__(self):
        """Return a human-readable representation of the newsletter.

        :returns: A string in the format ``'<title> by <author username>'``.
        :rtype: str
        """
        return f'{self.title} by {self.author.username}'
