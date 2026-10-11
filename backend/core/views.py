from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from core.models import Organization, LineItem, Transaction, MatchSuggestion
from core.views_base import TenantScopedAPIView
from core.serializers import (
    OrganizationSerializer,
    LineItemSerializer,
    TransactionSerializer,
)
from core.services.csv_importer import import_bank_statement_csv, CSVImportError
from core.services.matching_engine import match_transactions_batch
from core.services.reconciliation import approve_match, reject_match, ignore_transaction


class OrganizationListView(APIView):
    """Public endpoint to list organizations for the UI tenant switcher."""
    def get(self, request):
        orgs = Organization.objects.all().order_by('name')
        return Response(OrganizationSerializer(orgs, many=True).data)


class BankStatementImportView(TenantScopedAPIView):
    """
    POST /api/bank-statements/import/
    Uploads a bank CSV, validates rows, saves records, runs matching engine.
    """
    def post(self, request):
        csv_file = request.FILES.get('file')
        raw_content = request.data.get('content')

        if not csv_file and not raw_content:
            return Response(
                {"error": "Please provide a CSV file upload or 'content' string."},
                status=status.HTTP_400_BAD_REQUEST
            )

        payload = csv_file if csv_file else raw_content

        try:
            result = import_bank_statement_csv(request.tenant, payload)
        except CSVImportError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Run rule-based matching engine for imported credit transactions
        credits = [
            tx for tx in result["imported_transactions"]
            if tx.transaction_type == Transaction.TYPE_CREDIT
        ]
        match_transactions_batch(credits)

        return Response({
            "imported_count": result["imported_count"],
            "duplicate_count": result["duplicate_count"],
            "errors": result["errors"],
        }, status=status.HTTP_201_CREATED)


class TransactionListView(TenantScopedAPIView):
    """
    GET /api/transactions/
    Lists all transactions for the current tenant, newest first, with matches.
    """
    def get(self, request):
        transactions = Transaction.objects.filter(
            organization=request.tenant
        ).prefetch_related('matches__line_item').order_by('-date', '-created_at')
        return Response(TransactionSerializer(transactions, many=True).data)


class LineItemListView(TenantScopedAPIView):
    """
    GET /api/line-items/
    Lists all capital call line items for the current tenant.
    """
    def get(self, request):
        items = LineItem.objects.filter(
            organization=request.tenant
        ).select_related('capital_call').order_by('capital_call__call_number', 'investor_name')
        return Response(LineItemSerializer(items, many=True).data)


class ApproveMatchView(TenantScopedAPIView):
    """
    POST /api/matches/<int:pk>/approve/
    Atomically approves a match suggestion, updating line item funding.
    """
    def post(self, request, pk):
        # Must return 404 if match doesn't belong to current tenant
        match = get_object_or_404(
            MatchSuggestion.objects.select_related('transaction'),
            id=pk,
            transaction__organization=request.tenant
        )
        tx = approve_match(match.id, request.tenant)
        return Response(TransactionSerializer(tx).data, status=status.HTTP_200_OK)


class RejectMatchView(TenantScopedAPIView):
    """
    POST /api/matches/<int:pk>/reject/
    Rejects a match suggestion.
    """
    def post(self, request, pk):
        match = get_object_or_404(
            MatchSuggestion.objects.select_related('transaction'),
            id=pk,
            transaction__organization=request.tenant
        )
        tx = reject_match(match.id, request.tenant)
        return Response(TransactionSerializer(tx).data, status=status.HTTP_200_OK)


class IgnoreTransactionView(TenantScopedAPIView):
    """
    POST /api/transactions/<int:pk>/ignore/
    Marks a transaction as ignored and rejects its matches.
    """
    def post(self, request, pk):
        tx_obj = get_object_or_404(Transaction, id=pk, organization=request.tenant)
        tx = ignore_transaction(tx_obj.id, request.tenant)
        return Response(TransactionSerializer(tx).data, status=status.HTTP_200_OK)
