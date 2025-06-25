from .permissions import get_user_role_context, get_user_menu_items


def user_role_context(request):
    """
    Add user role and permission context to all templates
    """
    if not request.user.is_authenticated:
        return {}
    
    context = get_user_role_context(request.user)
    context['user_menu_items'] = get_user_menu_items(request.user)
    
    return context