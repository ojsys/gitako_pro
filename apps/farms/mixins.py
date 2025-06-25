from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import models


class FarmAccessMixin(LoginRequiredMixin):
    """
    Mixin to provide role-based access control for farm-related views
    """
    
    def dispatch(self, request, *args, **kwargs):
        """
        Check if user has access to farm-related content
        """
        # Call parent dispatch first to handle login requirement
        response = super().dispatch(request, *args, **kwargs)
        
        # Additional access checks can be added here if needed
        user = request.user
        
        # Basic role validation
        if not user.is_authenticated:
            return response
            
        # Allow superusers full access
        if user.is_superuser:
            return response
            
        # Check if user has a valid role for farm access
        valid_roles = ['farm_owner', 'farm_manager', 'staff']
        if not hasattr(user, 'role') or user.role not in valid_roles:
            raise PermissionDenied("You don't have permission to access farm data.")
            
        return response


class FarmOwnerRequiredMixin(FarmAccessMixin):
    """
    Mixin that restricts access to farm owners and superusers only
    """
    
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        
        user = request.user
        if not user.is_superuser and user.role != 'farm_owner':
            raise PermissionDenied("Only farm owners can access this page.")
            
        return response


class FarmManagerRequiredMixin(FarmAccessMixin):
    """
    Mixin that restricts access to farm managers and above (farm owners, superusers)
    """
    
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        
        user = request.user
        allowed_roles = ['farm_owner', 'farm_manager']
        if not user.is_superuser and user.role not in allowed_roles:
            raise PermissionDenied("You need farm manager permissions or higher to access this page.")
            
        return response