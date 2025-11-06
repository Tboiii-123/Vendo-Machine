
from rest_framework import permissions

class IsSeller(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'seller')

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # read-only allowed to anyone (GET) - view-level default may override
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.seller_id == request.user.id
