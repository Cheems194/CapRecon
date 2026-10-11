import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.db import IntegrityError
from core.models import Transaction


REQUIRED_COLUMNS = ['date', 'description', 'amount', 'type', 'reference']


class CSVImportError(Exception):
    pass


def import_bank_statement_csv(organization, csv_file_or_content):
    if isinstance(csv_file_or_content, bytes):
        content = csv_file_or_content.decode('utf-8-sig', errors='replace')
    elif isinstance(csv_file_or_content, str):
        content = csv_file_or_content
    else:
        content = csv_file_or_content.read().decode('utf-8-sig', errors='replace')

    reader = csv.reader(io.StringIO(content))
    try:
        header_row = next(reader)
    except StopIteration:
        raise CSVImportError("The CSV file is empty.")

    headers = [col.strip().lower() for col in header_row]
    header_indices = {}
    for col in REQUIRED_COLUMNS:
        if col not in headers:
            raise CSVImportError(f"Missing required column: '{col}'")
        header_indices[col] = headers.index(col)

    imported_transactions = []
    errors = []
    duplicate_count = 0
    seen_references_in_file = set()

    for line_number, row in enumerate(reader, start=2):
        if not row or all(c.strip() == '' for c in row):
            continue

        if len(row) < len(REQUIRED_COLUMNS):
            errors.append({
                "line": line_number,
                "message": "Row has fewer columns than required."
            })
            continue

        raw_date = row[header_indices['date']].strip()
        raw_desc = row[header_indices['description']].strip()
        raw_amount = row[header_indices['amount']].strip()
        raw_type = row[header_indices['type']].strip().lower()
        raw_ref = row[header_indices['reference']].strip()

        if not raw_desc:
            errors.append({"line": line_number, "message": "Description is required."})
            continue
        if not raw_ref:
            errors.append({"line": line_number, "message": "Reference is required."})
            continue

        try:
            parsed_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
        except ValueError:
            errors.append({
                "line": line_number,
                "message": f"Invalid date '{raw_date}'. Must be YYYY-MM-DD real calendar date."
            })
            continue

        clean_amount_str = raw_amount.replace(',', '')
        try:
            parsed_amount = Decimal(clean_amount_str)
        except (InvalidOperation, ValueError):
            errors.append({
                "line": line_number,
                "message": f"Invalid amount format '{raw_amount}'."
            })
            continue

        if parsed_amount == Decimal('0.00'):
            errors.append({"line": line_number, "message": "Amount cannot be zero."})
            continue

        if raw_type not in ['credit', 'debit']:
            errors.append({
                "line": line_number,
                "message": f"Type must be 'credit' or 'debit', got '{raw_type}'."
            })
            continue

        if raw_type == 'credit' and parsed_amount < 0:
            errors.append({
                "line": line_number,
                "message": f"Credit amount must be positive, got {parsed_amount}."
            })
            continue

        if raw_type == 'debit' and parsed_amount > 0:
            errors.append({
                "line": line_number,
                "message": f"Debit amount must be negative, got {parsed_amount}."
            })
            continue

        if raw_ref in seen_references_in_file:
            duplicate_count += 1
            continue
        seen_references_in_file.add(raw_ref)

        if Transaction.objects.filter(organization=organization, bank_reference=raw_ref).exists():
            duplicate_count += 1
            continue

        tx_status = (
            Transaction.STATUS_IGNORED if raw_type == 'debit'
            else Transaction.STATUS_NEEDS_REVIEW
        )

        try:
            tx = Transaction.objects.create(
                organization=organization,
                date=parsed_date,
                description=raw_desc,
                amount=parsed_amount,
                transaction_type=raw_type,
                bank_reference=raw_ref,
                status=tx_status,
                review_reason="Debit transaction ignored" if raw_type == 'debit' else ""
            )
            imported_transactions.append(tx)
        except IntegrityError:
            duplicate_count += 1

    return {
        "imported_count": len(imported_transactions),
        "duplicate_count": duplicate_count,
        "errors": errors,
        "imported_transactions": imported_transactions,
    }
