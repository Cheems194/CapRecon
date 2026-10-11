from decimal import Decimal
from datetime import date
from django.core.management.base import BaseCommand
from core.models import Organization, CapitalCall, LineItem


class Command(BaseCommand):
    help = "Seeds initial demo organizations, capital calls, and line items."

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")

        # 1. Organizations
        northwind, _ = Organization.objects.get_or_create(
            slug="northwind",
            defaults={"name": "Northwind Ventures"}
        )
        bluebird, _ = Organization.objects.get_or_create(
            slug="bluebird",
            defaults={"name": "Bluebird Capital"}
        )

        # 2. Capital Calls
        nw_call1, _ = CapitalCall.objects.get_or_create(
            organization=northwind,
            call_number=1,
            defaults={
                "call_date": date(2026, 3, 25),
                "due_date": date(2026, 4, 10),
            }
        )
        nw_call2, _ = CapitalCall.objects.get_or_create(
            organization=northwind,
            call_number=2,
            defaults={
                "call_date": date(2026, 4, 1),
                "due_date": date(2026, 4, 20),
            }
        )
        bb_call1, _ = CapitalCall.objects.get_or_create(
            organization=bluebird,
            call_number=1,
            defaults={
                "call_date": date(2026, 4, 1),
                "due_date": date(2026, 4, 15),
            }
        )

        # 3. Line Items
        line_items_data = [
            # Northwind Call #1
            {
                "org": northwind,
                "call": nw_call1,
                "investor": "Haller Capital LLC",
                "reference": "CC-1001",
                "amount": Decimal("27500.00"),
            },
            {
                "org": northwind,
                "call": nw_call1,
                "investor": "Rahul Shah Trust",
                "reference": "CC-1002",
                "amount": Decimal("25000.00"),
            },
            {
                "org": northwind,
                "call": nw_call1,
                "investor": "Patel Family Trust",
                "reference": "CC-1003",
                "amount": Decimal("12500.00"),
            },
            {
                "org": northwind,
                "call": nw_call1,
                "investor": "Meridian Partners LP",
                "reference": "CC-1004",
                "amount": Decimal("15000.00"),
            },
            {
                "org": northwind,
                "call": nw_call1,
                "investor": "Oakridge Holdings LLC",
                "reference": "CC-1005",
                "amount": Decimal("15000.00"),
            },
            # Northwind Call #2
            {
                "org": northwind,
                "call": nw_call2,
                "investor": "Oakridge Holdings LLC",
                "reference": "CC-1006",
                "amount": Decimal("15000.00"),
            },
            # Bluebird Call #1
            {
                "org": bluebird,
                "call": bb_call1,
                "investor": "Cedar Grove Fund LP",
                "reference": "CC-2001",
                "amount": Decimal("40000.00"),
            },
        ]

        # Seed each line item
        for item in line_items_data:
            LineItem.objects.update_or_create(
                organization=item["org"],
                wire_reference=item["reference"],
                defaults={
                    "capital_call": item["call"],
                    "investor_name": item["investor"],
                    "amount_called": item["amount"],
                    "amount_funded": Decimal("0.00"),
                    "status": LineItem.STATUS_OPEN,
                }
            )

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully!"))
