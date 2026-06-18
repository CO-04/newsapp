"""
Utility functions for the news app.

``send_approval_emails`` — notify subscribers when an article is approved.
``tweet_approved_article`` — post a tweet via TwitterService (best-effort).
"""

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


def send_approval_emails(article):
    """
    Send a notification email to every subscriber who follows the article's
    author or publisher.

    Deduplication is handled by collecting recipient addresses into a set
    before sending so that readers who follow both the journalist and the
    publisher only receive one email.
    """
    recipients = set()

    # Readers subscribed to this journalist
    for user in article.author.readers.all():
        if user.email:
            recipients.add(user.email)

    # Readers subscribed to this publisher (if the article has one)
    if article.publisher:
        for user in article.publisher.subscribers.all():
            if user.email:
                recipients.add(user.email)

    if not recipients:
        return

    subject = f'New article: {article.title}'
    message = render_to_string(
        'news/email_article.txt',
        {'article': article},
    )
    from_email = getattr(
        settings, 'DEFAULT_FROM_EMAIL', 'noreply@newsapp.local',
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=list(recipients),
        fail_silently=True,
    )


def tweet_approved_article(article):
    """
    Post a tweet announcing the newly approved article.

    Attaches the article image if one exists.  Failures are swallowed
    silently so that a missing or invalid Twitter configuration never
    breaks the approval workflow.
    """
    try:
        from .twitter import TwitterService
        service = TwitterService()
        url   = f"/articles/{article.pk}/"
        text  = f'New article published: "{article.title}" {url}'
        image = (
            article.image
            if (article.image and article.image.name)
            else None
        )
        service.tweet(text, image_field=image)
    except Exception:  # noqa: BLE001
        pass
