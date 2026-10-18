
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "scheme_details.json"
OUTPUT_FILE = BASE_DIR / "clean_scheme_details.json"


def clean_text(text):
    """Normalize whitespace without removing meaningful content."""
    if not text:
        return ""

    text = text.replace("\xa0", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)

    return text.strip()


def normalize_label(label):
    """Normalize a field label for comparison."""
    return re.sub(r"\s+", " ", label.strip().lower()).rstrip(":")


def split_label(line):
    """Split a line into its label and value."""
    match = re.match(r"^\s*([^:]{1,100}):\s*(.*?)\s*$", line)

    if not match:
        return None, None

    return match.group(1).strip(), match.group(2).strip()


def extract_field(text, labels):
    """Extract a single value while skipping empty labels."""
    wanted_labels = {normalize_label(label) for label in labels}
    lines = text.splitlines()

    for index, line in enumerate(lines):
        label, value = split_label(line)

        if label is None:
            continue

        if normalize_label(label) not in wanted_labels:
            continue

        if value:
            value = clean_text(value)

            if value.lower() not in {"-", "na", "n/a", "none", "null"}:
                return value

            return ""

        # If the value is on the next line, only accept it when
        # the next non-empty line is not another field label.
        for next_line in lines[index + 1:]:
            candidate = next_line.strip()

            if not candidate:
                continue

            next_label, next_value = split_label(candidate)

            if next_label is not None:
                return ""

            return clean_text(candidate)

    return ""


def extract_multiline_field(text, labels, end_labels):
    """Extract a field that may contain multiple lines."""
    wanted_labels = {normalize_label(label) for label in labels}
    stop_labels = {normalize_label(label) for label in end_labels}
    lines = text.splitlines()

    for index, line in enumerate(lines):
        label, value = split_label(line)

        if label is None:
            continue

        if normalize_label(label) not in wanted_labels:
            continue

        collected = []

        if value:
            collected.append(value)

        for next_line in lines[index + 1:]:
            candidate = next_line.strip()

            if not candidate:
                continue

            next_label, next_value = split_label(candidate)

            if next_label is not None:
                if normalize_label(next_label) in stop_labels:
                    break

            # Skip common navigation text if encountered.
            if candidate in {
                "Screen Reader Access",
                "Accessibility Menu",
                "Accessibility Options",
                "Skip To Main Content",
            }:
                continue

            collected.append(candidate)

        result = clean_text("\n".join(collected))

        if result.lower() in {"-", "na", "n/a", "none", "null"}:
            return ""

        return result

    return ""


def extract_eligibility(text):
    """Keep only eligibility criteria that have actual values."""
    fields = [
        ("Income", ["Income"]),
        ("Age From", ["Age From"]),
        ("Age To", ["Age To"]),
        ("Community", ["Community"]),
    ]

    results = []

    for display_label, labels in fields:
        value = extract_field(text, labels)

        if value:
            results.append(f"{display_label}: {value}")

    return "\n".join(results)


def clean_scheme(scheme):
    """Convert one raw scheme into a structured record."""
    raw_details = scheme.get("details", "")
    raw_details = raw_details.replace("\r\n", "\n").replace("\r", "\n")

    name = clean_text(scheme.get("name", ""))

    if not name:
        name = extract_field(
            raw_details,
            ["Scheme Title/Name", "Scheme Name"],
        )

    return {
        "name": name,
        "url": scheme.get("url", ""),
        "department": extract_field(
            raw_details,
            ["Concerned Department"],
        ),
        "concerned_district": extract_field(
            raw_details,
            ["Concerned District"],
        ),
        "sponsored_by": extract_field(
            raw_details,
            ["Sponsored By", "Sponsered By"],
        ),
        "funding_pattern": extract_field(
            raw_details,
            ["Funding Pattern"],
        ),
        "beneficiaries": extract_field(
            raw_details,
            ["Beneficiaries", "Beneficiary"],
        ),
        "types_of_benefits": extract_field(
            raw_details,
            ["Types of Benefits", "Type of Benefits"],
        ),
        "income": extract_field(raw_details, ["Income"]),
        "age_from": extract_field(raw_details, ["Age From"]),
        "age_to": extract_field(raw_details, ["Age To"]),
        "community": extract_field(raw_details, ["Community"]),
        "eligibility_criteria": extract_eligibility(raw_details),
        "how_to_apply": extract_multiline_field(
            raw_details,
            ["How To avail", "How to Apply", "How to avail"],
            [
                "Validity of the Scheme",
                "Introduced On",
                "Description",
                "Scheme Type",
                "Uploaded File",
            ],
        ),
        "description": extract_multiline_field(
            raw_details,
            ["Description"],
            ["Scheme Type", "Uploaded File"],
        ),
        "status": scheme.get("status", "unknown"),
        # Keep original page text for future inspection.
        "raw_details": clean_text(raw_details),
    }


def main():
    print("=" * 60)
    print("Tamil Nadu Scheme Details Cleaner")
    print("=" * 60)

    if not INPUT_FILE.exists():
        print(f"ERROR: Input file not found: {INPUT_FILE}")
        return

    try:
        with INPUT_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError) as error:
        print(f"ERROR reading input file: {error}")
        return

    schemes = data.get("schemes", [])

    if not isinstance(schemes, list):
        print("ERROR: 'schemes' must be a list in scheme_details.json.")
        return

    cleaned_schemes = [
        clean_scheme(scheme)
        for scheme in schemes
        if isinstance(scheme, dict)
    ]

    output_data = {
        "source": data.get("source", ""),
        "scheme_count": len(cleaned_schemes),
        "schemes": cleaned_schemes,
    }

    try:
        with OUTPUT_FILE.open("w", encoding="utf-8") as file:
            json.dump(
                output_data,
                file,
                ensure_ascii=False,
                indent=2,
            )
    except OSError as error:
        print(f"ERROR writing output file: {error}")
        return

    print(f"\nInput schemes:  {len(schemes)}")
    print(f"Output schemes: {len(cleaned_schemes)}")
    print(f"Saved file:     {OUTPUT_FILE.name}")

    fields_to_check = [
        "department",
        "funding_pattern",
        "beneficiaries",
        "types_of_benefits",
        "eligibility_criteria",
        "how_to_apply",
        "description",
    ]

    print("\nField extraction summary:")

    for field in fields_to_check:
        count = sum(
            bool(scheme.get(field))
            for scheme in cleaned_schemes
        )
        print(f"{field}: {count}/{len(cleaned_schemes)}")

    print("\nFirst scheme preview:")

    if cleaned_schemes:
        sample = {
            key: value
            for key, value in cleaned_schemes[0].items()
            if key != "raw_details"
        }

        print(json.dumps(sample, ensure_ascii=False, indent=2))

    print("\nCleaning completed.")
    print("Verify the fields before updating Neo4j.")


if __name__ == "__main__":
    main()
