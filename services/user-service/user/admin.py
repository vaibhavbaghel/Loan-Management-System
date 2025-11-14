from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_customer', 'is_agent', 'is_admin', 'is_approved')
    list_filter = ('is_customer', 'is_agent', 'is_admin', 'is_approved')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
