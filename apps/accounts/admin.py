from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, UserProfile, Organization, OrganizationMembership


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'role')


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'role', 'is_active', 'is_staff')


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_active', 'is_verified', 'date_joined')
    list_filter = ('role', 'is_active', 'is_verified', 'is_staff', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'username')
    ordering = ('-date_joined',)
    inlines = [UserProfileInline]

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'username', 'phone_number', 'profile_picture')}),
        ('Address', {'fields': ('address', 'city', 'state', 'country')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )


class OrganizationMembershipInline(admin.TabularInline):
    model = OrganizationMembership
    extra = 0
    readonly_fields = ('invited_at', 'joined_at')


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'city', 'state', 'is_active', 'created_at')
    list_filter = ('is_active', 'state', 'country', 'created_at')
    search_fields = ('name', 'owner__email', 'city', 'state')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [OrganizationMembershipInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'owner', 'logo')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'website')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'country')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'role', 'is_active', 'invited_at', 'joined_at')
    list_filter = ('role', 'is_active', 'invited_at', 'joined_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'organization__name')
    readonly_fields = ('invited_at', 'joined_at')

    fieldsets = (
        ('Membership Details', {
            'fields': ('organization', 'user', 'role', 'is_active')
        }),
        ('Invitation Details', {
            'fields': ('invited_by', 'invited_at', 'joined_at')
        }),
    )