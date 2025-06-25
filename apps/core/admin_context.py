def admin_dashboard_context(request):
    """
    Context processor for admin dashboard statistics
    """
    context = {
        'total_users': 0,
        'total_farms': 0,
        'total_products': 0,
        'total_transactions': 0,
    }
    
    try:
        from django.contrib.auth import get_user_model
        from apps.farms.models import Farm
        from apps.marketplace.models import Product, Transaction
        
        User = get_user_model()
        
        # Total Users
        context['total_users'] = User.objects.count()
        
        # Active Farms
        context['total_farms'] = Farm.objects.filter(is_active=True).count()
        
        # Marketplace Products
        context['total_products'] = Product.objects.filter(
            status__in=[Product.ProductStatus.ACTIVE, Product.ProductStatus.DRAFT]
        ).count()
        
        # Total Transactions
        context['total_transactions'] = Transaction.objects.count()
        
    except Exception as e:
        # Fallback to zeros if models don't exist yet or during migrations
        pass
    
    return context