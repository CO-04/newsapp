"""
news.forms
==========

Django ModelForms for the NewsApp news module.

Forms
-----
ArticleForm
    Create and edit articles; author is set by the view.
NewsletterForm
    Create and edit newsletters; filters articles to approved only.
PublisherForm
    Create and edit publishers; restricted to editors.
"""

from django import forms

from accounts.forms import BootstrapFormMixin
from .models import Article, Newsletter, Publisher


class ArticleForm(BootstrapFormMixin, forms.ModelForm):
    """Form for creating and editing an Article.

    The publisher field is optional (independent articles have no
    publisher). The image field is optional. The author field is
    excluded and set by the view from the logged-in user.
    """

    class Meta:
        """Form configuration: model, fields, and widget overrides."""

        model   = Article
        fields  = ['title', 'content', 'publisher', 'image']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
        }


class NewsletterForm(BootstrapFormMixin, forms.ModelForm):
    """Form for creating and editing a Newsletter.

    The articles M2M field is rendered as checkboxes so the journalist
    can pick which articles to include. Only approved articles are
    selectable so that unpublished drafts cannot appear in a newsletter.
    The author field is excluded and set by the view.
    """

    def __init__(self, *args, **kwargs):
        """Initialise the form, restricting articles to approved only.

        :param args: Positional arguments passed to the parent form.
        :param kwargs: Keyword arguments passed to the parent form.
        """
        super().__init__(*args, **kwargs)
        self.fields['articles'].queryset = (
            Article.objects
            .filter(approved=True)
            .select_related('author')
            .order_by('-created_at')
        )
        self.fields['articles'].label = 'Articles (approved only)'

    class Meta:
        """Form configuration: model, fields, and widget overrides."""

        model   = Newsletter
        fields  = ['title', 'description', 'articles']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'articles':    forms.CheckboxSelectMultiple(),
        }


class PublisherForm(BootstrapFormMixin, forms.ModelForm):
    """Form for creating and editing a Publisher.

    Only editors can access this form. The logo and website fields
    are optional.
    """

    class Meta:
        """Form configuration: model, fields, and widget overrides."""

        model  = Publisher
        fields = ['name', 'description', 'logo', 'website']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
