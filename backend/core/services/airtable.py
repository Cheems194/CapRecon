import os
import requests
from core.models import Transaction


def sync_transaction_to_airtable(transaction, client=None):
    token = os.getenv('AIRTABLE_TOKEN') or os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_BASE_ID')
    table_name = os.getenv('AIRTABLE_TABLE_NAME', 'Needs Review')

    if not token or not base_id:
        return

    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "fields": {
            "Bank Reference": transaction.bank_reference,
            "Date": str(transaction.date),
            "Description": transaction.description,
            "Amount": float(transaction.amount),
            "Review Reason": transaction.review_reason,
            "Organization": transaction.organization.slug,
        }
    }

    try:
        http = client or requests
        response = http.post(url, json=payload, headers=headers, timeout=5)

        if response.status_code in [200, 201]:
            data = response.json()
            transaction.airtable_record_id = data.get('id', '')
            transaction.airtable_sync_status = Transaction.AIRTABLE_SYNCED
            transaction.save(update_fields=['airtable_record_id', 'airtable_sync_status'])
        else:
            transaction.airtable_sync_status = Transaction.AIRTABLE_SYNC_FAILED
            transaction.save(update_fields=['airtable_sync_status'])

    except Exception:
        transaction.airtable_sync_status = Transaction.AIRTABLE_SYNC_FAILED
        transaction.save(update_fields=['airtable_sync_status'])


def sync_needs_review_transactions(transactions, client=None):
    for tx in transactions:
        if tx.status == Transaction.STATUS_NEEDS_REVIEW:
            sync_transaction_to_airtable(tx, client=client)
