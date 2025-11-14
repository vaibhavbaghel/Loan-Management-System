from rest_framework import serializers
from .models import Loan


class LoanSerializer(serializers.ModelSerializer):
    """Serializer for creating and listing loans."""
    class Meta:
        model = Loan
        fields = [
            'id', 'customer_id', 'agent_id', 'principal', 'interest',
            'months', 'emi', 'amount', 'status',
            'start_date', 'end_date', 'created_at', 'modified_date'
        ]
        read_only_fields = ['id', 'interest', 'emi', 'amount', 'created_at', 'modified_date']


class CreateLoanSerializer(serializers.ModelSerializer):
    """Serializer for agent requesting a loan."""
    class Meta:
        model = Loan
        fields = ['customer_id', 'agent_id', 'principal', 'months']

    def validate_principal(self, value):
        if value < 10000:
            raise serializers.ValidationError('Principal must be at least 10,000')
        return value


class ApproveLoanSerializer(serializers.ModelSerializer):
    """Serializer for approving/rejecting a loan."""
    status = serializers.ChoiceField(choices=['APPROVED', 'REJECTED'])

    class Meta:
        model = Loan
        fields = ['status']

    def validate_status(self, value):
        if value not in ['APPROVED', 'REJECTED']:
            raise serializers.ValidationError('Status must be APPROVED or REJECTED')
        return value


class EditLoanSerializer(serializers.ModelSerializer):
    """Serializer for editing a loan."""
    class Meta:
        model = Loan
        fields = ['principal', 'months']

    def validate_principal(self, value):
        if value < 10000:
            raise serializers.ValidationError('Principal must be at least 10,000')
        return value

    def validate_months(self, value):
        if value <= 0:
            raise serializers.ValidationError('Months must be greater than 0')
        return value
