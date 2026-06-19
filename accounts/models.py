"""
accounts.models
===============

Custom user model for the NewsApp accounts module.

Models
------
CustomUser
    Extends Django's ``AbstractUser`` with a role field and reader
    subscription relations.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Extended user model supporting three roles: Reader, Journalist, Editor.

    :ivar role: The user's assigned role; one of ``reader``,
        ``journalist``, or ``editor``.
    :vartype role: str
    :ivar email: Unique email address used for login and notifications.
    :vartype email: str
    :ivar bio: Optional biographical text displayed on the profile page.
    :vartype bio: str
    :ivar subscribed_publishers: Publishers the reader follows.
    :vartype subscribed_publishers: ManyToManyField(Publisher)
    :ivar subscribed_journalists: Journalists the reader follows.
    :vartype subscribed_journalists: ManyToManyField(CustomUser)

    .. note::
        Role is set at registration and drives group assignment via a
        ``post_save`` signal in ``accounts/signals.py``.
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
        """Return ``True`` if this user has the Reader role.

        :returns: ``True`` if ``role == 'reader'``.
        :rtype: bool
        """
        return self.role == 'reader'

    def is_journalist(self):
        """Return ``True`` if this user has the Journalist role.

        :returns: ``True`` if ``role == 'journalist'``.
        :rtype: bool
        """
        return self.role == 'journalist'

    def is_editor(self):
        """Return ``True`` if this user has the Editor role or is a superuser.

        :returns: ``True`` if ``role == 'editor'`` or ``is_superuser``.
        :rtype: bool
        """
        return self.role == 'editor' or self.is_superuser

    def __str__(self):
        """Return username and role as a human-readable string.

        :returns: A string in the format ``'<username> (<role>)'``.
        :rtype: str
        """
        return f'{self.username} ({self.get_role_display()})'
