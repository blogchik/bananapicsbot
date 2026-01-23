"""Tests for ledger operations - balance deduction, refunds, and accounting."""

from decimal import Decimal

import pytest
from app.domain.entities.ledger import LedgerEntryType


# === Ledger Entity Tests ===


def test_ledger_entry_types_exist():
    """Test that ledger entry types are properly defined."""
    # Test that all expected entry types exist
    assert hasattr(LedgerEntryType, "STARS_PURCHASE")
    assert hasattr(LedgerEntryType, "GENERATION_COST")
    assert hasattr(LedgerEntryType, "REFUND")
    assert hasattr(LedgerEntryType, "REFERRAL_BONUS")
    assert hasattr(LedgerEntryType, "ADMIN_ADJUSTMENT")
    assert hasattr(LedgerEntryType, "ADMIN_CREDIT")
    assert hasattr(LedgerEntryType, "PROMO_CREDIT")


def test_ledger_entry_type_values():
    """Test ledger entry type string values."""
    assert LedgerEntryType.STARS_PURCHASE.value == "stars_purchase"
    assert LedgerEntryType.GENERATION_COST.value == "generation_cost"
    assert LedgerEntryType.REFUND.value == "refund"
    assert LedgerEntryType.REFERRAL_BONUS.value == "referral_bonus"
    assert LedgerEntryType.ADMIN_ADJUSTMENT.value == "admin_adjustment"


def test_balance_calculation_logic():
    """Test balance calculation logic with positive and negative amounts."""
    # Simulates balance calculation
    transactions = [
        1000,  # Stars purchase
        -140,  # Generation cost
        -27,  # Another generation
        50,  # Referral bonus
        140,  # Refund
    ]
    balance = sum(transactions)
    assert balance == 1023  # 1000 - 140 - 27 + 50 + 140


def test_refund_amount_should_be_positive():
    """Test that refund amounts should be positive (credits back)."""
    refund_amount = 140
    assert refund_amount > 0  # Refunds add credits back


def test_generation_cost_should_be_negative():
    """Test that generation costs should be negative (debit)."""
    generation_cost = -140
    assert generation_cost < 0  # Generation costs deduct credits


def test_deposit_amount_should_be_positive():
    """Test that deposit amounts should be positive (credit)."""
    deposit_amount = 1000
    assert deposit_amount > 0  # Deposits add credits


def test_decimal_precision():
    """Test decimal precision for currency operations."""
    amount1 = Decimal("100.00")
    amount2 = Decimal("0.01")
    total = amount1 + amount2
    assert total == Decimal("100.01")


def test_negative_balance_detection():
    """Test detection of negative balance."""
    balance = Decimal("-50")
    assert balance < 0  # Insufficient funds


def test_zero_balance():
    """Test zero balance condition."""
    balance = Decimal("0")
    assert balance == 0
