from django.contrib import admin
from .models import Loan


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_id', 'agent_id', 'principal', 'status', 'created_at', 'modified_date')
    list_filter = ('status', 'created_at')
    search_fields = ('customer_id', 'agent_id')
    readonly_fields = ('created_at', 'modified_date')
    ordering = ('-created_at',)
