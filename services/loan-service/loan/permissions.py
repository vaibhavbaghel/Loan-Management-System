from rest_framework import permissions


class IsCustomer(permissions.BasePermission):
    """Check if user is a customer."""
    def has_permission(self, request, view):
        return request.user.get('is_customer', False)


class IsAgent(permissions.BasePermission):
    """Check if user is an approved agent."""
    def has_permission(self, request, view):
        return request.user.get('is_agent', False) and request.user.get('is_approved', False)


class IsAdmin(permissions.BasePermission):
    """Check if user is an admin."""
    def has_permission(self, request, view):
        return request.user.get('is_admin', False)


class IsAdminOrAgent(permissions.BasePermission):
    """Check if user is admin or approved agent."""
    def has_permission(self, request, view):
        is_admin = request.user.get('is_admin', False)
        is_agent = request.user.get('is_agent', False)
        is_approved = request.user.get('is_approved', False)
        return is_admin or (is_agent and is_approved)
