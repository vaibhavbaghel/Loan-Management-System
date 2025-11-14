from django.db import models
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords


def validate_principal(value):
    """Validator: principal must be >= 10,000."""
    if value < 10000:
        raise ValidationError('Principal Amount Cannot be less than 10000')


class Loan(models.Model):
    """
    Loan model representing a loan request/approval.
    Stores references to customer and agent IDs (not FK to User since User Service is separate).
    """
    LOAN_STATUS_CHOICES = [
        ('NEW', 'New'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    customer_id = models.CharField(max_length=255)  # Reference to User Service
    agent_id = models.CharField(max_length=255, null=True, blank=True)  # Reference to User Service
    
    principal = models.FloatField(default=10000, validators=[validate_principal])
    interest = models.FloatField(default=9)
    months = models.IntegerField(default=0)
    amount = models.FloatField(default=0)
    emi = models.FloatField(default=0)
    status = models.CharField(max_length=12, choices=LOAN_STATUS_CHOICES, default="NEW", db_index=True)
    
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords()

    def __str__(self):
        return f"Loan {self.id} - Customer {self.customer_id} - {self.principal}"

    class Meta:
        db_table = 'loan'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['customer_id']),
            models.Index(fields=['agent_id']),
        ]
