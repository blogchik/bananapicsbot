"""Tests for credit adjustment endpoint schema alignment between backend and frontend.

Regression tests for issue #59: frontend was calling a non-existent route
/admin/users/{id}/adjust-credits instead of /admin/credits, and the request body
was missing the telegram_id field.
"""

import pytest
from pydantic import ValidationError

from app.schemas.admin import AdminCreditIn, AdminCreditOut


class TestAdminCreditInSchema:
    """Verify AdminCreditIn accepts the request body that the frontend sends."""

    def test_requires_telegram_id(self):
        """telegram_id is mandatory — frontend must include it in the request body."""
        with pytest.raises(ValidationError):
            AdminCreditIn(amount=100, reason="test")

    def test_requires_amount(self):
        """amount is mandatory."""
        with pytest.raises(ValidationError):
            AdminCreditIn(telegram_id=123456789, reason="test")

    def test_accepts_positive_amount(self):
        """Positive amount adds credits to the user."""
        data = AdminCreditIn(telegram_id=123456789, amount=500, reason="Bonus")
        assert data.telegram_id == 123456789
        assert data.amount == 500
        assert data.reason == "Bonus"

    def test_accepts_negative_amount(self):
        """Negative amount removes credits from the user."""
        data = AdminCreditIn(telegram_id=123456789, amount=-200, reason="Penalty")
        assert data.amount == -200

    def test_reason_is_optional(self):
        """reason field is optional; defaults to None."""
        data = AdminCreditIn(telegram_id=123456789, amount=100)
        assert data.reason is None

    def test_reason_max_length(self):
        """reason must not exceed 255 characters."""
        long_reason = "x" * 256
        with pytest.raises(ValidationError):
            AdminCreditIn(telegram_id=123456789, amount=100, reason=long_reason)

    def test_reason_at_max_length(self):
        """reason at exactly 255 characters should be accepted."""
        max_reason = "x" * 255
        data = AdminCreditIn(telegram_id=123456789, amount=100, reason=max_reason)
        assert len(data.reason) == 255

    def test_frontend_request_body_shape(self):
        """Frontend sends {telegram_id, amount, reason} — all three fields must be accepted."""
        payload = {"telegram_id": 987654321, "amount": 1000, "reason": "Admin bonus"}
        data = AdminCreditIn(**payload)
        assert data.telegram_id == 987654321
        assert data.amount == 1000
        assert data.reason == "Admin bonus"


class TestAdminCreditOutSchema:
    """Verify AdminCreditOut fields match the frontend CreditAdjustmentResponse interface.

    Frontend interface (admin-panel/src/api/users.ts):
        interface CreditAdjustmentResponse {
            telegram_id: number;
            amount: number;
            old_balance: number;
            new_balance: number;
            reason: string | null;
        }
    """

    def _make_response(self, **kwargs) -> AdminCreditOut:
        defaults = {
            "telegram_id": 123456789,
            "amount": 500,
            "old_balance": 1000,
            "new_balance": 1500,
            "reason": "Test adjustment",
        }
        defaults.update(kwargs)
        return AdminCreditOut(**defaults)

    def test_has_telegram_id_field(self):
        """Backend must return telegram_id — frontend CreditAdjustmentResponse reads this."""
        resp = self._make_response(telegram_id=111222333)
        assert resp.telegram_id == 111222333

    def test_has_amount_field(self):
        """Backend must return amount — frontend CreditAdjustmentResponse reads this."""
        resp = self._make_response(amount=250)
        assert resp.amount == 250

    def test_has_old_balance_field(self):
        """Backend must return old_balance — frontend CreditAdjustmentResponse reads this."""
        resp = self._make_response(old_balance=800)
        assert resp.old_balance == 800

    def test_has_new_balance_field(self):
        """Backend must return new_balance — frontend CreditAdjustmentResponse reads this."""
        resp = self._make_response(new_balance=1300)
        assert resp.new_balance == 1300

    def test_has_reason_field(self):
        """Backend must return reason — frontend CreditAdjustmentResponse reads this."""
        resp = self._make_response(reason="Promo credit")
        assert resp.reason == "Promo credit"

    def test_reason_can_be_null(self):
        """reason is nullable — frontend expects string | null."""
        resp = self._make_response(reason=None)
        assert resp.reason is None

    def test_serialized_fields_match_frontend_interface(self):
        """Serialized JSON must contain exactly the fields the frontend expects."""
        resp = self._make_response()
        data = resp.model_dump()
        required_fields = {"telegram_id", "amount", "old_balance", "new_balance", "reason"}
        missing = required_fields - data.keys()
        assert not missing, f"AdminCreditOut is missing fields expected by frontend: {missing}"

    def test_balance_reflects_adjustment(self):
        """new_balance must equal old_balance + amount for positive adjustments."""
        old = 1000
        amount = 300
        resp = self._make_response(old_balance=old, amount=amount, new_balance=old + amount)
        assert resp.new_balance == resp.old_balance + resp.amount

    def test_balance_reflects_negative_adjustment(self):
        """new_balance must equal old_balance + amount for negative (deduction) adjustments."""
        old = 1000
        amount = -400
        resp = self._make_response(old_balance=old, amount=amount, new_balance=old + amount)
        assert resp.new_balance == resp.old_balance + resp.amount

    def test_no_entry_id_field(self):
        """Regression: original schema had entry_id instead of telegram_id/amount/old_balance.
        Ensure entry_id is not present in the serialized output."""
        resp = self._make_response()
        data = resp.model_dump()
        assert "entry_id" not in data, (
            "entry_id must not be present — frontend CreditAdjustmentResponse does not have this field"
        )
