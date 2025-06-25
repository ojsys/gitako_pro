from django.views.generic import DeleteView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from apps.farms.models import Farm, FarmStaff
from apps.farms.mixins import FarmAccessMixin
from .models import Activity


class ActivityDeleteView(FarmAccessMixin, DeleteView):
    model = Activity
    template_name = 'calendar/activity_delete.html'
    success_url = reverse_lazy('calendar:activities')

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return Activity.objects.all()
        elif user.role == 'farm_owner':
            return Activity.objects.filter(calendar__farm__owner=user)
        elif user.role in ['farm_manager', 'staff', 'farmer']:
            
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

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Activity deleted successfully!')
        return super().delete(request, *args, **kwargs)


@login_required
def activity_start(request, pk):
    """Start an activity (change status from pending to in_progress)"""
    activity = get_object_or_404(Activity, pk=pk)
    
    # Check if user has permission to modify this activity
    user = request.user
    if not user.is_superuser and user.role != 'admin':
        # Check if user has access to this activity's farm
        if user.role == 'farm_owner':
            if activity.calendar.farm.owner != user:
                messages.error(request, 'You do not have permission to modify this activity.')
                return redirect('calendar:activity_detail', pk=pk)
        elif user.role in ['farm_manager', 'staff', 'farmer']:
            owned_farms = Farm.objects.filter(owner=user, is_active=True)
            managed_farms = FarmStaff.objects.filter(user=user, is_active=True).values_list('farm_id', flat=True)
            all_farm_ids = list(owned_farms.values_list('id', flat=True)) + list(managed_farms)
            
            if activity.calendar.farm.id not in all_farm_ids:
                messages.error(request, 'You do not have permission to modify this activity.')
                return redirect('calendar:activity_detail', pk=pk)
        else:
            messages.error(request, 'You do not have permission to modify this activity.')
            return redirect('calendar:activity_detail', pk=pk)
    
    if activity.status == 'pending':
        activity.status = 'in_progress'
        activity.actual_start_date = timezone.now().date()
        activity.save()
        messages.success(request, f'Activity "{activity.name}" has been started!')
    else:
        messages.warning(request, 'Activity cannot be started - it is not in pending status.')
    
    # Return to the referring page or activity detail
    next_url = request.GET.get('next', reverse('calendar:activity_detail', kwargs={'pk': pk}))
    return redirect(next_url)


@login_required
def activity_complete(request, pk):
    """Complete an activity (change status from in_progress to completed)"""
    activity = get_object_or_404(Activity, pk=pk)
    
    # Check if user has permission to modify this activity
    user = request.user
    if not user.is_superuser and user.role != 'admin':
        # Check if user has access to this activity's farm
        if user.role == 'farm_owner':
            if activity.calendar.farm.owner != user:
                messages.error(request, 'You do not have permission to modify this activity.')
                return redirect('calendar:activity_detail', pk=pk)
        elif user.role in ['farm_manager', 'staff', 'farmer']:
            owned_farms = Farm.objects.filter(owner=user, is_active=True)
            managed_farms = FarmStaff.objects.filter(user=user, is_active=True).values_list('farm_id', flat=True)
            all_farm_ids = list(owned_farms.values_list('id', flat=True)) + list(managed_farms)
            
            if activity.calendar.farm.id not in all_farm_ids:
                messages.error(request, 'You do not have permission to modify this activity.')
                return redirect('calendar:activity_detail', pk=pk)
        else:
            messages.error(request, 'You do not have permission to modify this activity.')
            return redirect('calendar:activity_detail', pk=pk)
    
    if activity.status == 'in_progress':
        activity.status = 'completed'
        activity.actual_end_date = timezone.now().date()
        activity.save()
        messages.success(request, f'Activity "{activity.name}" has been completed!')
    elif activity.status == 'pending':
        # Allow direct completion from pending
        activity.status = 'completed'
        activity.actual_start_date = timezone.now().date()
        activity.actual_end_date = timezone.now().date()
        activity.save()
        messages.success(request, f'Activity "{activity.name}" has been completed!')
    else:
        messages.warning(request, 'Activity cannot be completed - it is not in progress or pending status.')
    
    # Return to the referring page or activity detail
    next_url = request.GET.get('next', reverse('calendar:activity_detail', kwargs={'pk': pk}))
    return redirect(next_url)