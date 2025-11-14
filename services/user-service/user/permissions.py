from rest_framework import permissions


class IsCustomer(permissions.BasePermission):
    """Check if user is a customer."""
    def has_permission(self, request, view):
        return request.user.is_customer


class IsAgent(permissions.BasePermission):
    """Check if user is an approved agent."""
    def has_permission(self, request, view):
        return request.user.is_agent and request.user.is_approved


class IsAdmin(permissions.BasePermission):
    """Check if user is an admin."""
    def has_permission(self, request, view):
        return request.user.is_admin


class IsAdminOrAgent(permissions.BasePermission):
    """Check if user is admin or approved agent."""
    def has_permission(self, request, view):
        return request.user.is_admin or (request.user.is_agent and request.user.is_approved)
