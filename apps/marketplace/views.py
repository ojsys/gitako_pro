from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.utils import timezone
from django.http import JsonResponse
from .models import Product, ProductCategory, Inquiry, Transaction, Review
from apps.farms.models import Farm


class MarketplaceListView(ListView):
    model = Product
    template_name = 'marketplace/list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(
            status=Product.ProductStatus.ACTIVE,
            listing_expiry__gt=timezone.now(),
            quantity_available__gt=0
        ).select_related('seller', 'farm', 'crop', 'category').order_by('-featured', '-created_at')
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(crop__name__icontains=search_query)
            )
        
        # Category filter
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Location filter
        location = self.request.GET.get('location')
        if location:
            queryset = queryset.filter(pickup_location__icontains=location)
        
        # Price range filter
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price_per_unit__gte=min_price)
        if max_price:
            queryset = queryset.filter(price_per_unit__lte=max_price)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ProductCategory.objects.filter(is_active=True)
        context['featured_products'] = Product.objects.filter(
            featured=True,
            status=Product.ProductStatus.ACTIVE,
            listing_expiry__gt=timezone.now()
        )[:6]
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'marketplace/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.select_related('seller', 'farm', 'crop', 'variety', 'category')

    def get_object(self):
        obj = super().get_object()
        # Increment view count
        obj.increment_views()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get seller's other products
        context['seller_products'] = Product.objects.filter(
            seller=self.object.seller,
            status=Product.ProductStatus.ACTIVE
        ).exclude(pk=self.object.pk)[:4]
        
        # Get seller's reviews
        context['seller_reviews'] = Review.objects.filter(
            reviewed_user=self.object.seller
        ).select_related('reviewer')[:5]
        
        # Calculate seller rating
        context['seller_rating'] = Review.objects.filter(
            reviewed_user=self.object.seller
        ).aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
        
        return context


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    template_name = 'marketplace/product_create.html'
    fields = [
        'title', 'description', 'category', 'crop', 'variety',
        'quantity_available', 'unit', 'price_per_unit', 'minimum_order',
        'quality_grade', 'organic_certified', 'certification_details',
        'harvest_date', 'processing_method', 'storage_conditions',
        'pickup_location', 'delivery_available', 'delivery_radius_km',
        'delivery_cost_per_km', 'listing_expiry', 'primary_image'
    ]

    def get_form(self):
        form = super().get_form()
        # Filter crops and categories for better UX
        form.fields['crop'].queryset = form.fields['crop'].queryset.filter(is_active=True)
        
        # Update empty_label for select fields to show "Select" instead of "----"
        form.fields['category'].empty_label = "Select Category"
        form.fields['crop'].empty_label = "Select Crop"
        form.fields['variety'].empty_label = "Select Variety"
        form.fields['quality_grade'].empty_label = "Select Quality Grade"
        form.fields['unit'].empty_label = "Select Unit"
        
        return form

    def form_valid(self, form):
        form.instance.seller = self.request.user
        # Set the farm to the user's first farm (or they should select it)
        user_farm = self.request.user.owned_farms.first()
        if not user_farm:
            messages.error(self.request, 'You must have a farm to list products.')
            return self.form_invalid(form)
        form.instance.farm = user_farm
        messages.success(self.request, 'Product listed successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('marketplace:detail', kwargs={'pk': self.object.pk})


class InquiryCreateView(LoginRequiredMixin, CreateView):
    model = Inquiry
    template_name = 'marketplace/inquiry_create.html'
    fields = [
        'quantity_requested', 'offered_price_per_unit', 'message',
        'buyer_contact', 'delivery_required', 'delivery_address',
        'preferred_delivery_date'
    ]

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, pk=kwargs['product_pk'])
        # Prevent sellers from inquiring about their own products
        if request.user == self.product.seller:
            messages.error(request, "You cannot inquire about your own product.")
            return redirect('marketplace:detail', pk=self.product.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.product = self.product
        form.instance.buyer = self.request.user
        
        # Increment inquiry count
        self.product.increment_inquiries()
        
        messages.success(self.request, 'Inquiry sent successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('marketplace:detail', kwargs={'pk': self.product.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        return context


class MyProductsView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'marketplace/my_products.html'
    context_object_name = 'products'
    paginate_by = 10

    def get_queryset(self):
        return Product.objects.filter(seller=self.request.user).order_by('-created_at')


class MyInquiriesView(LoginRequiredMixin, ListView):
    model = Inquiry
    template_name = 'marketplace/my_inquiries.html'
    context_object_name = 'inquiries'
    paginate_by = 10

    def get_queryset(self):
        tab = self.request.GET.get('tab', 'sent')
        if tab == 'received':
            return Inquiry.objects.filter(
                product__seller=self.request.user
            ).select_related('buyer', 'product').order_by('-created_at')
        else:
            return Inquiry.objects.filter(
                buyer=self.request.user
            ).select_related('product', 'product__seller').order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tab'] = self.request.GET.get('tab', 'sent')
        return context


class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'marketplace/transactions.html'
    context_object_name = 'transactions'
    paginate_by = 10

    def get_queryset(self):
        return Transaction.objects.filter(
            Q(buyer=self.request.user) | Q(seller=self.request.user)
        ).select_related('product', 'buyer', 'seller').order_by('-created_at')


class ProductUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Product
    template_name = 'marketplace/product_edit.html'
    fields = [
        'title', 'description', 'category', 'crop', 'variety',
        'quantity_available', 'unit', 'price_per_unit', 'minimum_order',
        'quality_grade', 'organic_certified', 'certification_details',
        'harvest_date', 'processing_method', 'storage_conditions',
        'pickup_location', 'delivery_available', 'delivery_radius_km',
        'delivery_cost_per_km', 'listing_expiry', 'primary_image', 'status'
    ]

    def test_func(self):
        product = self.get_object()
        return self.request.user == product.seller

    def get_form(self):
        form = super().get_form()
        # Filter crops and categories for better UX
        form.fields['crop'].queryset = form.fields['crop'].queryset.filter(is_active=True)
        
        # Update empty_label for select fields
        form.fields['category'].empty_label = "Select Category"
        form.fields['crop'].empty_label = "Select Crop"
        form.fields['variety'].empty_label = "Select Variety"
        form.fields['quality_grade'].empty_label = "Select Quality Grade"
        form.fields['unit'].empty_label = "Select Unit"
        form.fields['status'].empty_label = "Select Status"
        
        return form

    def form_valid(self, form):
        messages.success(self.request, 'Product updated successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('marketplace:detail', kwargs={'pk': self.object.pk})


class ProductDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Product
    template_name = 'marketplace/product_confirm_delete.html'
    success_url = reverse_lazy('marketplace:my_products')

    def test_func(self):
        product = self.get_object()
        return self.request.user == product.seller

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        product_title = self.object.title
        result = super().delete(request, *args, **kwargs)
        messages.success(request, f'Product "{product_title}" has been deleted successfully.')
        return result


class ProductStatusUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """AJAX view to update product status"""
    
    def test_func(self):
        product = get_object_or_404(Product, pk=self.kwargs['pk'])
        return self.request.user == product.seller
    
    def post(self, request, *args, **kwargs):
        if not self.test_func():
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
            
        product = get_object_or_404(Product, pk=kwargs['pk'])
        new_status = request.POST.get('status')
        
        if new_status in dict(Product.ProductStatus.choices):
            old_status = product.get_status_display()
            product.status = new_status
            product.save()
            
            return JsonResponse({
                'success': True, 
                'message': f'Product status updated from {old_status} to {product.get_status_display()}',
                'new_status': product.get_status_display()
            })
        else:
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)


class ProductDuplicateView(LoginRequiredMixin, UserPassesTestMixin, View):
    """View to duplicate a product"""
    
    def test_func(self):
        product = get_object_or_404(Product, pk=self.kwargs['pk'])
        return self.request.user == product.seller
    
    def post(self, request, *args, **kwargs):
        if not self.test_func():
            messages.error(request, 'Permission denied.')
            return redirect('marketplace:my_products')
            
        original_product = get_object_or_404(Product, pk=kwargs['pk'])
        
        # Create a duplicate
        duplicate = Product.objects.create(
            title=f"{original_product.title} (Copy)",
            description=original_product.description,
            category=original_product.category,
            crop=original_product.crop,
            variety=original_product.variety,
            seller=original_product.seller,
            farm=original_product.farm,
            quantity_available=original_product.quantity_available,
            unit=original_product.unit,
            price_per_unit=original_product.price_per_unit,
            minimum_order=original_product.minimum_order,
            quality_grade=original_product.quality_grade,
            organic_certified=original_product.organic_certified,
            certification_details=original_product.certification_details,
            harvest_date=original_product.harvest_date,
            processing_method=original_product.processing_method,
            storage_conditions=original_product.storage_conditions,
            pickup_location=original_product.pickup_location,
            delivery_available=original_product.delivery_available,
            delivery_radius_km=original_product.delivery_radius_km,
            delivery_cost_per_km=original_product.delivery_cost_per_km,
            status=Product.ProductStatus.DRAFT,  # Set to draft for review
            listing_expiry=timezone.now() + timezone.timedelta(days=30),
            # Note: primary_image is not copied to avoid file conflicts
        )
        
        messages.success(request, f'Product duplicated successfully! New product: "{duplicate.title}"')
        return redirect('marketplace:edit_product', pk=duplicate.pk)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'marketplace/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Seller statistics
        context['seller_stats'] = {
            'total_products': Product.objects.filter(seller=user).count(),
            'active_products': Product.objects.filter(seller=user, status=Product.ProductStatus.ACTIVE).count(),
            'total_sales': Transaction.objects.filter(seller=user).count(),
            'pending_inquiries': Inquiry.objects.filter(product__seller=user, status=Inquiry.InquiryStatus.PENDING).count(),
        }
        
        # Buyer statistics
        context['buyer_stats'] = {
            'total_purchases': Transaction.objects.filter(buyer=user).count(),
            'pending_transactions': Transaction.objects.filter(buyer=user, status__in=['pending', 'paid']).count(),
            'sent_inquiries': Inquiry.objects.filter(buyer=user).count(),
        }
        
        # Recent activities
        context['recent_transactions'] = Transaction.objects.filter(
            Q(buyer=user) | Q(seller=user)
        ).select_related('product')[:5]
        
        context['recent_inquiries'] = Inquiry.objects.filter(
            Q(buyer=user) | Q(product__seller=user)
        ).select_related('product', 'buyer')[:5]
        
        return context