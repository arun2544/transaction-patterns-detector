
import json
from pathlib import Path

import pandas as pd

from detector.structuring import detect_structuring
from llm_response.llm_explanation import generate_explanation


def main():
    config_path = Path("config/config.json")
    transactions_path = Path("data/transactions.csv")
    output_path = Path("output/results.json")

    with config_path.open("r", encoding="utf-8") as file:
        config = json.load(file)

    transactions = pd.read_csv(transactions_path)

    threshold = config["reporting_threshold"]
    window_hours = config["rolling_window_hours"]
    min_count = config["min_transaction_count"]

    print(f"Loaded transactions: {len(transactions)}")
    print(f"Reporting threshold: {threshold}")
    print(f"Rolling window: {window_hours} hours")
    print(f"Minimum transaction count: {min_count}")

    # Step 1: Deterministic detection
    results = detect_structuring(
        transactions=transactions,
        threshold=threshold,
        window_hours=window_hours,
        min_transaction_count=min_count,
    )

    print(f"\nQualifying patterns found: {len(results)}")

    attempted_calls = 0
    successful_explanations = 0

    # Step 2: LLM explanation for detected patterns only
    for index, evidence in enumerate(results, start=1):

        print(
            f"\nGenerating explanation {index}/{len(results)} "
            f"for {evidence['account_id']}..."
        )

        attempted_calls += 1

        evidence["explanation"] = generate_explanation(evidence)

        if not evidence["explanation"].startswith(
            ("LLM explanation unavailable", "LLM returned")
        ):
            successful_explanations += 1

        print("\nCompliance Alert Explanation:")
        print(evidence["explanation"])
        print("-" * 80)

    if not results:
        print("No suspicious patterns detected. No LLM calls required.")

    # Step 3: Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(results, file, indent=4, ensure_ascii=False)

    flagged_accounts = {
        result["account_id"] for result in results
    }

    # Step 4: Final summary
    print("\n" + "=" * 50)
    print("PROCESSING COMPLETED")
    print("=" * 50)

    print(f"Transactions processed: {len(transactions)}")
    print(f"Patterns detected: {len(results)}")
    print(f"Unique flagged accounts: {len(flagged_accounts)}")
    print(f"LLM calls attempted: {attempted_calls}")
    print(f"Successful LLM explanations: {successful_explanations}")
    print(f"Output file: {output_path}")


if __name__ == "__main__":
    main()
