# CapRecon

**Capital Call Bank Reconciliation Portal**

A full-stack multi-tenant web application designed for private equity funds to reconcile incoming bank statement transactions against investor capital call notices.

---

## Tech Stack

- **Backend**: Python 3.11+, Django 6, Django REST Framework, PostgreSQL
- **Frontend**: React 19, Vite, Vanilla CSS
- **Integrations**: Airtable REST API (optional sync for review items)

---

## Features

- **Multi-Tenant Isolation**: Complete data separation per organization (e.g. `Northwind Ventures`, `Bluebird Capital`) scoped via the `X-Organization` header.
- **CSV Ingestion & Validation**: Header validation, date integrity checks, amount formatting (commas, signs, decimals), and duplicate detection (intra-file and re-upload).
- **Matching Engine**:
  1. Exact wire reference matching (case-insensitive, normalizing prefixes like `CC-`).
  2. Investor name matching with legal suffix stripping (`LLC`, `LP`) and amount matching.
  3. Overpayment detection routing directly to review.
- **Atomic Reconciliation**: Concurrency-safe approval workflows using PostgreSQL `select_for_update()` row locks to prevent double-funding race conditions.
- **Airtable Sync (Bonus)**: Automatically sends `needs_review` items to an external Airtable base with fail-safe error isolation.

---

## Quickstart

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL running locally on port 5432

---

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Run database migrations
python manage.py migrate

# Seed initial demo data (organizations and capital calls)
python manage.py seed_demo

# Start the API server
python manage.py runserver 8000
```

> **Tip**: Run `python manage.py seed_demo --reset` anytime to wipe transactions and reset line item balances.

---

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```

Open your browser at `http://localhost:5173/`.

---

## Testing

Run the automated test suite from the `backend/` directory:

```bash
python manage.py test
```

Includes 10 unit tests covering CSV validation, duplicate detection, matching rules, atomic double-funding locks, multi-tenant isolation, and Airtable synchronization.

---

## Documentation

For detailed architectural decisions, trade-offs, data model specifications, and endpoint references, see [ASSESSMENT_NOTES.md](file:///c:/Users/harje/Downloads/DAP/ASSESSMENT_NOTES.md).
