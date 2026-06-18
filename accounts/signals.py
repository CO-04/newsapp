from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CustomUser

# Map each role value to the corresponding auth Group name.
ROLE_TO_GROUP = {
    'reader':     'Reader',
    'journalist': 'Journalist',
    'editor':     'Editor',
}


@receiver(post_save, sender=CustomUser)
def assign_group_on_save(sender, instance, **kwargs):
    """
    Assign the user to their role group on every save.

    Removes the user from all other role groups first so that a role change
    is immediately reflected in permissions without requiring a manual admin
    action.
    """
    target_name = ROLE_TO_GROUP.get(instance.role)
    if not target_name:
        return

    target_group, _ = Group.objects.get_or_create(name=target_name)

    # Remove from any previously held role groups
    other_names = [
        name for name in ROLE_TO_GROUP.values()
        if name != target_name
    ]
    instance.groups.remove(*Group.objects.filter(name__in=other_names))

    instance.groups.add(target_group)
