from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import FarmStaff, Farm


class RolePermissionMixin:
    """
    Mixin to check role-based permissions for farm staff
    """
    
    def get_user_farm_staff(self):
        """Get the FarmStaff object for the current user"""
        if hasattr(self, '_user_farm_staff'):
            return self._user_farm_staff
            
        try:
            self._user_farm_staff = FarmStaff.objects.select_related('farm', 'user').get(
                user=self.request.user,
                is_active=True
            )
            return self._user_farm_staff
        except FarmStaff.DoesNotExist:
            return None
    
    def get_user_assigned_farm(self):
        """Get the farm assigned to the current user"""
        staff = self.get_user_farm_staff()
        return staff.farm if staff else None
    
    def user_has_role(self, roles):
        """Check if user has any of the specified roles"""
        if isinstance(roles, str):
            roles = [roles]
        
        # SuperUsers and Farm owners can do everything
        if self.request.user.is_superuser or self.request.user.role == 'farm_owner':
            return True
            
        # Check staff role
        staff = self.get_user_farm_staff()
        if staff:
            return staff.role in roles
        
        return False
    
    def user_can_manage_farm(self):
        """Check if user can manage farm operations"""
        return self.user_has_role(['manager', 'supervisor']) or self.request.user.role in ['farm_owner', 'admin'] or self.request.user.is_superuser
    
    def user_can_manage_blocks(self):
        """Check if user can manage blocks"""
        return self.user_has_role(['manager', 'supervisor', 'technician']) or self.request.user.role in ['farm_owner', 'admin'] or self.request.user.is_superuser
    
    def user_can_view_financials(self):
        """Check if user can view financial information"""
        return self.user_has_role(['manager']) or self.request.user.role in ['farm_owner', 'admin'] or self.request.user.is_superuser
    
    def user_can_create_staff(self):
        """Check if user can create/manage staff"""
        return self.user_has_role(['manager']) or self.request.user.role in ['farm_owner', 'admin'] or self.request.user.is_superuser
    
    def user_can_field_operations(self):
        """Check if user can perform field operations"""
        return self.user_has_role(['manager', 'supervisor', 'field_worker', 'technician']) or self.request.user.role in ['farm_owner', 'admin'] or self.request.user.is_superuser
    
    def filter_by_user_farm(self, queryset, farm_field='farm'):
        """Filter queryset by user's assigned farm"""
        if self.request.user.is_superuser:
            # SuperUsers see everything
            return queryset
        elif self.request.user.role == 'farm_owner':
            # Farm owners see their own farms
            return queryset.filter(**{f'{farm_field}__owner': self.request.user})
        
        # Staff see only their assigned farm
        assigned_farm = self.get_user_assigned_farm()
        if assigned_farm:
            return queryset.filter(**{farm_field: assigned_farm})
        
        # No farm assigned, return empty queryset
        return queryset.none()


class FarmOwnerRequiredMixin(RolePermissionMixin, LoginRequiredMixin):
    """Require farm owner role or superuser"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not (request.user.is_superuser or request.user.role == 'farm_owner'):
            raise PermissionDenied("Only farm owners or superusers can access this page.")
        
        return super().dispatch(request, *args, **kwargs)


class FarmManagerRequiredMixin(RolePermissionMixin, LoginRequiredMixin):
    """Require farm manager or higher role (including superuser)"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not (request.user.is_superuser or self.user_can_manage_farm()):
            raise PermissionDenied("You don't have permission to access this page.")
        
        return super().dispatch(request, *args, **kwargs)


class FieldWorkerRequiredMixin(RolePermissionMixin, LoginRequiredMixin):
    """Require field worker or higher role (including superuser)"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not (request.user.is_superuser or self.user_can_field_operations()):
            raise PermissionDenied("You don't have permission to access this page.")
        
        return super().dispatch(request, *args, **kwargs)


class StaffRequiredMixin(RolePermissionMixin, LoginRequiredMixin):
    """Require any staff role, farm owner, or superuser"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Check if user is superuser, farm owner or has staff assignment
        if request.user.is_superuser or request.user.role == 'farm_owner' or self.get_user_farm_staff():
            return super().dispatch(request, *args, **kwargs)
        
        raise PermissionDenied("You must be assigned to a farm to access this page.")


def get_user_role_context(user):
    """Get context data about user's role and permissions"""
    context = {
        'user_role': user.role,
        'is_farm_owner': user.role == 'farm_owner',
        'is_admin': user.role == 'admin',
        'is_superuser': user.is_superuser,
        'assigned_farm': None,
        'staff_role': None,
        'can_manage_farm': False,
        'can_manage_blocks': False,
        'can_view_financials': False,
        'can_create_staff': False,
        'can_field_operations': False,
    }
    
    # Get staff information if user is staff
    try:
        staff = FarmStaff.objects.select_related('farm').get(user=user, is_active=True)
        context.update({
            'assigned_farm': staff.farm,
            'staff_role': staff.role,
            'staff_role_display': staff.get_role_display(),
        })
    except FarmStaff.DoesNotExist:
        pass
    
    # Set permissions
    if user.is_superuser or user.role == 'farm_owner' or user.role == 'admin':
        context.update({
            'can_manage_farm': True,
            'can_manage_blocks': True,
            'can_view_financials': True,
            'can_create_staff': True,
            'can_field_operations': True,
        })
    elif context['staff_role']:
        role = context['staff_role']
        context.update({
            'can_manage_farm': role in ['manager', 'supervisor'],
            'can_manage_blocks': role in ['manager', 'supervisor', 'technician'],
            'can_view_financials': role in ['manager'],
            'can_create_staff': role in ['manager'],
            'can_field_operations': role in ['manager', 'supervisor', 'field_worker', 'technician'],
        })
    
    return context


# Role-based menu items
ROLE_MENU_ITEMS = {
    'superuser': [
        {'name': 'Dashboard', 'url': 'dashboard:dashboard', 'icon': 'dashboard'},
        {'name': 'All Farms', 'url': 'farms:list', 'icon': 'agriculture'},
        {'name': 'All Blocks', 'url': 'farms:blocks', 'icon': 'grid_view'},
        {'name': 'All Staff', 'url': 'farms:staff', 'icon': 'people'},
        {'name': 'All Farmers', 'url': 'farms:farmers', 'icon': 'person'},
        {'name': 'Marketplace', 'url': 'marketplace:list', 'icon': 'store'},
        {'name': 'Admin Panel', 'url': '/admin/', 'icon': 'admin_panel_settings'},
        {'name': 'System Reports', 'url': 'reports:dashboard', 'icon': 'assessment'},
        {'name': 'User Management', 'url': '#', 'icon': 'manage_accounts'},
    ],
    'farm_owner': [
        {'name': 'Dashboard', 'url': 'dashboard:dashboard', 'icon': 'dashboard'},
        {'name': 'Farms', 'url': 'farms:list', 'icon': 'agriculture'},
        {'name': 'Blocks', 'url': 'farms:blocks', 'icon': 'grid_view'},
        {'name': 'Staff', 'url': 'farms:staff', 'icon': 'people'},
        {'name': 'Farmers', 'url': 'farms:farmers', 'icon': 'person'},
        {'name': 'Marketplace', 'url': 'marketplace:list', 'icon': 'store'},
        {'name': 'Reports', 'url': 'reports:dashboard', 'icon': 'assessment'},
    ],
    'manager': [
        {'name': 'Dashboard', 'url': 'dashboard:dashboard', 'icon': 'dashboard'},
        {'name': 'My Farm', 'url': 'farms:list', 'icon': 'agriculture'},
        {'name': 'Blocks', 'url': 'farms:blocks', 'icon': 'grid_view'},
        {'name': 'Staff', 'url': 'farms:staff', 'icon': 'people'},
        {'name': 'Farmers', 'url': 'farms:farmers', 'icon': 'person'},
        {'name': 'Tasks', 'url': 'calendar:activities', 'icon': 'task'},
        {'name': 'Reports', 'url': 'reports:dashboard', 'icon': 'assessment'},
    ],
    'supervisor': [
        {'name': 'Dashboard', 'url': 'dashboard:dashboard', 'icon': 'dashboard'},
        {'name': 'My Farm', 'url': 'farms:list', 'icon': 'agriculture'},
        {'name': 'Blocks', 'url': 'farms:blocks', 'icon': 'grid_view'},
        {'name': 'Staff', 'url': 'farms:staff', 'icon': 'people'},
        {'name': 'Tasks', 'url': 'calendar:activities', 'icon': 'task'},
        {'name': 'Field Reports', 'url': '#', 'icon': 'description'},
    ],
    'field_worker': [
        {'name': 'Dashboard', 'url': 'dashboard:dashboard', 'icon': 'dashboard'},
        {'name': 'My Tasks', 'url': 'calendar:activities', 'icon': 'task'},
        {'name': 'Field Inventory', 'url': '#', 'icon': 'inventory'},
        {'name': 'Block Status', 'url': 'farms:blocks', 'icon': 'grid_view'},
        {'name': 'Report Issue', 'url': '#', 'icon': 'report_problem'},
    ],
    'technician': [
        {'name': 'Dashboard', 'url': 'dashboard:dashboard', 'icon': 'dashboard'},
        {'name': 'My Farm', 'url': 'farms:list', 'icon': 'agriculture'},
        {'name': 'Blocks', 'url': 'farms:blocks', 'icon': 'grid_view'},
        {'name': 'Equipment', 'url': '#', 'icon': 'build'},
        {'name': 'Maintenance', 'url': '#', 'icon': 'build_circle'},
        {'name': 'Tasks', 'url': 'calendar:activities', 'icon': 'task'},
    ],
    'security': [
        {'name': 'Dashboard', 'url': 'dashboard:dashboard', 'icon': 'dashboard'},
        {'name': 'Security Log', 'url': '#', 'icon': 'security'},
        {'name': 'Incidents', 'url': '#', 'icon': 'report_problem'},
        {'name': 'Farm Access', 'url': '#', 'icon': 'lock'},
    ],
}


def get_user_menu_items(user):
    """Get menu items based on user role"""
    if user.is_superuser:
        return ROLE_MENU_ITEMS['superuser']
    elif user.role == 'farm_owner':
        return ROLE_MENU_ITEMS['farm_owner']
    
    # Get staff role
    try:
        staff = FarmStaff.objects.get(user=user, is_active=True)
        return ROLE_MENU_ITEMS.get(staff.role, [])
    except FarmStaff.DoesNotExist:
        return []