from django.urls import path
from .views import (
    RequestLoanView, ApproveOrRejectLoanView, EditLoanView,
    ListLoansForAdminAgentView, ListLoansForCustomerView
)

urlpatterns = [
    path('customer-loan/', RequestLoanView.as_view(), name='request-loan'),
    path('approve-reject-loan/<int:pk>/', ApproveOrRejectLoanView.as_view(), name='approve-reject-loan'),
    path('edit-loan/<int:pk>/', EditLoanView.as_view(), name='edit-loan'),
    path('list-loans-admin-agent/', ListLoansForAdminAgentView.as_view(), name='list-loans-admin-agent'),
    path('list-loans-customer/', ListLoansForCustomerView.as_view(), name='list-loans-customer'),
]
