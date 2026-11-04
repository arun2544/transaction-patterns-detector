
import pandas as pd
import pytest

from detector.structuring import detect_structuring


# Helper function to create a transaction
def transaction(txn_id, account_id, amount, direction, timestamp):
    return {
        "txn_id": txn_id,
        "account_id": account_id,
        "amount": amount,
        "direction": direction,
        "timestamp": timestamp,
    }


# Helper function to run the detector with default test settings
def detect(data, threshold=50000, window_hours=24, min_count=3):
    return detect_structuring(
        transactions=pd.DataFrame(data),
        threshold=threshold,
        window_hours=window_hours,
        min_transaction_count=min_count,
    )


# Test 1: Valid structuring pattern should be detected
def test_valid_structuring_pattern():
    data = [
        transaction("T1", "A1", 15000, "credit", "2026-01-01 08:00"),
        transaction("T2", "A1", 18000, "credit", "2026-01-01 12:00"),
        transaction("T3", "A1", 20000, "credit", "2026-01-01 17:00"),
    ]

    results = detect(data)

    assert len(results) == 1
    assert results[0]["account_id"] == "A1"
    assert results[0]["transaction_count"] == 3
    assert results[0]["total_amount"] == 53000


# Test 2: Total exactly equal to threshold should not be flagged
def test_total_equal_to_threshold_not_flagged():
    data = [
        transaction("T1", "A1", 15000, "credit", "2026-01-01 08:00"),
        transaction("T2", "A1", 15000, "credit", "2026-01-01 12:00"),
        transaction("T3", "A1", 20000, "credit", "2026-01-01 17:00"),
    ]

    results = detect(data)

    assert len(results) == 0


# Test 3: Individual transaction equal to threshold is excluded
def test_individual_amount_equal_to_threshold_excluded():
    data = [
        transaction("T1", "A1", 20000, "credit", "2026-01-01 08:00"),
        transaction("T2", "A1", 15000, "credit", "2026-01-01 12:00"),
        transaction("T3", "A1", 50000, "credit", "2026-01-01 17:00"),
    ]

    results = detect(data)

    assert len(results) == 0


# Test 4: Minimum transaction count is required
def test_minimum_transaction_count_required():
    data = [
        transaction("T1", "A1", 30000, "credit", "2026-01-01 08:00"),
        transaction("T2", "A1", 25000, "credit", "2026-01-01 12:00"),
    ]

    results = detect(data, min_count=3)

    assert len(results) == 0


# Test 5: Transactions outside the rolling window must not be combined
def test_transactions_outside_window_not_combined():
    data = [
        transaction("T1", "A1", 20000, "credit", "2026-01-01 08:00"),
        transaction("T2", "A1", 20000, "credit", "2026-01-02 08:00"),
        transaction("T3", "A1", 20000, "credit", "2026-01-04 09:00"),
    ]

    results = detect(data, window_hours=72)

    assert len(results) == 0


# Test 6: Debit transactions must be excluded
def test_debit_transactions_are_excluded():
    data = [
        transaction("T1", "A1", 20000, "credit", "2026-01-01 08:00"),
        transaction("T2", "A1", 20000, "debit", "2026-01-01 12:00"),
        transaction("T3", "A1", 20000, "credit", "2026-01-01 17:00"),
    ]

    results = detect(data)

    assert len(results) == 0


# Test 7: Exact rolling-window boundary must be included
def test_exact_window_boundary_is_included():
    data = [
        transaction("T1", "A1", 20000, "credit", "2026-01-01 08:00"),
        transaction("T2", "A1", 20000, "credit", "2026-01-02 08:00"),
        transaction("T3", "A1", 20000, "credit", "2026-01-04 08:00"),
    ]

    # Explicitly use 72 hours, independent of config.json
    results = detect(
        data,
        threshold=50000,
        window_hours=72,
        min_count=3,
    )

    assert len(results) == 1
    assert results[0]["transaction_count"] == 3
    assert results[0]["total_amount"] == 60000


# Test 8: Transactions from different accounts must not be combined
def test_different_accounts_not_combined():
    data = [
        transaction("T1", "A1", 20000, "credit", "2026-01-01 08:00"),
        transaction("T2", "A2", 20000, "credit", "2026-01-01 12:00"),
        transaction("T3", "A3", 20000, "credit", "2026-01-01 17:00"),
    ]

    results = detect(data)

    assert len(results) == 0


# Test 9: Invalid threshold should raise an error
def test_invalid_threshold_rejected():
    data = [
        transaction("T1", "A1", 20000, "credit", "2026-01-01 08:00"),
    ]

    with pytest.raises(ValueError):
        detect(data, threshold=0)
