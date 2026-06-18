"""
Custom DRF permission classes for the news app.

Each class encapsulates a single access-control rule so views stay readable.
"""

from rest_framework.permissions import BasePermission


class IsEditorOrReadOnly(BasePermission):
    """
    Allow read access to everyone.
    Allow write access only to users with the 'editor' role.
    """

    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_authenticated and request.user.is_editor()


class IsJournalistOrReadOnly(BasePermission):
    """
    Allow read access to everyone.
    Allow write access only to users with the 'journalist' role.
    """

    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_authenticated and request.user.is_journalist()


class IsAuthorOrEditor(BasePermission):
    """
    Object-level permission.

    Allow modification if the requesting user is:
    - the author of the object, or
    - an editor.

    Safe methods are always permitted.
    """

    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        author = getattr(obj, 'author', None)
        return request.user.is_editor() or (author and author == request.user)


class IsApprovedOrAuthorOrEditor(BasePermission):
    """
    Object-level read permission for articles.

    - Approved articles are visible to everyone.
    - Unapproved articles are visible only to their author or any editor.
    """

    def has_permission(self, request, view):
        return True  # object-level check handles visibility

    def has_object_permission(self, request, view, obj):
        if getattr(obj, 'approved', True):
            return True
        if not request.user.is_authenticated:
            return False
        return request.user.is_editor() or obj.author == request.user
