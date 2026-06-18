from django.conf import settings
from django.db import models


class Publisher(models.Model):
    """
    A named publication affiliated with multiple journalists and editors.

    Journalists link via the reverse relation on CustomUser's
    subscribed_publishers M2M field, keeping the schema normalised.
    A Publisher is the optional parent of an Article.
    """

    name        = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    logo        = models.ImageField(upload_to='publisher_logos/', blank=True)
    website     = models.URLField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return the publisher name."""
        return self.name


class Article(models.Model):
    """
    A news article authored by a Journalist.

    An article is associated with EITHER a publisher (publisher-content) OR no
    publisher (independent).  It is visible to readers only once an Editor sets
    approved=True.

    Fields
    ------
    author    : FK → CustomUser (journalist)
    publisher : FK → Publisher (nullable — independent articles)
    approved  : Boolean controlled exclusively by editors
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
        """Return article title and author username."""
        return f'{self.title} – {self.author.username}'


class Newsletter(models.Model):
    """
    A curated collection of articles created by a Journalist.

    Readers can view newsletters; Journalists and Editors can create and edit
    them.  The many-to-many relation to Article allows the same article to
    appear in multiple newsletters.
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
        """Return newsletter title and author username."""
        return f'{self.title} by {self.author.username}'
