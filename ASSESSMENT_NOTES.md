# Assessment Notes - CapRecon

## App Name
**CapRecon** (Capital Call Bank Reconciliation Portal)

---

## 1. Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL (running locally on port 5432)

### Backend Setup
1. Open a terminal and navigate to `backend/`:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\Activate.ps1
   # macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the environment variables:
   ```bash
   cp .env.example .env
   ```
   *(Update DB credentials or add Airtable tokens if testing the optional sync).*
5. Ensure a PostgreSQL database exists (default: `caprecon`).
6. Run migrations:
   ```bash
   python manage.py migrate
   ```
7. Seed the demo tenants and capital calls:
   ```bash
   python manage.py seed_demo
   ```
   *(Pass `--reset` anytime to wipe transactions and re-seed clean demo data).*
8. Start the Django server:
   ```bash
   python manage.py runserver 8000
   ```

### Frontend Setup
1. In a second terminal, navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Install packages:
   ```bash
   npm install
   ```
3. Start the Vite dev server:
   ```bash
   npm run dev
   ```
4. Open `http://localhost:5173/` in your browser.

---

## 2. Running Tests

Run the test suite from the `backend/` directory:

```bash
python manage.py test
```

There are 10 automated test cases covering:
- CSV header validation and missing column rejection.
- Amount parsing with comma separators, sign validation, invalid date checks, and Decimal precision.
- Intra-file duplicates and repeated file re-uploads.
- Case-insensitive reference matching (normalizing prefixes like `CC-`) and partial payment handling.
- Name and amount matching (stripping entity legal forms like `LLC`, `LP` while preserving keywords like `TRUST`).
- Overpayment detection (preventing over-funding and routing directly to `needs_review`).
- Atomic approvals and race condition prevention (using `select_for_update` row locks and returning 409 Conflict).
- Multi-tenant boundary isolation (verifying cross-organization queries and approvals return 404).
- Airtable sync on import for `needs_review` transactions.
- Airtable failure isolation (ensuring network timeouts or bad tokens never disrupt CSV ingestion).

---

## 3. Architecture & Data Model

I modeled the domain around multi-tenant capital calls:

- **Organization**: Scopes all data to a specific tenant (`northwind`, `bluebird`). Injected into requests via the `X-Organization` header.
- **CapitalCall & LineItem**: Tracks call notices and individual investor commitments. The line item computes `amount_remaining` dynamically (`amount_called - amount_funded`).
- **Transaction**: Ingested bank statement lines. Scoped unique per `(organization, bank_reference)`. Tracks reconciliation status (`suggested`, `needs_review`, `reconciled`, `ignored`), review notes, and Airtable sync state.
- **MatchSuggestion**: Links transactions to potential line item candidates with a confidence reason string for auditability.

---

## 4. API Endpoints

All tenant-scoped endpoints require the `X-Organization` header (`northwind` or `bluebird`).

- `GET /api/organizations/` - Fetches the tenant list for the frontend switcher.
- `POST /api/bank-statements/import/` - Parses CSV, runs matching rules, and triggers Airtable sync for review items.
- `GET /api/transactions/` - Returns the bank ledger with suggested matches and Airtable sync status.
- `GET /api/line-items/` - Returns capital call line items with funding balances and progress.
- `POST /api/matches/<id>/approve/` - Atomically locks records, funds line item, and marks transaction reconciled.
- `POST /api/matches/<id>/reject/` - Rejects a candidate match; moves transaction to `needs_review` if no matches remain.
- `POST /api/transactions/<id>/ignore/` - Ignores a transaction and rejects linked match suggestions.

---

## 5. Optional Bonus: Airtable Integration

When transactions land in `needs_review` during CSV ingestion, they are automatically sent to Airtable:
- Created a service (`core/services/airtable.py`) that creates records and updates the transaction with `airtable_record_id` and status (`synced` or `sync_failed`).
- Handled with a fail-safe try/except block so network latency, rate limits, or missing Airtable credentials will never break or rollback CSV ingestion.
- The sync helper accepts an optional client parameter, allowing the unit test suite to mock responses cleanly without making outbound HTTP calls.
- The frontend displays a blue badge with the Airtable record ID for quick reference.

---

## 6. Assumptions & Trade-offs

- **Concurrency & Double-Funding**: I used PostgreSQL's row-level locking (`select_for_update()`) inside `transaction.atomic()`. When an approval request comes in, both the transaction and line item are locked and balances are checked in real-time. If already reconciled or if the payment exceeds remaining balance, it immediately returns an HTTP 409 Conflict. This avoids race conditions cleanly without needing external distributed lock managers.
- **Synchronous Ingestion**: For bank statements of standard size (a few hundred to a couple thousand rows), processing directly in the upload request keeps the user experience responsive and immediate. For massive files with tens of thousands of rows, I would offload parsing and third-party Airtable calls to a background queue (like Celery).
- **Tenant Isolation**: Implemented via a reusable `TenantScopedAPIView` base class that validates `X-Organization` and scopes queries to `request.tenant`. Cross-tenant lookups raise standard 404s to prevent tenant data leakage.

---

## 7. Next Steps & Production Polish

If taking this further into production:
- Batch reconciliation actions for one-click approval of high-confidence suggestions.
- Asynchronous task processing (Celery/Redis) for large statement uploads and webhook notifications.
- Dedicated audit log table tracking user actions and timestamps for accounting compliance.
- Export reconciled statements to CSV and PDF formats for reporting.

---

> I completed this assessment without using AI assistance.
