import io
from decimal import Decimal
from datetime import date
from rest_framework.test import APITestCase
from rest_framework import status

from core.models import Organization, CapitalCall, LineItem, Transaction, MatchSuggestion


class BankReconciliationTests(APITestCase):

    def setUp(self):
        self.northwind = Organization.objects.create(name="Northwind Ventures", slug="northwind")
        self.nw_call1 = CapitalCall.objects.create(
            organization=self.northwind,
            call_number=1,
            call_date=date(2026, 3, 25),
            due_date=date(2026, 4, 10)
        )
        self.nw_item1 = LineItem.objects.create(
            organization=self.northwind,
            capital_call=self.nw_call1,
            investor_name="Haller Capital LLC",
            wire_reference="CC-1001",
            amount_called=Decimal("27500.00"),
            amount_funded=Decimal("0.00"),
            status=LineItem.STATUS_OPEN
        )
        self.nw_item2 = LineItem.objects.create(
            organization=self.northwind,
            capital_call=self.nw_call1,
            investor_name="Patel Family Trust",
            wire_reference="CC-1003",
            amount_called=Decimal("12500.00"),
            amount_funded=Decimal("0.00"),
            status=LineItem.STATUS_OPEN
        )

        self.bluebird = Organization.objects.create(name="Bluebird Capital", slug="bluebird")
        self.bb_call1 = CapitalCall.objects.create(
            organization=self.bluebird,
            call_number=1,
            call_date=date(2026, 4, 1),
            due_date=date(2026, 4, 15)
        )
        self.bb_item1 = LineItem.objects.create(
            organization=self.bluebird,
            capital_call=self.bb_call1,
            investor_name="Cedar Grove Fund LP",
            wire_reference="CC-2001",
            amount_called=Decimal("40000.00"),
            amount_funded=Decimal("0.00"),
            status=LineItem.STATUS_OPEN
        )

    def test_missing_column_rejects_and_saves_nothing(self):
        csv_content = "date,description,amount,type\n2026-04-03,WIRE INCOMING,25000.00,credit"
        response = self.client.post(
            '/api/bank-statements/import/',
            {'content': csv_content},
            format='json',
            headers={'X-Organization': 'northwind'}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Missing required column", response.data['error'])
        self.assertEqual(Transaction.objects.count(), 0)

    def test_amount_and_date_parsing_and_decimal_type(self):
        csv_content = (
            "date,description,amount,type,reference\n"
            '2026-04-03,WIRE INCOMING,"25,000.00",credit,FT20260403A\n'
            '2026-04-31,WIRE INCOMING MERIDIAN,500.00,credit,FT20260431L\n'
            '2026-04-17,ACH CREDIT OAKRIDGE,-15000.00,credit,ACH20260417M\n'
        )
        response = self.client.post(
            '/api/bank-statements/import/',
            {'content': csv_content},
            format='json',
            headers={'X-Organization': 'northwind'}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['imported_count'], 1)
        self.assertEqual(len(response.data['errors']), 2)

        error_lines = [err['line'] for err in response.data['errors']]
        self.assertIn(3, error_lines)
        self.assertIn(4, error_lines)

        tx = Transaction.objects.get(bank_reference="FT20260403A")
        self.assertIsInstance(tx.amount, Decimal)
        self.assertEqual(tx.amount, Decimal("25000.00"))

    def test_duplicates_handling_within_file_and_reupload(self):
        csv_content = (
            "date,description,amount,type,reference\n"
            '2026-04-03,WIRE INCOMING,25000.00,credit,DUP_REF_01\n'
            '2026-04-03,WIRE INCOMING,25000.00,credit,DUP_REF_01\n'
        )
        res1 = self.client.post(
            '/api/bank-statements/import/',
            {'content': csv_content},
            format='json',
            headers={'X-Organization': 'northwind'}
        )
        self.assertEqual(res1.data['imported_count'], 1)
        self.assertEqual(res1.data['duplicate_count'], 1)

        res2 = self.client.post(
            '/api/bank-statements/import/',
            {'content': csv_content},
            format='json',
            headers={'X-Organization': 'northwind'}
        )
        self.assertEqual(res2.data['imported_count'], 0)
        self.assertEqual(res2.data['duplicate_count'], 2)

    def test_reference_matching_and_partial_payment(self):
        csv_content = (
            "date,description,amount,type,reference\n"
            "2026-04-04,ACH CREDIT HALLER CAPITAL cc1001,20000.00,credit,ACH20260404B\n"
        )
        response = self.client.post(
            '/api/bank-statements/import/',
            {'content': csv_content},
            format='json',
            headers={'X-Organization': 'northwind'}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        tx = Transaction.objects.get(bank_reference="ACH20260404B")
        self.assertEqual(tx.status, Transaction.STATUS_SUGGESTED)
        self.assertEqual(tx.matches.count(), 1)

        match = tx.matches.first()
        self.assertEqual(match.line_item, self.nw_item1)
        self.assertEqual(match.status, MatchSuggestion.STATUS_PROPOSED)
        self.assertIn("partial payment", match.reason.lower())

    def test_name_and_exact_amount_matching(self):
        csv_content = (
            "date,description,amount,type,reference\n"
            "2026-04-07,WIRE INCOMING PATEL FAMILY TRUST,12500.00,credit,FT20260407C\n"
        )
        self.client.post(
            '/api/bank-statements/import/',
            {'content': csv_content},
            format='json',
            headers={'X-Organization': 'northwind'}
        )
        tx = Transaction.objects.get(bank_reference="FT20260407C")
        self.assertEqual(tx.status, Transaction.STATUS_SUGGESTED)
        self.assertEqual(tx.matches.first().line_item, self.nw_item2)

        LineItem.objects.create(
            organization=self.northwind,
            capital_call=self.nw_call1,
            investor_name="Patel Family Trust",
            wire_reference="CC-1099",
            amount_called=Decimal("12500.00"),
            amount_funded=Decimal("0.00"),
            status=LineItem.STATUS_OPEN
        )
        csv_content_multi = (
            "date,description,amount,type,reference\n"
            "2026-04-07,WIRE INCOMING PATEL FAMILY TRUST,12500.00,credit,FT20260407D\n"
        )
        self.client.post(
            '/api/bank-statements/import/',
            {'content': csv_content_multi},
            format='json',
            headers={'X-Organization': 'northwind'}
        )
        tx_multi = Transaction.objects.get(bank_reference="FT20260407D")
        self.assertEqual(tx_multi.status, Transaction.STATUS_NEEDS_REVIEW)
        self.assertEqual(tx_multi.matches.count(), 2)

    def test_overpayment_creates_no_match(self):
        csv_content = (
            "date,description,amount,type,reference\n"
            "2026-04-15,WIRE INCOMING PATEL FAMILY TRUST CC-1003,13000.00,credit,FT20260415J\n"
        )
        self.client.post(
            '/api/bank-statements/import/',
            {'content': csv_content},
            format='json',
            headers={'X-Organization': 'northwind'}
        )
        tx = Transaction.objects.get(bank_reference="FT20260415J")
        self.assertEqual(tx.status, Transaction.STATUS_NEEDS_REVIEW)
        self.assertEqual(tx.matches.count(), 0)
        self.assertIn("Overpayment", tx.review_reason)

    def test_approving_updates_funding_and_prevents_double_funding(self):
        tx = Transaction.objects.create(
            organization=self.northwind,
            date=date(2026, 4, 3),
            description="WIRE INCOMING REF CC-1003",
            amount=Decimal("12500.00"),
            transaction_type=Transaction.TYPE_CREDIT,
            bank_reference="TX_APPROVE_01",
            status=Transaction.STATUS_SUGGESTED
        )
        match = MatchSuggestion.objects.create(
            transaction=tx,
            line_item=self.nw_item2,
            status=MatchSuggestion.STATUS_PROPOSED,
            reason="Exact match"
        )

        res1 = self.client.post(
            f'/api/matches/{match.id}/approve/',
            headers={'X-Organization': 'northwind'}
        )
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        self.nw_item2.refresh_from_db()
        tx.refresh_from_db()
        self.assertEqual(self.nw_item2.amount_funded, Decimal("12500.00"))
        self.assertEqual(self.nw_item2.status, LineItem.STATUS_FUNDED)
        self.assertEqual(tx.status, Transaction.STATUS_RECONCILED)

        res2 = self.client.post(
            f'/api/matches/{match.id}/approve/',
            headers={'X-Organization': 'northwind'}
        )
        self.assertEqual(res2.status_code, status.HTTP_409_CONFLICT)

        self.nw_item2.refresh_from_db()
        self.assertEqual(self.nw_item2.amount_funded, Decimal("12500.00"))

    def test_organization_isolation(self):
        res_no_header = self.client.get('/api/transactions/')
        self.assertEqual(res_no_header.status_code, status.HTTP_400_BAD_REQUEST)

        res_unknown = self.client.get('/api/transactions/', headers={'X-Organization': 'unknown_firm'})
        self.assertEqual(res_unknown.status_code, status.HTTP_404_NOT_FOUND)

        tx_nw = Transaction.objects.create(
            organization=self.northwind,
            date=date(2026, 4, 3),
            description="Northwind wire",
            amount=Decimal("1000.00"),
            transaction_type=Transaction.TYPE_CREDIT,
            bank_reference="TX_NW_ONLY"
        )
        match_nw = MatchSuggestion.objects.create(
            transaction=tx_nw,
            line_item=self.nw_item1,
            status=MatchSuggestion.STATUS_PROPOSED,
            reason="test"
        )

        res_bb_list = self.client.get('/api/transactions/', headers={'X-Organization': 'bluebird'})
        self.assertEqual(res_bb_list.status_code, status.HTTP_200_OK)
        tx_ids = [item['id'] for item in res_bb_list.data]
        self.assertNotIn(tx_nw.id, tx_ids)

        res_cross_approve = self.client.post(
            f'/api/matches/{match_nw.id}/approve/',
            headers={'X-Organization': 'bluebird'}
        )
        self.assertEqual(res_cross_approve.status_code, status.HTTP_404_NOT_FOUND)
