from django.urls import path
from .views import (
    UserSignupView, UserLoginView, UserProfileView,
    CreateAdminView, ListAgentCustomersView, ListAdminUsersView,
    ListPendingApprovalsView, ApproveOrDeleteAgentView
)

urlpatterns = [
    path('signup/', UserSignupView.as_view(), name='signup'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('create-admin/', CreateAdminView.as_view(), name='create-admin'),
    path('list-agents/', ListAgentCustomersView.as_view(), name='list-agents'),
    path('list-users/', ListAdminUsersView.as_view(), name='list-users'),
    path('list-approvals/', ListPendingApprovalsView.as_view(), name='list-approvals'),
    path('approve-delete/<int:pk>/', ApproveOrDeleteAgentView.as_view(), name='approve-delete'),
]
