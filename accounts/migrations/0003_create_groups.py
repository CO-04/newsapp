"""
Data migration: create Reader, Journalist, and Editor groups with their
corresponding model-level permissions.

Groups and permissions
----------------------
Reader     : view_article, view_newsletter
Journalist : add_article, view_article, change_article, delete_article,
             add_newsletter, view_newsletter, change_newsletter, delete_newsletter
Editor     : view_article, change_article, delete_article,
             view_newsletter, change_newsletter, delete_newsletter
"""

from django.db import migrations


GROUP_PERMISSIONS = {
    'Reader': [
        ('news', 'article',    'view_article'),
        ('news', 'newsletter', 'view_newsletter'),
    ],
    'Journalist': [
        ('news', 'article',    'add_article'),
        ('news', 'article',    'view_article'),
        ('news', 'article',    'change_article'),
        ('news', 'article',    'delete_article'),
        ('news', 'newsletter', 'add_newsletter'),
        ('news', 'newsletter', 'view_newsletter'),
        ('news', 'newsletter', 'change_newsletter'),
        ('news', 'newsletter', 'delete_newsletter'),
    ],
    'Editor': [
        ('news', 'article',    'view_article'),
        ('news', 'article',    'change_article'),
        ('news', 'article',    'delete_article'),
        ('news', 'newsletter', 'view_newsletter'),
        ('news', 'newsletter', 'change_newsletter'),
        ('news', 'newsletter', 'delete_newsletter'),
    ],
}


def create_groups(apps, schema_editor):
    """Create the three role groups and assign their permissions."""
    Group      = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    for group_name, perms in GROUP_PERMISSIONS.items():
        group, _ = Group.objects.get_or_create(name=group_name)
        for app_label, model_name, codename in perms:
            try:
                perm = Permission.objects.get(
                    codename=codename,
                    content_type__app_label=app_label,
                    content_type__model=model_name,
                )
                group.permissions.add(perm)
            except Permission.DoesNotExist:
                pass  # Permission not yet available (e.g. during fresh test runs)


def delete_groups(apps, schema_editor):
    """Remove the three role groups (reverse operation)."""
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=GROUP_PERMISSIONS.keys()).delete()


class Migration(migrations.Migration):
    """Data migration to seed Reader, Journalist, and Editor auth groups."""

    dependencies = [
        ('accounts', '0002_initial'),
        ('news', '0001_initial'),       # permissions exist only after news models are created
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(create_groups, reverse_code=delete_groups),
    ]
