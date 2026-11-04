
from datetime import timedelta

import pandas as pd


def detect_structuring(
    transactions: pd.DataFrame,
    threshold: float,
    window_hours: int,
    min_transaction_count: int,
) -> list[dict]:
    """
    Detect potential structuring patterns using deterministic rules.
    """

    required_columns = {
        "txn_id",
        "account_id",
        "amount",
        "direction",
        "timestamp",
    }

    missing_columns = required_columns - set(transactions.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    if threshold <= 0:
        raise ValueError("Threshold must be positive.")

    if window_hours <= 0:
        raise ValueError("Window hours must be positive.")

    if min_transaction_count < 2:
        raise ValueError("Minimum transaction count must be at least 2.")

    df = transactions.copy()

    # Normalize transaction data
    df["direction"] = (
        df["direction"].astype(str).str.strip().str.lower()
    )

    df["amount"] = pd.to_numeric(
        df["amount"], errors="coerce"
    )

    df["timestamp"] = pd.to_datetime(
        df["timestamp"], errors="coerce", utc=True
    )

    # Filter eligible credit transactions
    df = df[
        (df["direction"] == "credit")
        & (df["amount"] > 0)
        & (df["amount"] < threshold)
        & df["timestamp"].notna()
        & df["account_id"].notna()
        & df["txn_id"].notna()
    ].copy()

    results = []
    window = timedelta(hours=window_hours)

    # Process each account independently
    for account_id, account_df in df.groupby("account_id"):

        account_df = account_df.sort_values(
            ["timestamp", "txn_id"]
        ).reset_index(drop=True)

        rows = account_df.to_dict("records")
        n = len(rows)

        # Check rolling windows
        for start in range(n):

            total = 0.0
            selected = []

            start_time = rows[start]["timestamp"]
            window_end = start_time + window

            for end in range(start, n):

                current = rows[end]

                if current["timestamp"] > window_end:
                    break

                total += float(current["amount"])
                selected.append(current)

                count = len(selected)

                # Check detection conditions
                if (
                    count >= min_transaction_count
                    and total > threshold
                ):

                    results.append({
                        "account_id": str(account_id),
                        "transaction_ids": [
                            str(row["txn_id"])
                            for row in selected
                        ],
                        "transaction_count": count,
                        "total_amount": round(total, 2),
                        "threshold": float(threshold),
                        "window_hours": window_hours,
                        "window_start": start_time.isoformat(),
                        "window_end": current["timestamp"].isoformat(),
                    })

                    # Keep shortest qualifying prefix for this start
                    break

    # Remove duplicate patterns
    unique_results = []
    seen = set()

    for result in results:

        key = (
            result["account_id"],
            tuple(result["transaction_ids"]),
        )

        if key not in seen:
            seen.add(key)
            unique_results.append(result)

    return unique_results
