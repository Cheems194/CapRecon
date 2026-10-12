# Assessment Notes - CapRecon

## App Name
**CapRecon** (Capital Call Bank Reconciliation Portal)

---

## 1. Setup Instructions (Fresh Clone)

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL running locally or in Docker

### Backend Setup
1. Open a terminal in the project root and navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure database environment variables (copy `.env.example` to `.env` or set environment variables):
   ```bash
   cp .env.example .env
   ```
5. Ensure a PostgreSQL database exists (default name: `caprecon`).
6. Run database migrations:
   ```bash
   python manage.py migrate
   ```
7. Seed the initial demo organizations and capital calls:
   ```bash
   python manage.py seed_demo
   ```
8. Start the Django API server:
   ```bash
   python manage.py runserver 8000
   ```

### Frontend Setup
1. Open a second terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Open your browser at `http://localhost:5173/`.

---

## 2. Command to Run Tests

From the `backend` directory (with virtual environment activated):

```bash
python manage.py test
```

This runs the automated test suite covering all 8 assessment specifications:
1. Missing column rejects the file and saves nothing.
2. Amount parsing with thousands separators, sign/type validation, invalid dates, and Decimal type integrity.
3. Intra-file and re-upload duplicate detection.
4. Case-insensitive reference matching and partial payments.
5. Name and amount matching, including multiple candidates handling.
6. Overpayment detection with no matches.
7. Atomic approval updating funded balance and returning 409 Conflict on repeated attempts.
8. Multi-tenant isolation returning 404 for cross-organization queries and approvals.

---

## 3. Data Model Summary

- **Organization**: Tenant entity (`name`, `slug`).
- **CapitalCall**: Call notice scoped to an organization (`call_number`, `call_date`, `due_date`).
- **LineItem**: An investor's share of a capital call (`investor_name`, `wire_reference`, `amount_called`, `amount_funded`, `status`). Computes dynamic `amount_remaining`.
- **Transaction**: Bank statement record (`date`, `description`, `amount`, `transaction_type`, `bank_reference`, `status`, `review_reason`). Unique per `(organization, bank_reference)`.
- **MatchSuggestion**: Link between a transaction and a line item (`transaction`, `line_item`, `status`, `reason`).

---
## 4. API Endpoints

All scoped endpoints require the `X-Organization` header containing the tenant slug (e.g., `northwind`).

| Method | Endpoint | Description |
| `GET` | `/api/organizations/` | Public list of organizations for UI switcher. |
| `POST` | `/api/bank-statements/import/` | Upload and validate bank CSV, run matching engine. |
| `GET` | `/api/transactions/` | List transactions with proposed matches and reasons (newest first). |
| `GET` | `/api/line-items/` | List capital call line items with funding status and balances. |
| `POST` | `/api/matches/<id>/approve/` | Atomically approve match, lock records with `select_for_update`, fund line item. |
| `POST` | `/api/matches/<id>/reject/` | Reject match, transition transaction to `needs_review` if no matches remain. |
| `POST` | `/api/transactions/<id>/ignore/` | Mark transaction as ignored and reject linked proposed matches. |

---

## 5. Assumptions, Trade-offs & Next Steps

### Assumptions
- Ingestion occurs synchronously during the upload request for files of typical statement size (up to a few thousand rows).
- Currency amounts are stored in fixed-point `Decimal` with two fractional digits.
- Line items are not funded beyond their called amounts; overpayments remain in `needs_review`.

### Trade-offs
- Concurrency protection relies on PostgreSQL row-level locking (`select_for_update()`) inside atomic transactions. This guarantees double-funding prevention under concurrent requests while maintaining low complexity without external distributed lock managers.
- Matching calculations are executed once during statement import. Approvals perform real-time verification against the latest remaining balance to catch changes that occurred between import and approval.

### Next Steps
- Implement batch reconciliation actions for bulk approval of high-confidence suggested matches.
- Add CSV export of reconciled line items and audit logs for accounting exports.
- Integrate asynchronous task workers for multi-megabyte statement files.

---

> I completed this assessment without using AI assistance.
