from rest_framework import serializers
from core.models import Organization, CapitalCall, LineItem, Transaction, MatchSuggestion


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'slug']


class LineItemSerializer(serializers.ModelSerializer):
    amount_remaining = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    capital_call_number = serializers.IntegerField(source='capital_call.call_number', read_only=True)
    capital_call_due_date = serializers.DateField(source='capital_call.due_date', read_only=True)

    class Meta:
        model = LineItem
        fields = [
            'id', 'capital_call_number', 'capital_call_due_date',
            'investor_name', 'wire_reference', 'amount_called',
            'amount_funded', 'amount_remaining', 'status'
        ]


class MatchSuggestionSerializer(serializers.ModelSerializer):
    investor_name = serializers.CharField(source='line_item.investor_name', read_only=True)
    wire_reference = serializers.CharField(source='line_item.wire_reference', read_only=True)
    amount_called = serializers.DecimalField(source='line_item.amount_called', max_digits=15, decimal_places=2, read_only=True)
    amount_remaining = serializers.DecimalField(source='line_item.amount_remaining', max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = MatchSuggestion
        fields = [
            'id', 'line_item', 'investor_name', 'wire_reference',
            'amount_called', 'amount_remaining', 'status', 'reason'
        ]


class TransactionSerializer(serializers.ModelSerializer):
    matches = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            'id', 'date', 'description', 'amount', 'transaction_type',
            'bank_reference', 'status', 'review_reason', 'matches'
        ]

    def get_matches(self, obj):
        # Return all matches (proposed, approved, rejected)
        return MatchSuggestionSerializer(obj.matches.all(), many=True).data
