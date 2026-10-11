from decimal import Decimal
from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class CapitalCall(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='capital_calls')
    call_number = models.PositiveIntegerField()
    call_date = models.DateField()
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('organization', 'call_number')
        ordering = ['call_number']

    def __str__(self):
        return f"{self.organization.slug} - Call #{self.call_number}"


class LineItem(models.Model):
    STATUS_OPEN = 'open'
    STATUS_PARTIALLY_FUNDED = 'partially_funded'
    STATUS_FUNDED = 'funded'

    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_PARTIALLY_FUNDED, 'Partially Funded'),
        (STATUS_FUNDED, 'Funded'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='line_items')
    capital_call = models.ForeignKey(CapitalCall, on_delete=models.CASCADE, related_name='line_items')
    investor_name = models.CharField(max_length=255)
    wire_reference = models.CharField(max_length=100)
    amount_called = models.DecimalField(max_digits=15, decimal_places=2)
    amount_funded = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['capital_call__call_number', 'investor_name']

    @property
    def amount_remaining(self):
        return max(Decimal('0.00'), self.amount_called - self.amount_funded)

    def __str__(self):
        return f"{self.investor_name} ({self.wire_reference}) - {self.amount_called}"


class Transaction(models.Model):
    TYPE_CREDIT = 'credit'
    TYPE_DEBIT = 'debit'

    TYPE_CHOICES = [
        (TYPE_CREDIT, 'Credit'),
        (TYPE_DEBIT, 'Debit'),
    ]

    STATUS_SUGGESTED = 'suggested'
    STATUS_NEEDS_REVIEW = 'needs_review'
    STATUS_RECONCILED = 'reconciled'
    STATUS_IGNORED = 'ignored'

    STATUS_CHOICES = [
        (STATUS_SUGGESTED, 'Suggested'),
        (STATUS_NEEDS_REVIEW, 'Needs Review'),
        (STATUS_RECONCILED, 'Reconciled'),
        (STATUS_IGNORED, 'Ignored'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='transactions')
    date = models.DateField()
    description = models.CharField(max_length=500)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    bank_reference = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEEDS_REVIEW)
    review_reason = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('organization', 'bank_reference')
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.date} {self.bank_reference} ({self.amount})"


class MatchSuggestion(models.Model):
    STATUS_PROPOSED = 'proposed'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PROPOSED, 'Proposed'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='matches')
    line_item = models.ForeignKey(LineItem, on_delete=models.CASCADE, related_name='matches')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PROPOSED)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Match {self.transaction.bank_reference} -> {self.line_item.wire_reference} ({self.status})"
