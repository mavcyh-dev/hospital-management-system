import csv
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

INPUT_FILE = SCRIPT_DIR / "RxTerms202512.txt"
OUTPUT_FILE = SCRIPT_DIR / "medications.json"


def clean_name(name: str) -> str:
    """Basic cleanup: strip whitespace & collapse interior spacing."""
    if not name:
        return ""
    # Remove leading/trailing whitespace
    name = name.strip()
    # Replace multiple spaces with single space
    while "  " in name:
        name = name.replace("  ", " ")
    return name


def extract_medications(input_path: Path):
    medications = {}
    # medications will be a dict: {generic_name: is_in_service}

    with open(input_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="|")

        for row in reader:
            full_generic = clean_name(row.get("FULL_GENERIC_NAME", ""))
            if not full_generic:
                continue  # skip empty

            # Retired: 1 → inactive
            is_retired = row.get("IS_RETIRED", "").strip()
            is_in_service = is_retired != "1"

            # Deduplicate by name, keeping the "active" version if any exist
            if full_generic not in medications:
                medications[full_generic] = is_in_service
            else:
                # If any entry is active, mark name as active
                medications[full_generic] = medications[full_generic] or is_in_service

    # Convert to JSON list format
    output_list = [
        {"generic_name": name, "is_in_service": flag}
        for name, flag in sorted(medications.items())
    ]

    return output_list


def main():
    meds = extract_medications(INPUT_FILE)
    print(f"Extracted {len(meds)} unique medications.")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(meds, f, indent=2, ensure_ascii=False)
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
