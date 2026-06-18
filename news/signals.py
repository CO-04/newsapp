"""
Signal handlers for the news app.

Listens for the post_save signal on Article and fires notification
logic when an article is approved for the first time.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Article


@receiver(post_save, sender=Article)
def on_article_approved(sender, instance, **kwargs):
    """
    Fire notifications when an article is approved for the first time.

    The ``_just_approved`` flag is set by the ``approve_article`` view
    and the ``approve_selected`` admin action immediately before
    ``article.save()``.  Without that flag this handler is a no-op,
    which prevents spurious emails on every subsequent edit.
    """
    if not getattr(instance, '_just_approved', False):
        return

    from .utils import send_approval_emails, tweet_approved_article

    send_approval_emails(instance)
    tweet_approved_article(instance)
