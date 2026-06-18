"""
Twitter / X integration for the news app.

Singleton service that wraps ``requests-oauthlib`` to post tweets
(with optional image attachment) via the X v2 API.
Credentials are read from Django settings, which in turn reads them
from .env via python-decouple — nothing sensitive is hard-coded.
"""

import logging
import mimetypes

from requests_oauthlib import OAuth1Session

logger = logging.getLogger(__name__)


class TwitterService:
    """Singleton service for posting to X (Twitter) via API v2."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.oauth = cls._instance._build_oauth()
        return cls._instance

    def _build_oauth(self):
        from django.conf import settings

        api_key             = getattr(settings, 'TWITTER_API_KEY', '')
        api_secret          = getattr(settings, 'TWITTER_API_KEY_SECRET', '')
        access_token        = getattr(settings, 'TWITTER_ACCESS_TOKEN', '')
        access_token_secret = getattr(
            settings, 'TWITTER_ACCESS_TOKEN_SECRET', '',
        )

        if not all([api_key, api_secret, access_token, access_token_secret]):
            logger.warning(
                'Twitter credentials are not fully configured. '
                'Tweeting is disabled.'
            )
            return None

        return OAuth1Session(
            api_key,
            client_secret=api_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret,
        )

    def upload_media(self, image_field):
        """Upload an image to X. Returns the media_id string, or None."""
        if not self.oauth or not image_field:
            return None

        try:
            media_type, _ = mimetypes.guess_type(image_field.name)
            if not media_type:
                media_type = 'image/jpeg'

            image_field.open('rb')
            file_data = image_field.read()
            image_field.close()

            response = self.oauth.post(
                'https://api.x.com/2/media/upload',
                data={
                    'media_category': 'tweet_image',
                    'media_type':     media_type,
                },
                files={
                    'media': (image_field.name, file_data, media_type),
                },
            )

            if response.status_code != 200:
                logger.error(
                    'Media upload failed: %s – %s',
                    response.status_code, response.text,
                )
                return None

            return response.json()['data']['id']

        except Exception:
            logger.exception('Unexpected error uploading media to X.')
            return None

    def tweet(self, text, image_field=None):
        """
        Post a tweet with optional image.

        Returns True on success, False on failure.
        """
        if not self.oauth:
            return False

        try:
            payload = {'text': text[:280]}

            media_id = self.upload_media(image_field) if image_field else None
            if media_id:
                payload['media'] = {'media_ids': [media_id]}

            response = self.oauth.post(
                'https://api.x.com/2/tweets',
                json=payload,
            )

            if response.status_code not in (200, 201):
                logger.error(
                    'Tweet failed: %s – %s',
                    response.status_code, response.text,
                )
                return False

            logger.info('Tweet posted successfully.')
            return True

        except Exception:
            logger.exception('Unexpected error posting tweet to X.')
            return False
