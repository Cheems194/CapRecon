from django.urls import path
from core.views import (
    OrganizationListView,
    BankStatementImportView,
    TransactionListView,
    LineItemListView,
    ApproveMatchView,
    RejectMatchView,
    IgnoreTransactionView,
)

urlpatterns = [
    path('organizations/', OrganizationListView.as_view(), name='organization-list'),
    path('bank-statements/import/', BankStatementImportView.as_view(), name='bank-statement-import'),
    path('transactions/', TransactionListView.as_view(), name='transaction-list'),
    path('line-items/', LineItemListView.as_view(), name='line-item-list'),
    path('matches/<int:pk>/approve/', ApproveMatchView.as_view(), name='match-approve'),
    path('matches/<int:pk>/reject/', RejectMatchView.as_view(), name='match-reject'),
    path('transactions/<int:pk>/ignore/', IgnoreTransactionView.as_view(), name='transaction-ignore'),
]
