from typing import Any
import json
from pathlib import Path
from sqlalchemy import insert
from sqlalchemy.orm import Session

from app.database.models import Medication


MEDICATIONS_JSON = Path(__file__).resolve().parent / "data" / "medications.json"


def seed_medications(session: Session) -> None:
    if not MEDICATIONS_JSON.exists():
        raise FileNotFoundError(f"Medication seed file not found: {MEDICATIONS_JSON}")

    with open(MEDICATIONS_JSON, "r", encoding="utf-8") as f:
        medications_data = json.load(f)

    if not isinstance(medications_data, list):
        raise ValueError("medications.json must contain a JSON list")

    # Deduplicate just in case
    seen = set()
    unique_records = []
    for record in medications_data:
        name = record.get("generic_name")
        if name not in seen:
            seen.add(name)
            unique_records.append(record)

    # SQLAlchemy 2.0: use Core insert() for type-safe bulk operations
    stmt = insert(Medication)
    session.execute(
        stmt,
        [
            {
                "generic_name": record["generic_name"],
                "is_in_service": record.get("is_in_service", True),
            }
            for record in unique_records
        ],
    )

    print(f"[seed] Inserted {len(unique_records)} medications.")
