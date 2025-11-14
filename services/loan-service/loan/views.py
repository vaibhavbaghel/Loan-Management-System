import datetime
from django.http import Http404
from django.utils import timezone
from django.db import transaction

from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from .models import Loan
from .serializers import (
    LoanSerializer, CreateLoanSerializer,
    ApproveLoanSerializer, EditLoanSerializer
)
from .permissions import IsAgent, IsAdmin, IsAdminOrAgent, IsCustomer
from .utils import calculate_interest, calculate_emi


class RequestLoanView(APIView):
    """
    POST /api/loan/customer-loan/
    Agent requests a loan for a customer.
    """
    permission_classes = (IsAuthenticated, IsAgent,)
    authentication_classes = (JSONWebTokenAuthentication,)

    def post(self, request):
        try:
            serializer = CreateLoanSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': 'Invalid loan request data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            # Calculate interest and EMI
            principal = serializer.validated_data['principal']
            months = serializer.validated_data['months']
            interest = calculate_interest(principal)
            emi = calculate_emi(principal, months, interest)
            amount = emi * months

            # Create loan
            loan = Loan.objects.create(
                customer_id=serializer.validated_data['customer_id'],
                agent_id=request.user.get('id'),
                principal=principal,
                interest=interest,
                months=months,
                emi=emi,
                amount=amount,
                status='NEW',
                start_date=timezone.localtime(),
                end_date=timezone.localtime() + datetime.timedelta(hours=months * 730)
            )

            response_serializer = LoanSerializer(loan)
            return Response({
                'success': True,
                'message': 'Loan request submitted successfully',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'success': False,
                'message': 'Failed to create loan',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ApproveOrRejectLoanView(APIView):
    """
    PUT /api/loan/approve-reject-loan/<int:pk>/
    Admin approves or rejects a loan (atomic transaction).
    """
    permission_classes = (IsAuthenticated, IsAdmin,)
    authentication_classes = (JSONWebTokenAuthentication,)

    def get_object(self, pk):
        try:
            return Loan.objects.get(pk=pk)
        except Loan.DoesNotExist:
            raise Http404('Loan not found')

    def put(self, request, pk):
        try:
            with transaction.atomic():
                loan = Loan.objects.select_for_update().get(pk=pk)
                
                # Validate current status
                if loan.status != 'NEW':
                    return Response({
                        'success': False,
                        'message': f'Cannot modify loan with status {loan.status}'
                    }, status=status.HTTP_400_BAD_REQUEST)

                serializer = ApproveLoanSerializer(data=request.data)
                if not serializer.is_valid():
                    return Response({
                        'success': False,
                        'message': 'Invalid status value',
                        'errors': serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)

                loan.status = serializer.validated_data['status']
                loan.save()

                response_serializer = LoanSerializer(loan)
                return Response({
                    'success': True,
                    'message': f'Loan {pk} has been {loan.status.lower()}',
                    'data': response_serializer.data
                }, status=status.HTTP_200_OK)

        except Http404:
            return Response({
                'success': False,
                'message': 'Loan not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Failed to update loan',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class EditLoanView(APIView):
    """
    PUT /api/loan/edit-loan/<int:pk>/
    Agent edits a loan (only if not approved).
    """
    permission_classes = (IsAuthenticated, IsAgent,)
    authentication_classes = (JSONWebTokenAuthentication,)

    def get_object(self, pk):
        try:
            return Loan.objects.get(pk=pk)
        except Loan.DoesNotExist:
            raise Http404('Loan not found')

    def put(self, request, pk):
        try:
            loan = self.get_object(pk)

            # Prevent editing approved loans
            if loan.status == 'APPROVED':
                return Response({
                    'success': False,
                    'message': 'Cannot edit an approved loan'
                }, status=status.HTTP_400_BAD_REQUEST)

            serializer = EditLoanSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'message': 'Invalid edit data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            # Recalculate interest and EMI
            principal = serializer.validated_data['principal']
            months = serializer.validated_data['months']
            interest = calculate_interest(principal)
            emi = calculate_emi(principal, months, interest)
            amount = emi * months

            # Update loan
            loan.principal = principal
            loan.interest = interest
            loan.months = months
            loan.emi = emi
            loan.amount = amount
            loan.status = 'NEW'
            loan.start_date = timezone.localtime()
            loan.end_date = timezone.localtime() + datetime.timedelta(hours=months * 730)
            loan.save()

            response_serializer = LoanSerializer(loan)
            return Response({
                'success': True,
                'message': 'Loan updated successfully',
                'data': response_serializer.data
            }, status=status.HTTP_200_OK)

        except Http404:
            return Response({
                'success': False,
                'message': 'Loan not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Failed to update loan',
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class ListLoansForAdminAgentView(generics.ListAPIView):
    """
    GET /api/loan/list-loans-admin-agent/
    List loans for admins and agents (with optional status filter).
    """
    permission_classes = (IsAuthenticated, IsAdminOrAgent,)
    authentication_classes = (JSONWebTokenAuthentication,)
    serializer_class = LoanSerializer

    def get_queryset(self):
        queryset = Loan.objects.all().select_related()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.order_by('-modified_date')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'count': len(serializer.data)
        })


class ListLoansForCustomerView(generics.ListAPIView):
    """
    GET /api/loan/list-loans-customer/
    List loans for a customer (with optional status filter).
    """
    permission_classes = (IsAuthenticated, IsCustomer,)
    authentication_classes = (JSONWebTokenAuthentication,)
    serializer_class = LoanSerializer

    def get_queryset(self):
        customer_id = str(self.request.user.get('id'))
        queryset = Loan.objects.filter(customer_id=customer_id)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.order_by('-modified_date')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data,
            'count': len(serializer.data)
        })
