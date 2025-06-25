from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from apps.accounts.models import User as CustomUser
from .models import Farm, Block, FarmStaff, FarmerRecord, Crop, CropVariety


class FarmForm(forms.ModelForm):
    class Meta:
        model = Farm
        fields = ['name', 'description', 'total_area', 'location', 'latitude', 'longitude', 'soil_type', 'climate_zone', 'water_source', 'farm_image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter farm name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief description of your farm'}),
            'total_area': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Farm address or location'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': 'GPS Latitude'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any', 'placeholder': 'GPS Longitude'}),
            'soil_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Loamy, Clay, Sandy'}),
            'climate_zone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Tropical, Savanna'}),
            'water_source': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., River, Borehole, Rain-fed'}),
            'farm_image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class BlockForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set custom empty labels
        self.fields['farm'].empty_label = "Select a farm"
        self.fields['crop'].empty_label = "Select a crop"
        self.fields['variety'].empty_label = "Select a variety"
        self.fields['block_manager'].empty_label = "Select a manager"
        
        # Filter queryset based on user role
        if user:
            if user.is_superuser or user.role == 'admin':
                # Superuser and admin see all farms
                self.fields['farm'].queryset = Farm.objects.filter(is_active=True)
            elif user.role == 'farm_owner':
                # Farm owner sees their own farms
                self.fields['farm'].queryset = Farm.objects.filter(owner=user, is_active=True)
            elif user.role in ['farm_manager', 'staff', 'farmer']:
                # Farm manager, staff, and farmers see farms they're associated with
                
                # Get farms where user is owner or staff member
                owned_farms = Farm.objects.filter(owner=user, is_active=True)
                managed_farm_ids = FarmStaff.objects.filter(
                    user=user, is_active=True
                ).values_list('farm_id', flat=True)
                managed_farms = Farm.objects.filter(id__in=managed_farm_ids, is_active=True)
                
                # Combine both querysets
                farm_ids = list(owned_farms.values_list('id', flat=True)) + list(managed_farms.values_list('id', flat=True))
                self.fields['farm'].queryset = Farm.objects.filter(id__in=farm_ids, is_active=True).distinct()
            else:
                # Default: no farms
                self.fields['farm'].queryset = Farm.objects.none()
        
        # Filter to active crops only
        self.fields['crop'].queryset = Crop.objects.filter(is_active=True)

    class Meta:
        model = Block
        fields = ['farm', 'name', 'description', 'size', 'crop', 'variety', 'plant_population', 'expected_yield', 'block_manager', 'soil_ph', 'irrigation_type', 'planting_date', 'expected_harvest_date', 'notes']
        widgets = {
            'farm': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter block/field name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief description of this block'}),
            'size': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'crop': forms.Select(attrs={'class': 'form-select'}),
            'variety': forms.Select(attrs={'class': 'form-select'}),
            'plant_population': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': 'Number of plants per hectare'}),
            'expected_yield': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Expected yield in tons'}),
            'block_manager': forms.Select(attrs={'class': 'form-select'}),
            'soil_ph': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'max': '14', 'placeholder': '0.0 - 14.0'}),
            'irrigation_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Drip, Sprinkler, Flood'}),
            'planting_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expected_harvest_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes about this block'}),
        }


class BlockUpdateForm(BlockForm):
    class Meta(BlockForm.Meta):
        fields = BlockForm.Meta.fields + ['actual_harvest_date']
        widgets = {
            **BlockForm.Meta.widgets,
            'actual_harvest_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class StaffCreationForm(forms.ModelForm):
    # User account fields
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username for login'
        }),
        help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
    )
    
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name'
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'staff@example.com'
        })
    )
    
    phone_number = forms.CharField(
        max_length=17,
        required=False,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+234 xxx xxx xxxx'
        })
    )
    
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Street address'
        })
    )
    
    city = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'City'
        })
    )
    
    state = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'State'
        })
    )
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        }),
        help_text='Password must be at least 8 characters long.'
    )
    
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set custom empty labels
        self.fields['farm'].empty_label = "Select Farm"
        self.fields['role'].empty_label = "Select Role"
        
        # Filter queryset based on user
        if user:
            self.fields['farm'].queryset = Farm.objects.filter(owner=user, is_active=True)
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError('A user with this username already exists.')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Passwords do not match.')
        return password2
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1 and len(password1) < 8:
            raise forms.ValidationError('Password must be at least 8 characters long.')
        return password1
    
    class Meta:
        model = FarmStaff
        fields = ['farm', 'role', 'salary', 'hire_date', 'notes']
        widgets = {
            'farm': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Monthly salary in Naira'
            }),
            'hire_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes about this staff member'
            }),
        }


class FarmStaffForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set custom empty labels
        self.fields['farm'].empty_label = "Select Farm"
        self.fields['user'].empty_label = "Select User"
        self.fields['role'].empty_label = "Select Role"
        
        # Filter queryset based on user
        if user:
            self.fields['farm'].queryset = Farm.objects.filter(owner=user, is_active=True)

    class Meta:
        model = FarmStaff
        fields = ['farm', 'user', 'role', 'salary', 'hire_date', 'notes']
        widgets = {
            'farm': forms.Select(attrs={'class': 'form-select'}),
            'user': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Monthly salary in Naira'
            }),
            'hire_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes about this staff member'
            }),
        }


class FarmerRecordForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set custom empty labels
        self.fields['farm'].empty_label = "Select a farm"
        self.fields['block'].empty_label = "Select a block (optional)"
        
        # Filter queryset based on user role
        if user:
            if user.is_superuser:
                self.fields['farm'].queryset = Farm.objects.filter(is_active=True)
                self.fields['block'].queryset = Block.objects.filter(is_active=True)
            elif user.role == 'farm_owner':
                self.fields['farm'].queryset = Farm.objects.filter(owner=user, is_active=True)
                self.fields['block'].queryset = Block.objects.filter(farm__owner=user, is_active=True)
            else:
                # Staff - get their assigned farm
                from .permissions import RolePermissionMixin
                permission_mixin = RolePermissionMixin()
                permission_mixin.request = type('MockRequest', (), {'user': user})()
                assigned_farm = permission_mixin.get_user_assigned_farm()
                
                if assigned_farm:
                    self.fields['farm'].queryset = Farm.objects.filter(id=assigned_farm.id, is_active=True)
                    self.fields['block'].queryset = Block.objects.filter(farm=assigned_farm, is_active=True)
                else:
                    self.fields['farm'].queryset = Farm.objects.none()
                    self.fields['block'].queryset = Block.objects.none()
        
        # Filter to active crops only
        self.fields['crops_grown'].queryset = Crop.objects.filter(is_active=True)

    class Meta:
        model = FarmerRecord
        fields = ['farm', 'block', 'farmer_name', 'farmer_email', 'farmer_phone', 'location', 'allocated_hectares', 'crops_grown', 'season_year', 'expected_yield', 'farming_experience', 'irrigation_method', 'soil_type', 'registration_date', 'notes']
        widgets = {
            'farm': forms.Select(attrs={'class': 'form-select'}),
            'block': forms.Select(attrs={'class': 'form-select'}),
            'farmer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name of the farmer'}),
            'farmer_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'farmer@example.com'}),
            'farmer_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+234 xxx xxx xxxx'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Farmer location/address'}),
            'allocated_hectares': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Hectares allocated'}),
            'crops_grown': forms.CheckboxSelectMultiple(),
            'season_year': forms.NumberInput(attrs={'class': 'form-control', 'min': '2020', 'max': '2030', 'placeholder': '2024'}),
            'expected_yield': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Expected yield in tons'}),
            'farming_experience': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': 'Years of farming experience'}),
            'irrigation_method': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Drip, Sprinkler, Rain-fed'}),
            'soil_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Loamy, Clay, Sandy'}),
            'registration_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes about this farmer'}),
        }