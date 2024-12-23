from rest_framework import permissions
from django.core.exceptions import ObjectDoesNotExist

class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to access it.
    """
    def has_permission(self, request, view):
        print("has_permission called")  # Debug
        return True  # Allow initial request, object level check happens later

    def has_object_permission(self, request, view, obj):
        print("has_object_permission called")  # Debug
        print("Request user:", request.user)  # Debug
        try:
            print("Object book user:", obj.book.user)  # Debug
        except ObjectDoesNotExist:
            print("Failed to get book user")  # Debug
            return False
            
        return obj.book.user == request.user