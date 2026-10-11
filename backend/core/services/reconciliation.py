from decimal import Decimal
from django.db import transaction
from rest_framework.exceptions import APIException
from core.models import LineItem, MatchSuggestion, Transaction


class ConflictError(APIException):
    status_code = 409
    default_detail = "Conflict: The requested reconciliation action cannot be performed."


def approve_match(match_id, organization):
    """
    Approves a match in one atomic transaction with row locking:
    - Re-checks remaining amount against transaction amount.
    - If transaction is already reconciled or amount > remaining -> raises 409 Conflict.
    - Updates line item funded amount and status.
    - Updates match to 'approved', other matches to 'rejected'.
    - Updates transaction to 'reconciled'.
    """
    with transaction.atomic():
        try:
            match = MatchSuggestion.objects.select_related('transaction', 'line_item').get(
                id=match_id,
                transaction__organization=organization
            )
        except MatchSuggestion.DoesNotExist:
            raise ConflictError("Match suggestion not found for this organization.")

        # Lock rows in PostgreSQL
        line_item = LineItem.objects.select_for_update().get(id=match.line_item_id)
        tx = Transaction.objects.select_for_update().get(id=match.transaction_id)

        # 1. Double-funding prevention check
        if tx.status == Transaction.STATUS_RECONCILED:
            raise ConflictError("Transaction is already reconciled.")

        if match.status != MatchSuggestion.STATUS_PROPOSED:
            raise ConflictError(f"Cannot approve match with status '{match.status}'.")

        # 2. Check remaining amount
        if tx.amount > line_item.amount_remaining:
            raise ConflictError(
                f"Amount {tx.amount:,.2f} exceeds remaining balance {line_item.amount_remaining:,.2f}."
            )

        # 3. Update Line Item
        line_item.amount_funded += tx.amount
        if line_item.amount_remaining == Decimal('0.00'):
            line_item.status = LineItem.STATUS_FUNDED
        else:
            line_item.status = LineItem.STATUS_PARTIALLY_FUNDED
        line_item.save()

        # 4. Update Matches: approve chosen, reject others
        match.status = MatchSuggestion.STATUS_APPROVED
        match.save()

        tx.matches.exclude(id=match.id).update(status=MatchSuggestion.STATUS_REJECTED)

        # 5. Mark transaction reconciled
        tx.status = Transaction.STATUS_RECONCILED
        tx.save()

        return tx


def reject_match(match_id, organization):
    """
    Rejects a specific proposed match.
    If no proposed matches remain on the transaction, marks it 'needs_review'.
    """
    with transaction.atomic():
        try:
            match = MatchSuggestion.objects.select_related('transaction').get(
                id=match_id,
                transaction__organization=organization
            )
        except MatchSuggestion.DoesNotExist:
            raise ConflictError("Match suggestion not found.")

        tx = Transaction.objects.select_for_update().get(id=match.transaction_id)
        if tx.status == Transaction.STATUS_RECONCILED:
            raise ConflictError("Cannot reject a match on an already reconciled transaction.")

        match.status = MatchSuggestion.STATUS_REJECTED
        match.save()

        # If no proposed matches remain, mark transaction as needs_review
        has_proposed = tx.matches.filter(status=MatchSuggestion.STATUS_PROPOSED).exists()
        if not has_proposed:
            tx.status = Transaction.STATUS_NEEDS_REVIEW
            tx.review_reason = "All proposed matches were rejected."
            tx.save()

        return tx


def ignore_transaction(transaction_id, organization):
    """
    Marks a suggested or needs_review credit transaction as 'ignored'.
    Rejects its matches. Returns 409 if already reconciled.
    """
    with transaction.atomic():
        try:
            tx = Transaction.objects.select_for_update().get(
                id=transaction_id,
                organization=organization
            )
        except Transaction.DoesNotExist:
            raise ConflictError("Transaction not found.")

        if tx.status == Transaction.STATUS_RECONCILED:
            raise ConflictError("Cannot ignore an already reconciled transaction.")

        tx.status = Transaction.STATUS_IGNORED
        tx.review_reason = "Manually marked as ignored."
        tx.save()

        # Reject all linked proposed matches
        tx.matches.filter(status=MatchSuggestion.STATUS_PROPOSED).update(
            status=MatchSuggestion.STATUS_REJECTED
        )

        return tx
