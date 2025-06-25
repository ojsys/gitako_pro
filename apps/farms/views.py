from django.views.generic import ListView, CreateView, UpdateView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Sum, Count, Q, Avg, F
from django.utils import timezone
from django.shortcuts import redirect
from .models import Farm, Block, FarmStaff, FarmerRecord, Crop, CropVariety
from .forms import FarmForm, BlockForm, BlockUpdateForm, FarmStaffForm, FarmerRecordForm, StaffCreationForm
from .permissions import (
    RolePermissionMixin, FarmOwnerRequiredMixin, FarmManagerRequiredMixin, 
    FieldWorkerRequiredMixin, StaffRequiredMixin
)


class FarmListView(StaffRequiredMixin, ListView):
    model = Farm
    template_name = 'farms/list.html'
    context_object_name = 'farms'
    paginate_by = 10

    def get_queryset(self):
        queryset = Farm.objects.filter(is_active=True)
        
        if self.request.user.is_superuser:
            # SuperUsers see all farms
            return queryset.order_by('-created_at')
        elif self.request.user.role == 'farm_owner':
            # Farm owners see their own farms
            return queryset.filter(owner=self.request.user).order_by('-created_at')
        else:
            # Staff see only their assigned farm
            assigned_farm = self.get_user_assigned_farm()
            if assigned_farm:
                return queryset.filter(id=assigned_farm.id).order_by('-created_at')
            return queryset.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get farms based on user role
        if self.request.user.is_superuser:
            user_farms = Farm.objects.filter(is_active=True)
        elif self.request.user.role == 'farm_owner':
            user_farms = Farm.objects.filter(owner=self.request.user, is_active=True)
        else:
            # Staff - get their assigned farm
            assigned_farm = self.get_user_assigned_farm()
            if assigned_farm:
                user_farms = Farm.objects.filter(id=assigned_farm.id, is_active=True)
            else:
                user_farms = Farm.objects.none()
        
        # Get summary statistics
        context['total_farms'] = user_farms.count()
        context['total_area'] = user_farms.aggregate(total=Sum('total_area'))['total'] or 0
        
        # Get blocks based on user role
        if self.request.user.is_superuser:
            user_blocks = Block.objects.filter(is_active=True)
        elif self.request.user.role == 'farm_owner':
            user_blocks = Block.objects.filter(farm__owner=self.request.user, is_active=True)
        else:
            # Staff - get blocks from their assigned farm
            assigned_farm = self.get_user_assigned_farm()
            if assigned_farm:
                user_blocks = Block.objects.filter(farm=assigned_farm, is_active=True)
            else:
                user_blocks = Block.objects.none()
        
        context['total_blocks'] = user_blocks.count()
        context['total_allocated_area'] = user_blocks.aggregate(total=Sum('size'))['total'] or 0
        
        # Get staff count based on user role
        if self.request.user.is_superuser:
            context['total_staff'] = FarmStaff.objects.filter(is_active=True).count()
        elif self.request.user.role == 'farm_owner':
            context['total_staff'] = FarmStaff.objects.filter(farm__owner=self.request.user, is_active=True).count()
        else:
            # Staff - get staff from their assigned farm
            assigned_farm = self.get_user_assigned_farm()
            if assigned_farm:
                context['total_staff'] = FarmStaff.objects.filter(farm=assigned_farm, is_active=True).count()
            else:
                context['total_staff'] = 0
        
        # Get user role information
        context['user_role'] = self.request.user.role
        context['is_superuser'] = self.request.user.is_superuser
        context['is_farm_manager'] = self.user_can_manage_farm()
        context['assigned_farm'] = self.get_user_assigned_farm()
        
        # Recent activities (if calendar app exists)
        try:
            from apps.calendar.models import Activity
            if self.request.user.is_superuser:
                context['recent_activities'] = Activity.objects.filter(
                    status__in=['pending', 'in_progress']
                ).select_related('calendar', 'calendar__farm').order_by('scheduled_date')[:5]
            elif self.request.user.role == 'farm_owner':
                context['recent_activities'] = Activity.objects.filter(
                    calendar__farm__owner=self.request.user,
                    status__in=['pending', 'in_progress']
                ).select_related('calendar', 'calendar__farm').order_by('scheduled_date')[:5]
            else:
                # Staff - get activities from their assigned farm
                assigned_farm = self.get_user_assigned_farm()
                if assigned_farm:
                    context['recent_activities'] = Activity.objects.filter(
                        calendar__farm=assigned_farm,
                        status__in=['pending', 'in_progress']
                    ).select_related('calendar', 'calendar__farm').order_by('scheduled_date')[:5]
                else:
                    context['recent_activities'] = []
        except ImportError:
            context['recent_activities'] = []
        
        return context


class FarmDetailView(LoginRequiredMixin, DetailView):
    model = Farm
    template_name = 'farms/detail.html'
    context_object_name = 'farm'

    def get_queryset(self):
        return Farm.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['blocks'] = self.object.blocks.filter(is_active=True).order_by('name')
        context['staff'] = self.object.staff.filter(is_active=True).select_related('user')
        return context


class BlockListView(LoginRequiredMixin, ListView):
    model = Block
    template_name = 'farms/blocks.html'
    context_object_name = 'blocks'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        
        # Get base queryset with role-based filtering
        if user.is_superuser or user.role == 'admin':
            # Superuser and admin see all blocks
            queryset = Block.objects.filter(is_active=True)
        elif user.role == 'farm_owner':
            # Farm owner sees blocks from their own farms
            queryset = Block.objects.filter(farm__owner=user, is_active=True)
        elif user.role in ['farm_manager', 'staff', 'farmer']:
            # Farm manager, staff, and farmers see blocks from farms they're associated with
            
            # Get farms where user is owner or staff member
            owned_farm_ids = Farm.objects.filter(owner=user, is_active=True).values_list('id', flat=True)
            managed_farm_ids = FarmStaff.objects.filter(
                user=user, is_active=True
            ).values_list('farm_id', flat=True)
            
            # Combine farm IDs
            farm_ids = list(owned_farm_ids) + list(managed_farm_ids)
            queryset = Block.objects.filter(farm__id__in=farm_ids, is_active=True)
        else:
            # Default: no blocks
            queryset = Block.objects.none()
        
        queryset = queryset.select_related('farm', 'crop', 'variety', 'block_manager').order_by('farm__name', 'name')
        
        # Farm filter
        farm_id = self.request.GET.get('farm')
        if farm_id:
            queryset = queryset.filter(farm_id=farm_id)
        
        # Crop filter
        crop_id = self.request.GET.get('crop')
        if crop_id:
            queryset = queryset.filter(crop_id=crop_id)
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(farm__name__icontains=search_query) |
                Q(crop__name__icontains=search_query)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get filter options based on user role
        if user.is_superuser or user.role == 'admin':
            # Superuser and admin see all farms
            context['farms'] = Farm.objects.filter(is_active=True).order_by('name')
            user_blocks = Block.objects.filter(is_active=True)
        elif user.role == 'farm_owner':
            # Farm owner sees their own farms
            context['farms'] = Farm.objects.filter(owner=user, is_active=True).order_by('name')
            user_blocks = Block.objects.filter(farm__owner=user, is_active=True)
        elif user.role in ['farm_manager', 'staff', 'farmer']:
            # Farm manager, staff, and farmers see farms they're associated with
            
            # Get farms where user is owner or staff member
            owned_farm_ids = Farm.objects.filter(owner=user, is_active=True).values_list('id', flat=True)
            managed_farm_ids = FarmStaff.objects.filter(
                user=user, is_active=True
            ).values_list('farm_id', flat=True)
            
            # Combine farm IDs
            farm_ids = list(owned_farm_ids) + list(managed_farm_ids)
            context['farms'] = Farm.objects.filter(id__in=farm_ids, is_active=True).order_by('name')
            user_blocks = Block.objects.filter(farm__id__in=farm_ids, is_active=True)
        else:
            # Default: no farms or blocks
            context['farms'] = Farm.objects.none()
            user_blocks = Block.objects.none()
        
        context['crops'] = Crop.objects.filter(is_active=True).order_by('name')
        
        # Get summary statistics
        context['total_blocks'] = user_blocks.count()
        context['total_block_area'] = user_blocks.aggregate(total=Sum('size'))['total'] or 0
        context['planted_blocks'] = user_blocks.filter(planting_date__isnull=False).count()
        context['harvested_blocks'] = user_blocks.filter(actual_harvest_date__isnull=False).count()
        
        # Block status distribution
        context['growing_blocks'] = user_blocks.filter(
            planting_date__isnull=False,
            actual_harvest_date__isnull=True
        ).count()
        
        return context


class StaffListView(FarmManagerRequiredMixin, ListView):
    model = FarmStaff
    template_name = 'farms/staff.html'
    context_object_name = 'staff_members'
    paginate_by = 20

    def get_queryset(self):
        queryset = self.filter_by_user_farm(
            FarmStaff.objects.filter(is_active=True),
            farm_field='farm'
        ).select_related('farm', 'user').order_by('farm__name', 'user__first_name')
        
        # Farm filter
        farm_id = self.request.GET.get('farm')
        if farm_id:
            queryset = queryset.filter(farm_id=farm_id)
        
        # Role filter
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter options
        context['farms'] = Farm.objects.filter(owner=self.request.user, is_active=True).order_by('name')
        context['roles'] = FarmStaff.StaffRole.choices
        
        # Get summary statistics
        user_staff = FarmStaff.objects.filter(farm__owner=self.request.user, is_active=True)
        context['total_staff'] = user_staff.count()
        context['staff_by_role'] = user_staff.values('role').annotate(count=Count('id')).order_by('role')
        
        return context


class FarmerListView(StaffRequiredMixin, ListView):
    model = FarmerRecord
    template_name = 'farms/farmers.html'
    context_object_name = 'farmers'
    paginate_by = 20

    def get_queryset(self):
        queryset = self.filter_by_user_farm(
            FarmerRecord.objects.filter(is_active=True),
            farm_field='farm'
        ).select_related('farm', 'block').prefetch_related('crops_grown').order_by('-season_year', 'farmer_name')
        
        # Farm filter
        farm_id = self.request.GET.get('farm')
        if farm_id:
            queryset = queryset.filter(farm_id=farm_id)
        
        # Block filter
        block_id = self.request.GET.get('block')
        if block_id:
            queryset = queryset.filter(block_id=block_id)
        
        # Season filter
        season_year = self.request.GET.get('season_year')
        if season_year:
            queryset = queryset.filter(season_year=season_year)
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(farmer_name__icontains=search_query) |
                Q(farmer_email__icontains=search_query) |
                Q(location__icontains=search_query)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter options based on user role
        if self.request.user.is_superuser:
            context['farms'] = Farm.objects.filter(is_active=True).order_by('name')
            user_farmers = FarmerRecord.objects.filter(is_active=True)
        elif self.request.user.role == 'farm_owner':
            context['farms'] = Farm.objects.filter(owner=self.request.user, is_active=True).order_by('name')
            user_farmers = FarmerRecord.objects.filter(farm__owner=self.request.user, is_active=True)
        else:
            # Staff - get their assigned farm
            assigned_farm = self.get_user_assigned_farm()
            if assigned_farm:
                context['farms'] = Farm.objects.filter(id=assigned_farm.id, is_active=True).order_by('name')
                user_farmers = FarmerRecord.objects.filter(farm=assigned_farm, is_active=True)
                # Get blocks for the assigned farm
                context['blocks'] = Block.objects.filter(farm=assigned_farm, is_active=True).order_by('name')
            else:
                context['farms'] = Farm.objects.none()
                user_farmers = FarmerRecord.objects.none()
                context['blocks'] = Block.objects.none()
        
        # Get blocks for farm filtering (if not staff)
        if self.request.user.is_superuser or self.request.user.role == 'farm_owner':
            if self.request.user.is_superuser:
                context['blocks'] = Block.objects.filter(is_active=True).order_by('farm__name', 'name')
            else:
                context['blocks'] = Block.objects.filter(farm__owner=self.request.user, is_active=True).order_by('farm__name', 'name')
        
        context['season_years'] = user_farmers.values_list('season_year', flat=True).distinct().order_by('-season_year')
        
        # Get summary statistics
        context['total_farmers'] = user_farmers.count()
        context['total_allocated_hectares'] = user_farmers.aggregate(total=Sum('allocated_hectares'))['total'] or 0
        context['average_yield_efficiency'] = user_farmers.filter(
            expected_yield__isnull=False,
            actual_yield__isnull=False
        ).aggregate(
            avg=Avg(F('actual_yield') / F('expected_yield') * 100)
        )['avg'] or 0
        
        # Role-based context
        context['is_farm_manager'] = self.user_can_manage_farm()
        context['can_create_farmers'] = self.user_can_manage_farm()
        context['assigned_farm'] = self.get_user_assigned_farm()
        
        return context


class FarmCreateView(LoginRequiredMixin, CreateView):
    model = Farm
    form_class = FarmForm
    template_name = 'farms/create.html'
    success_url = reverse_lazy('farms:list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Farm created successfully!')
        return super().form_valid(form)


class FarmUpdateView(LoginRequiredMixin, UpdateView):
    model = Farm
    form_class = FarmForm
    template_name = 'farms/update.html'
    success_url = reverse_lazy('farms:list')

    def get_queryset(self):
        return Farm.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Farm updated successfully!')
        return super().form_valid(form)


class BlockCreateView(LoginRequiredMixin, CreateView):
    model = Block
    form_class = BlockForm
    template_name = 'farms/block_create.html'
    success_url = reverse_lazy('farms:blocks')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Block created successfully!')
        return super().form_valid(form)


class BlockDetailView(LoginRequiredMixin, DetailView):
    model = Block
    template_name = 'farms/block_detail.html'
    context_object_name = 'block'

    def get(self, request, *args, **kwargs):
        """
        Custom get method to completely control the flow
        """
        from django.shortcuts import get_object_or_404
        from django.http import Http404
        
        # Get the block and check access based on user role
        try:
            user = request.user
            
            if user.is_superuser or user.role == 'admin':
                # Superuser and admin can access all blocks
                block = get_object_or_404(
                    Block.objects.select_related('farm', 'crop', 'variety', 'block_manager'),
                    pk=kwargs['pk']
                )
            elif user.role == 'farm_owner':
                # Farm owner can access blocks from their own farms
                block = get_object_or_404(
                    Block.objects.select_related('farm', 'crop', 'variety', 'block_manager'),
                    pk=kwargs['pk'],
                    farm__owner=user
                )
            elif user.role in ['farm_manager', 'staff', 'farmer']:
                # Farm manager, staff, and farmers can access blocks from farms they're associated with
                
                # Get farms where user is owner or staff member
                owned_farm_ids = Farm.objects.filter(owner=user, is_active=True).values_list('id', flat=True)
                managed_farm_ids = FarmStaff.objects.filter(
                    user=user, is_active=True
                ).values_list('farm_id', flat=True)
                
                # Combine farm IDs
                farm_ids = list(owned_farm_ids) + list(managed_farm_ids)
                block = get_object_or_404(
                    Block.objects.select_related('farm', 'crop', 'variety', 'block_manager'),
                    pk=kwargs['pk'],
                    farm__id__in=farm_ids
                )
            else:
                # Default: no access
                raise Http404("Block not found or you don't have permission to view it.")
        except:
            raise Http404("Block not found or you don't have permission to view it.")
        
        # Set up context manually - use farm_block to avoid conflicts with Django's {% block %} template tag
        context = {
            'farm_block': block,
            'object': block,  # For compatibility with DetailView
        }
        
        return self.render_to_response(context)

    


class BlockUpdateView(LoginRequiredMixin, UpdateView):
    model = Block
    form_class = BlockUpdateForm
    template_name = 'farms/block_update.html'
    success_url = reverse_lazy('farms:blocks')

    def get(self, request, *args, **kwargs):
        """
        Custom get method to control context like BlockDetailView
        """
        from django.shortcuts import get_object_or_404
        from django.http import Http404
        
        # Get the block and check access based on user role
        try:
            user = request.user
            
            if user.is_superuser or user.role == 'admin':
                # Superuser and admin can access all blocks
                block = get_object_or_404(
                    Block.objects.select_related('farm', 'crop', 'variety', 'block_manager'),
                    pk=kwargs['pk']
                )
            elif user.role == 'farm_owner':
                # Farm owner can access blocks from their own farms
                block = get_object_or_404(
                    Block.objects.select_related('farm', 'crop', 'variety', 'block_manager'),
                    pk=kwargs['pk'],
                    farm__owner=user
                )
            elif user.role in ['farm_manager', 'staff', 'farmer']:
                # Farm manager, staff, and farmers can access blocks from farms they're associated with
                
                # Get farms where user is owner or staff member
                owned_farm_ids = Farm.objects.filter(owner=user, is_active=True).values_list('id', flat=True)
                managed_farm_ids = FarmStaff.objects.filter(
                    user=user, is_active=True
                ).values_list('farm_id', flat=True)
                
                # Combine farm IDs
                farm_ids = list(owned_farm_ids) + list(managed_farm_ids)
                block = get_object_or_404(
                    Block.objects.select_related('farm', 'crop', 'variety', 'block_manager'),
                    pk=kwargs['pk'],
                    farm__id__in=farm_ids
                )
            else:
                # Default: no access
                raise Http404("Block not found or you don't have permission to edit it.")
        except:
            raise Http404("Block not found or you don't have permission to edit it.")
        
        # Get the form
        form = self.form_class(instance=block, user=request.user)
        
        # Set up context manually - use farm_block to avoid conflicts
        context = {
            'farm_block': block,
            'object': block,
            'form': form,
        }
        
        return self.render_to_response(context)
    
    def post(self, request, *args, **kwargs):
        """
        Custom post method for form handling
        """
        from django.shortcuts import get_object_or_404
        from django.http import Http404
        from django.contrib import messages
        
        # Get the block and check access based on user role
        try:
            user = request.user
            
            if user.is_superuser or user.role == 'admin':
                # Superuser and admin can access all blocks
                block = get_object_or_404(
                    Block.objects.select_related('farm'),
                    pk=kwargs['pk']
                )
            elif user.role == 'farm_owner':
                # Farm owner can access blocks from their own farms
                block = get_object_or_404(
                    Block.objects.select_related('farm'),
                    pk=kwargs['pk'],
                    farm__owner=user
                )
            elif user.role in ['farm_manager', 'staff', 'farmer']:
                # Farm manager, staff, and farmers can access blocks from farms they're associated with
                
                # Get farms where user is owner or staff member
                owned_farm_ids = Farm.objects.filter(owner=user, is_active=True).values_list('id', flat=True)
                managed_farm_ids = FarmStaff.objects.filter(
                    user=user, is_active=True
                ).values_list('farm_id', flat=True)
                
                # Combine farm IDs
                farm_ids = list(owned_farm_ids) + list(managed_farm_ids)
                block = get_object_or_404(
                    Block.objects.select_related('farm'),
                    pk=kwargs['pk'],
                    farm__id__in=farm_ids
                )
            else:
                # Default: no access
                raise Http404("Block not found or you don't have permission to edit it.")
        except:
            raise Http404("Block not found or you don't have permission to edit it.")
        
        # Process the form
        form = self.form_class(request.POST, instance=block, user=request.user)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Block updated successfully!')
            return self.get_success_response()
        
        # If form is invalid, re-render with errors
        context = {
            'farm_block': block,
            'object': block,
            'form': form,
        }
        
        return self.render_to_response(context)
    
    def get_success_response(self):
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect(self.success_url)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Block updated successfully!')
        return super().form_valid(form)


class StaffDetailView(LoginRequiredMixin, DetailView):
    model = FarmStaff
    template_name = 'farms/staff_detail.html'
    context_object_name = 'staff_member'

    def get_queryset(self):
        return FarmStaff.objects.filter(
            farm__owner=self.request.user
        ).select_related('farm', 'user')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any additional context data if needed
        return context


class StaffUpdateView(LoginRequiredMixin, UpdateView):
    model = FarmStaff
    form_class = FarmStaffForm
    template_name = 'farms/staff_update.html'
    success_url = reverse_lazy('farms:staff')

    def get_queryset(self):
        return FarmStaff.objects.filter(farm__owner=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Staff member updated successfully!')
        return super().form_valid(form)


class StaffCreateView(FarmManagerRequiredMixin, CreateView):
    model = FarmStaff
    form_class = StaffCreationForm
    template_name = 'farms/staff_create.html'
    success_url = reverse_lazy('farms:staff')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        from apps.accounts.models import User as CustomUser
        from django.contrib.auth.hashers import make_password
        
        # Create the user account first
        user = CustomUser.objects.create(
            username=form.cleaned_data['username'],
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            email=form.cleaned_data['email'],
            phone_number=form.cleaned_data.get('phone_number', ''),
            address=form.cleaned_data.get('address', ''),
            city=form.cleaned_data.get('city', ''),
            state=form.cleaned_data.get('state', ''),
            role='staff',  # Set role as staff
            password=make_password(form.cleaned_data['password1']),
            is_verified=True  # Auto-verify staff accounts
        )
        
        # Create the staff record
        form.instance.user = user
        response = super().form_valid(form)
        
        messages.success(
            self.request, 
            f'Staff member {user.full_name} has been created successfully! '
            f'Login credentials: Username: {user.username}, Password: {form.cleaned_data["password1"]}'
        )
        return response


class FarmerCreateView(FarmManagerRequiredMixin, CreateView):
    model = FarmerRecord
    form_class = FarmerRecordForm
    template_name = 'farms/farmer_create.html'
    success_url = reverse_lazy('farms:farmers')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Farmer record created successfully!')
        return super().form_valid(form)


class FarmerBulkUploadView(FarmManagerRequiredMixin, TemplateView):
    template_name = 'farms/farmer_bulk_upload.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get available farms and blocks based on user role
        if self.request.user.is_superuser:
            context['farms'] = Farm.objects.filter(is_active=True).order_by('name')
            context['blocks'] = Block.objects.filter(is_active=True).order_by('farm__name', 'name')
        elif self.request.user.role == 'farm_owner':
            context['farms'] = Farm.objects.filter(owner=self.request.user, is_active=True).order_by('name')
            context['blocks'] = Block.objects.filter(farm__owner=self.request.user, is_active=True).order_by('farm__name', 'name')
        else:
            # Staff - get their assigned farm
            assigned_farm = self.get_user_assigned_farm()
            if assigned_farm:
                context['farms'] = Farm.objects.filter(id=assigned_farm.id, is_active=True)
                context['blocks'] = Block.objects.filter(farm=assigned_farm, is_active=True).order_by('name')
            else:
                context['farms'] = Farm.objects.none()
                context['blocks'] = Block.objects.none()
        
        context['assigned_farm'] = self.get_user_assigned_farm()
        context['is_farm_manager'] = self.user_can_manage_farm()
        
        return context
    
    def post(self, request, *args, **kwargs):
        import csv
        import io
        from decimal import Decimal
        
        if 'excel_file' not in request.FILES:
            messages.error(request, 'Please select a file to upload.')
            return self.get(request, *args, **kwargs)
        
        uploaded_file = request.FILES['excel_file']
        block_id = request.POST.get('block_id')
        
        if not block_id:
            messages.error(request, 'Please select a block to assign farmers to.')
            return self.get(request, *args, **kwargs)
        
        try:
            # Get the block and verify access
            if self.request.user.is_superuser:
                block = Block.objects.get(id=block_id, is_active=True)
            elif self.request.user.role == 'farm_owner':
                block = Block.objects.get(id=block_id, farm__owner=self.request.user, is_active=True)
            else:
                # Staff - verify it's their assigned farm's block
                assigned_farm = self.get_user_assigned_farm()
                if not assigned_farm:
                    messages.error(request, 'You are not assigned to any farm.')
                    return self.get(request, *args, **kwargs)
                block = Block.objects.get(id=block_id, farm=assigned_farm, is_active=True)
            
        except Block.DoesNotExist:
            messages.error(request, 'Invalid block selected.')
            return self.get(request, *args, **kwargs)
        
        try:
            # Read CSV file (for now, we'll support CSV instead of Excel)
            file_data = uploaded_file.read().decode('utf-8')
            io_string = io.StringIO(file_data)
            reader = csv.DictReader(io_string)
            
            # Validate required columns
            required_columns = ['farmer_name', 'allocated_hectares', 'season_year']
            fieldnames = reader.fieldnames or []
            missing_columns = [col for col in required_columns if col not in fieldnames]
            
            if missing_columns:
                messages.error(request, f'Missing required columns: {", ".join(missing_columns)}')
                return self.get(request, *args, **kwargs)
            
            # Process farmers
            created_count = 0
            errors = []
            
            for index, row in enumerate(reader, start=2):
                try:
                    # Validate data
                    if not row.get('farmer_name', '').strip():
                        errors.append(f'Row {index}: Farmer name is required')
                        continue
                    
                    try:
                        allocated_hectares = float(row.get('allocated_hectares', 0))
                        if allocated_hectares <= 0:
                            raise ValueError("Must be greater than 0")
                    except (ValueError, TypeError):
                        errors.append(f'Row {index}: Valid allocated hectares is required')
                        continue
                    
                    try:
                        season_year = int(row.get('season_year', 0))
                        if season_year <= 0:
                            raise ValueError("Must be a valid year")
                    except (ValueError, TypeError):
                        errors.append(f'Row {index}: Valid season year is required')
                        continue
                    
                    # Parse additional numeric fields
                    farming_experience = None
                    if row.get('farming_experience'):
                        try:
                            farming_experience = int(float(row.get('farming_experience', 0)))
                        except (ValueError, TypeError):
                            pass
                    
                    # Parse registration date
                    registration_date = None
                    if row.get('registration_date'):
                        try:
                            from datetime import datetime
                            registration_date = datetime.strptime(row.get('registration_date', ''), '%Y-%m-%d').date()
                        except (ValueError, TypeError):
                            pass
                    
                    # Create farmer record
                    farmer_record = FarmerRecord.objects.create(
                        farm=block.farm,
                        block=block,
                        farmer_name=row.get('farmer_name', '').strip(),
                        farmer_email=row.get('farmer_email', '').strip(),
                        farmer_phone=row.get('farmer_phone', '').strip(),
                        location=row.get('location', '').strip(),
                        allocated_hectares=Decimal(str(allocated_hectares)),
                        season_year=season_year,
                        expected_yield=Decimal(str(row.get('expected_yield', 0))) if row.get('expected_yield') else None,
                        actual_yield=Decimal(str(row.get('actual_yield', 0))) if row.get('actual_yield') else None,
                        farming_experience=farming_experience,
                        irrigation_method=row.get('irrigation_method', '').strip(),
                        soil_type=row.get('soil_type', '').strip(),
                        registration_date=registration_date,
                        notes=row.get('notes', '').strip(),
                    )
                    
                    # Handle crops grown - expect comma-separated crop names
                    crops_str = row.get('crops_grown', '').strip()
                    if crops_str:
                        crop_names = [name.strip() for name in crops_str.split(',') if name.strip()]
                        for crop_name in crop_names:
                            try:
                                # Try to find existing crop (case-insensitive)
                                crop = Crop.objects.filter(name__iexact=crop_name, is_active=True).first()
                                if crop:
                                    farmer_record.crops_grown.add(crop)
                                else:
                                    # Create new crop if it doesn't exist
                                    crop = Crop.objects.create(
                                        name=crop_name.title(),
                                        category='Unknown',  # Default category
                                        growing_season='All year',  # Default season
                                        maturity_days=90,  # Default maturity
                                        description=f'Auto-created from farmer upload: {crop_name}'
                                    )
                                    farmer_record.crops_grown.add(crop)
                            except Exception as crop_error:
                                # Log crop error but don't fail the farmer creation
                                errors.append(f'Row {index}: Warning - Could not add crop "{crop_name}": {str(crop_error)}')
                    
                    created_count += 1
                    
                except Exception as e:
                    errors.append(f'Row {index}: {str(e)}')
            
            # Show results
            if created_count > 0:
                messages.success(request, f'Successfully created {created_count} farmer records for block "{block.name}".')
            
            if errors:
                error_message = f'Encountered {len(errors)} errors:\n' + '\n'.join(errors[:10])
                if len(errors) > 10:
                    error_message += f'\n... and {len(errors) - 10} more errors.'
                messages.warning(request, error_message)
            
            if created_count > 0:
                return redirect('farms:farmers')
            
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}. Please ensure it is a valid CSV file.')
        
        return self.get(request, *args, **kwargs)