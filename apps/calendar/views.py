from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db import models
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import CropCalendar, Activity, CalendarTemplate
from apps.farms.models import Farm
from apps.farms.mixins import FarmAccessMixin
from .forms import CropCalendarForm, ActivityForm

# Import additional views
from .views_additional import ActivityDeleteView, activity_start, activity_complete


class CalendarListView(FarmAccessMixin, ListView):
    model = CropCalendar
    template_name = 'calendar/list.html'
    context_object_name = 'calendars'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return CropCalendar.objects.all().select_related('farm', 'crop', 'variety').order_by('-start_date')
        elif user.role == 'farm_owner':
            return CropCalendar.objects.filter(
                farm__owner=user
            ).select_related('farm', 'crop', 'variety').order_by('-start_date')
        elif user.role in ['farm_manager', 'staff', 'farmer']:
            from apps.farms.models import FarmStaff
            
            # Get farms where user is owner or staff member
            owned_farm_ids = Farm.objects.filter(owner=user, is_active=True).values_list('id', flat=True)
            managed_farm_ids = FarmStaff.objects.filter(
                user=user, is_active=True
            ).values_list('farm_id', flat=True)
            
            # Combine farm IDs
            farm_ids = list(owned_farm_ids) + list(managed_farm_ids)
            return CropCalendar.objects.filter(
                farm__id__in=farm_ids
            ).distinct().select_related('farm', 'crop', 'variety').order_by('-start_date')
        else:
            return CropCalendar.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get calendar IDs user has access to
        calendar_ids = self.get_queryset().values_list('id', flat=True)
        
        # Get upcoming activities
        context['upcoming_activities'] = Activity.objects.filter(
            calendar_id__in=calendar_ids,
            status__in=['pending', 'in_progress'],
            scheduled_date__gte=timezone.now().date()
        ).select_related('calendar', 'assigned_to').order_by('scheduled_date')[:5]
        
        # Get overdue activities
        context['overdue_activities'] = Activity.objects.filter(
            calendar_id__in=calendar_ids,
            status__in=['pending', 'in_progress'],
            scheduled_date__lt=timezone.now().date()
        ).select_related('calendar', 'assigned_to').order_by('scheduled_date')[:5]
        
        return context


class CalendarDetailView(FarmAccessMixin, DetailView):
    model = CropCalendar
    template_name = 'calendar/detail.html'
    context_object_name = 'calendar'

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return CropCalendar.objects.all()
        elif user.role == 'farm_owner':
            return CropCalendar.objects.filter(farm__owner=user)
        elif user.role in ['farm_manager', 'staff', 'farmer']:
            from apps.farms.models import FarmStaff
            
            # Get farms where user is owner or staff member
            owned_farm_ids = Farm.objects.filter(owner=user, is_active=True).values_list('id', flat=True)
            managed_farm_ids = FarmStaff.objects.filter(
                user=user, is_active=True
            ).values_list('farm_id', flat=True)
            
            # Combine farm IDs
            farm_ids = list(owned_farm_ids) + list(managed_farm_ids)
            return CropCalendar.objects.filter(farm__id__in=farm_ids).distinct()
        else:
            return CropCalendar.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activities'] = self.object.activities.all().order_by('scheduled_date')
        return context


class ActivityListView(FarmAccessMixin, ListView):
    model = Activity
    template_name = 'calendar/activities.html'
    context_object_name = 'activities'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return Activity.objects.all().select_related('calendar', 'assigned_to').order_by('scheduled_date')
        elif user.role == 'farm_owner':
            return Activity.objects.filter(
                calendar__farm__owner=user
            ).select_related('calendar', 'assigned_to').order_by('scheduled_date')
        elif user.role in ['farm_manager', 'staff', 'farmer']:
            from apps.farms.models import FarmStaff
            
            # Get farms where user is owner or staff member
            owned_farm_ids = Farm.objects.filter(owner=user, is_active=True).values_list('id', flat=True)
            managed_farm_ids = FarmStaff.objects.filter(
                user=user, is_active=True
            ).values_list('farm_id', flat=True)
            
            # Combine farm IDs
            farm_ids = list(owned_farm_ids) + list(managed_farm_ids)
            return Activity.objects.filter(
                calendar__farm__id__in=farm_ids
            ).distinct().select_related('calendar', 'assigned_to').order_by('scheduled_date')
        else:
            return Activity.objects.none()


class CalendarCreateView(FarmAccessMixin, CreateView):
    model = CropCalendar
    form_class = CropCalendarForm
    template_name = 'calendar/create.html'
    success_url = reverse_lazy('calendar:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Crop calendar created successfully!')
        return super().form_valid(form)


class CalendarUpdateView(FarmAccessMixin, UpdateView):
    model = CropCalendar
    form_class = CropCalendarForm
    template_name = 'calendar/update.html'
    success_url = reverse_lazy('calendar:list')

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return CropCalendar.objects.all()
        elif user.role == 'farm_owner':
            return CropCalendar.objects.filter(farm__owner=user)
        elif user.role in ['farm_manager', 'staff', 'farmer']:
            from apps.farms.models import FarmStaff
            
            # Get farms where user is owner or staff member
            owned_farm_ids = Farm.objects.filter(owner=user, is_active=True).values_list('id', flat=True)
            managed_farm_ids = FarmStaff.objects.filter(
                user=user, is_active=True
            ).values_list('farm_id', flat=True)
            
            # Combine farm IDs
            farm_ids = list(owned_farm_ids) + list(managed_farm_ids)
            return CropCalendar.objects.filter(farm__id__in=farm_ids).distinct()
        else:
            return CropCalendar.objects.none()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Crop calendar updated successfully!')
        return super().form_valid(form)


class ActivityCreateView(FarmAccessMixin, CreateView):
    model = Activity
    form_class = ActivityForm
    template_name = 'calendar/activity_create.html'
    success_url = reverse_lazy('calendar:activities')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Activity created successfully!')
        return super().form_valid(form)


class ActivityUpdateView(FarmAccessMixin, UpdateView):
    model = Activity
    form_class = ActivityForm
    template_name = 'calendar/activity_update.html'
    success_url = reverse_lazy('calendar:activities')

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return Activity.objects.all()
        elif user.role == 'farm_owner':
            return Activity.objects.filter(calendar__farm__owner=user)
        elif user.role in ['farm_manager', 'staff', 'farmer']:
            from apps.farms.models import FarmStaff
            
            # Get farms where user is owner or staff member
            owned_farm_ids = Farm.objects.filter(owner=user, is_active=True).values_list('id', flat=True)
            managed_farm_ids = FarmStaff.objects.filter(
                user=user, is_active=True
            ).values_list('farm_id', flat=True)
            
            # Combine farm IDs
            farm_ids = list(owned_farm_ids) + list(managed_farm_ids)
            return Activity.objects.filter(calendar__farm__id__in=farm_ids).distinct()
        else:
            return Activity.objects.none()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Activity updated successfully!')
        return super().form_valid(form)


class ActivityDetailView(FarmAccessMixin, DetailView):
    model = Activity
    template_name = 'calendar/activity_detail.html'
    context_object_name = 'activity'

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return Activity.objects.all()
        elif user.role == 'farm_owner':
            return Activity.objects.filter(calendar__farm__owner=user)
        elif user.role in ['farm_manager', 'staff', 'farmer']:
            from apps.farms.models import FarmStaff
            
            # Get farms where user is owner or staff member
            owned_farm_ids = Farm.objects.filter(owner=user, is_active=True).values_list('id', flat=True)
            managed_farm_ids = FarmStaff.objects.filter(
                user=user, is_active=True
            ).values_list('farm_id', flat=True)
            
            # Combine farm IDs
            farm_ids = list(owned_farm_ids) + list(managed_farm_ids)
            return Activity.objects.filter(calendar__farm__id__in=farm_ids).distinct()
        else:
            return Activity.objects.none()