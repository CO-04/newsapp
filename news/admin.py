from django.contrib import admin

from .models import Article, Newsletter, Publisher


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    """Admin configuration for Publisher."""

    list_display  = ('name', 'website', 'created_at')
    search_fields = ('name',)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Admin configuration for Article, with a bulk-approve action."""

    list_display   = (
        'title', 'author', 'publisher',
        'submitted', 'approved', 'created_at',
    )
    list_filter    = ('approved', 'submitted', 'publisher')
    search_fields  = ('title', 'author__username')
    actions        = ['approve_selected']

    def approve_selected(self, request, queryset):
        """Approve all selected unapproved articles via the admin action."""
        for article in queryset.filter(approved=False):
            article._just_approved = True
            article.approved = True
            article.save()
    approve_selected.short_description = 'Approve selected articles'


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    """Admin configuration for Newsletter."""

    list_display     = ('title', 'author', 'created_at')
    filter_horizontal = ('articles',)
