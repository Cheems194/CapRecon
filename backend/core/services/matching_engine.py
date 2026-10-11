import re
from decimal import Decimal
from core.models import LineItem, MatchSuggestion, Transaction


def normalize_reference(text):
    """Uppercase and keep only alphanumeric characters: 'CC-1003' -> 'CC1003'."""
    if not text:
        return ""
    return re.sub(r'[^A-Z0-9]', '', text.upper())


def normalize_name(name):
    """
    Uppercase, replace non-alphanumeric with spaces, collapse spaces.
    Drop trailing LLC, LP, LTD, INC, but keep TRUST.
    """
    if not name:
        return ""
    clean = re.sub(r'[^A-Z0-9]+', ' ', name.upper()).strip()
    # Drop trailing legal entity indicators
    clean = re.sub(r'\b(LLC|LP|LTD|INC)\b$', '', clean).strip()
    return clean


def normalize_words(text):
    """Normalize text into uppercase space-separated words for whole-word searching."""
    if not text:
        return ""
    return re.sub(r'[^A-Z0-9]+', ' ', text.upper()).strip()


def run_matching_for_transaction(transaction):
    """
    Applies Section 6 matching rules to an incoming credit transaction.
    Debits or already reconciled transactions are skipped.
    """
    if transaction.transaction_type != Transaction.TYPE_CREDIT:
        return

    # Clear any existing proposed matches if re-running
    transaction.matches.filter(status=MatchSuggestion.STATUS_PROPOSED).delete()

    # 1. Eligible line items:
    # - Same organization
    # - Remaining amount > 0.00
    # - Capital call date on or before transaction date
    eligible_items = [
        item for item in LineItem.objects.filter(
            organization=transaction.organization,
            capital_call__call_date__lte=transaction.date
        ).select_related('capital_call')
        if item.amount_remaining > Decimal('0.00')
    ]

    tx_ref_norm = normalize_reference(transaction.bank_reference)
    tx_desc_ref_norm = normalize_reference(transaction.description)
    tx_words_norm = f" {normalize_words(transaction.description)} "

    # 2. Reference check
    ref_matched_items = []
    for item in eligible_items:
        item_ref_norm = normalize_reference(item.wire_reference)
        if item_ref_norm and (item_ref_norm in tx_desc_ref_norm or item_ref_norm in tx_ref_norm):
            ref_matched_items.append(item)

    if ref_matched_items:
        if len(ref_matched_items) == 1:
            item = ref_matched_items[0]
            if transaction.amount <= item.amount_remaining:
                # Valid full or partial payment
                if transaction.amount == item.amount_remaining:
                    reason = f"Reference {item.wire_reference} found; amount equals remaining {item.amount_remaining:,.2f}"
                else:
                    reason = f"Reference {item.wire_reference} found; partial payment of {transaction.amount:,.2f} against remaining {item.amount_remaining:,.2f}"

                MatchSuggestion.objects.create(
                    transaction=transaction,
                    line_item=item,
                    status=MatchSuggestion.STATUS_PROPOSED,
                    reason=reason
                )
                transaction.status = Transaction.STATUS_SUGGESTED
                transaction.review_reason = reason
            else:
                # Overpayment
                transaction.status = Transaction.STATUS_NEEDS_REVIEW
                transaction.review_reason = (
                    f"Overpayment: amount {transaction.amount:,.2f} exceeds remaining {item.amount_remaining:,.2f} "
                    f"for reference {item.wire_reference}"
                )
        else:
            # Multiple references found
            transaction.status = Transaction.STATUS_NEEDS_REVIEW
            transaction.review_reason = "Multiple matching line item references found in description"
            for item in ref_matched_items:
                MatchSuggestion.objects.create(
                    transaction=transaction,
                    line_item=item,
                    status=MatchSuggestion.STATUS_PROPOSED,
                    reason=f"Candidate match: reference {item.wire_reference} found in description"
                )
        transaction.save()
        return

    # 3. Name and exact amount check (only if no reference was found)
    name_matched_items = []
    for item in eligible_items:
        if transaction.amount == item.amount_remaining:
            norm_investor = normalize_name(item.investor_name)
            # Check if investor name appears as whole words in description
            if norm_investor and f" {norm_investor} " in tx_words_norm:
                name_matched_items.append(item)

    if len(name_matched_items) == 1:
        item = name_matched_items[0]
        reason = f"Investor '{item.investor_name}' found; amount equals remaining {item.amount_remaining:,.2f}"
        MatchSuggestion.objects.create(
            transaction=transaction,
            line_item=item,
            status=MatchSuggestion.STATUS_PROPOSED,
            reason=reason
        )
        transaction.status = Transaction.STATUS_SUGGESTED
        transaction.review_reason = reason
    elif len(name_matched_items) > 1:
        transaction.status = Transaction.STATUS_NEEDS_REVIEW
        transaction.review_reason = "Multiple candidates match both investor name and amount"
        for item in name_matched_items:
            MatchSuggestion.objects.create(
                transaction=transaction,
                line_item=item,
                status=MatchSuggestion.STATUS_PROPOSED,
                reason=f"Candidate match: investor '{item.investor_name}' and exact amount {transaction.amount:,.2f}"
            )
    else:
        transaction.status = Transaction.STATUS_NEEDS_REVIEW
        transaction.review_reason = "No matching reference or investor name found"

    transaction.save()


def match_transactions_batch(transactions):
    """Runs matching for a list of newly imported transactions."""
    for tx in transactions:
        run_matching_for_transaction(tx)
