from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Extended user model supporting three roles: Reader, Journalist, Editor.

    Reader fields
    -------------
    subscribed_publishers : ManyToManyField → news.Publisher
    subscribed_journalists : ManyToManyField (self, symmetrical=False)

    Journalist / Editor fields
    --------------------------
    Articles and Newsletters are accessed via reverse FK relations
    (articles, newsletters) on the relevant models.

    Notes
    -----
    - email is enforced unique so password reset and subscription emails work.
    - Role is set at registration and drives group assignment via a post_save
      signal in accounts/signals.py.
    """

    ROLE_CHOICES = [
        ('reader',     'Reader'),
        ('journalist', 'Journalist'),
        ('editor',     'Editor'),
    ]

    role  = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default='reader',
    )
    email = models.EmailField(unique=True)  # duplicate emails blocked
    bio   = models.TextField(blank=True)

    # Reader subscription fields (empty for journalists/editors)
    subscribed_publishers = models.ManyToManyField(
        'news.Publisher',
        blank=True,
        related_name='subscribers',
    )
    subscribed_journalists = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='readers',
    )

    def is_reader(self):
        """Return True if this user has the Reader role."""
        return self.role == 'reader'

    def is_journalist(self):
        """Return True if this user has the Journalist role."""
        return self.role == 'journalist'

    def is_editor(self):
        """Return True if this user has the Editor role or is a superuser."""
        return self.role == 'editor' or self.is_superuser

    def __str__(self):
        """Return username and role as a readable representation."""
        return f'{self.username} ({self.get_role_display()})'
