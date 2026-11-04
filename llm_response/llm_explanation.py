
import json
import os
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from groq import Groq


# Load .env from the project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_PATH)

MODEL_NAME = "openai/gpt-oss-20b"


def generate_explanation(evidence: dict) -> str:
    """
    Generate an analyst-readable explanation using only
    deterministic evidence returned by the structuring detector.

    The LLM does not detect patterns or make alert decisions.
    """

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print("[LLM] API key not configured. Skipping API call.")
        return "LLM explanation unavailable: API key not configured."

    # Send only detector-generated evidence to the LLM
    evidence_payload = {
        "account_id": evidence["account_id"],
        "transaction_ids": evidence["transaction_ids"],
        "transaction_count": evidence["transaction_count"],
        "total_amount": evidence["total_amount"],
        "threshold": evidence["threshold"],
        "window_hours": evidence["window_hours"],
        "window_start": evidence["window_start"],
        "window_end": evidence["window_end"],
    }

    # Calculate actual duration deterministically in Python
    start = datetime.fromisoformat(
        evidence["window_start"].replace("Z", "+00:00")
    )
    end = datetime.fromisoformat(
        evidence["window_end"].replace("Z", "+00:00")
    )

    actual_duration_hours = (
        end - start
    ).total_seconds() / 3600

    evidence_payload["actual_duration_hours"] = actual_duration_hours

    prompt = f"""
    Explain the following pre-detected transaction pattern
    for a financial compliance analyst.

    Evidence:
    {json.dumps(evidence_payload, indent=2)}

    Instructions:
    - Write one clear, professional paragraph of 3-4 sentences.
    - Use INR (₹) when mentioning amounts.
    - Mention the account ID and transaction count.
    - Explain that individual transactions were below the threshold.
    - Mention the combined amount and actual time duration.
    - Recommend further analyst review.
    - Do not perform new calculations.
    - Do not independently decide whether the account is suspicious.
    - Do not claim that a crime has occurred.
    - Return only the explanation paragraph, without a heading.
    """

    try:
        client = Groq(api_key=api_key)

        print(
            f"[LLM] Calling Groq API for account: "
            f"{evidence['account_id']}"
        )

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a financial compliance analyst. "
                        "Your task is only to explain supplied "
                        "deterministic evidence. Never detect patterns "
                        "or make alert decisions."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
        )

        explanation = response.choices[0].message.content

        if not explanation or not explanation.strip():
            print("[LLM] API returned an empty explanation.")
            return "LLM returned an empty explanation."

        print(
            f"[LLM] Groq API response received successfully "
            f"for account: {evidence['account_id']}"
        )

        return explanation.strip()

    except Exception as error:
        print(
            f"[LLM] API request failed for "
            f"{evidence['account_id']}: {type(error).__name__}"
        )

        return (
            f"LLM explanation unavailable: "
            f"{type(error).__name__}"
        )

