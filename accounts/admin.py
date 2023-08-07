from django.contrib import admin
from . models import User,UserProfile
from django.contrib.auth.admin import UserAdmin
#from vendor.models import Vendor

# Register your models here.
class CustomUserAdmin(UserAdmin):
    list_display = ('email','first_name','last_name','role','is_active')
    ordering = ('-date_joined',)
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

admin.site.register(User,CustomUserAdmin)
admin.site.register(UserProfile)
#admin.site.register(Vendor)