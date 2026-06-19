"""
news.permissions
================

Custom Django REST Framework permission classes for the NewsApp API.

Each class encapsulates a single access-control rule so API views
remain readable and focused on business logic.

Permissions
-----------
IsEditorOrReadOnly
    Read access for everyone; write access for editors only.
IsJournalistOrReadOnly
    Read access for everyone; write access for journalists only.
IsAuthorOrEditor
    Object-level: allow modification by the object's author or editors.
IsApprovedOrAuthorOrEditor
    Object-level: unapproved articles visible only to author or editors.
"""

from rest_framework.permissions import BasePermission


class IsEditorOrReadOnly(BasePermission):
    """Allow read access to everyone; write access to editors only.

    Safe HTTP methods (``GET``, ``HEAD``, ``OPTIONS``) are permitted
    for all users including anonymous. All other methods require the
    requesting user to be authenticated with the ``editor`` role.
    """

    def has_permission(self, request, view):
        """Return ``True`` if the request should be permitted.

        :param request: The incoming HTTP request.
        :type request: HttpRequest
        :param view: The view being accessed.
        :type view: APIView
        :returns: ``True`` for safe methods or authenticated editors.
        :rtype: bool
        """
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return (
            request.user.is_authenticated and request.user.is_editor()
        )


class IsJournalistOrReadOnly(BasePermission):
    """Allow read access to everyone; write access to journalists only.

    Safe HTTP methods (``GET``, ``HEAD``, ``OPTIONS``) are permitted
    for all users including anonymous. All other methods require the
    requesting user to be authenticated with the ``journalist`` role.
    """

    def has_permission(self, request, view):
        """Return ``True`` if the request should be permitted.

        :param request: The incoming HTTP request.
        :type request: HttpRequest
        :param view: The view being accessed.
        :type view: APIView
        :returns: ``True`` for safe methods or authenticated journalists.
        :rtype: bool
        """
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return (
            request.user.is_authenticated and request.user.is_journalist()
        )


class IsAuthorOrEditor(BasePermission):
    """Object-level permission allowing modification by author or editors.

    Safe HTTP methods are always permitted. Write methods require the
    requesting user to be either the object's author or an editor.
    """

    def has_permission(self, request, view):
        """Return ``True`` if the request passes view-level checks.

        :param request: The incoming HTTP request.
        :type request: HttpRequest
        :param view: The view being accessed.
        :type view: APIView
        :returns: ``True`` for safe methods or authenticated users.
        :rtype: bool
        """
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Return ``True`` if the user may act on this specific object.

        :param request: The incoming HTTP request.
        :type request: HttpRequest
        :param view: The view being accessed.
        :type view: APIView
        :param obj: The model instance being accessed.
        :returns: ``True`` for safe methods, editors, or the author.
        :rtype: bool
        """
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        author = getattr(obj, 'author', None)
        return request.user.is_editor() or (author and author == request.user)


class IsApprovedOrAuthorOrEditor(BasePermission):
    """Object-level read permission for articles.

    Approved articles are visible to everyone. Unapproved articles are
    visible only to their author or any editor.
    """

    def has_permission(self, request, view):
        """Always return ``True``; visibility is enforced at object level.

        :param request: The incoming HTTP request.
        :type request: HttpRequest
        :param view: The view being accessed.
        :type view: APIView
        :returns: Always ``True``.
        :rtype: bool
        """
        return True  # object-level check handles visibility

    def has_object_permission(self, request, view, obj):
        """Return ``True`` if the user may view this article.

        :param request: The incoming HTTP request.
        :type request: HttpRequest
        :param view: The view being accessed.
        :type view: APIView
        :param obj: The Article instance being accessed.
        :returns: ``True`` if approved, or user is the author/an editor.
        :rtype: bool
        """
        if getattr(obj, 'approved', True):
            return True
        if not request.user.is_authenticated:
            return False
        return request.user.is_editor() or obj.author == request.user
