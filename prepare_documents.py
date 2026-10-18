
from pathlib import Path
import json
import re

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "tn_schemes.txt"
SCHEMES_FILE = BASE_DIR / "agriculture_schemes.json"
OUTPUT_FILE = BASE_DIR / "scheme_chunks.json"

DEPARTMENT = "Agriculture - Farmers Welfare Department"
EXPECTED_SCHEME_COUNT = 54

# Website navigation and other non-scheme text
IGNORE_LINES = {
    "Screen Reader Access",
    "W3C",
    "Accessibility Menu",
    "Text To Speech",
    "Bigger Text",
    "Small Text",
    "Line Height",
    "Highlight Links",
    "Text Spacing",
    "Cursor",
    "Light-Dark",
    "Invert Colors",
    "Reset All Settings",
    "Accessibility Options",
    "Skip To Main Content",
    "Home",
    "Government",
    "Government of Tamil Nadu",
    "தமிழ்நாடு அரசு",
    "Departments",
    "Districts",
    "Documents",
    "G.Os",
    "Policy notes / Performance Budget / Citizen Charter",
    "Rules & Regulations",
    "Circulars & notifications",
    "Announcements",
    "Acts",
    "Services",
    "Online Services",
    "Contact Directory",
    "Job Opportunity",
    "Important Websites",
    "Census",
    "Statistics",
    "Employment Details",
    "Grievances",
    "Forms",
    "RTI Contacts",
    "Mobile App Directory",
    "Schemes",
    "News & Events",
    "Press Releases",
    "Publications",
    "Photo Gallery",
    "Video Gallery",
    "Interact with Govt",
    "Polls",
    "Discussion Forum",
    "Others",
    "What's New",
    "Help line Numbers",
    "Holidays",
    "Sitemap",
    "Feedback",
    "CSC Login",
    "0:00",
    "Your browser does not support the audio tag.",
    "Disclaimer",
    "Privacy and Copyright policy",
    "Terms of Use",
    "FAQ",
    "|",
    "| copyright@2024",
}


# --------------------------------------------------
# Utility functions
# --------------------------------------------------

def clean_line(line):
    """Normalize spaces and remove surrounding whitespace."""
    return re.sub(r"\s+", " ", line).strip()


def extract_schemes(lines):
    """Extract unique schemes listed under the target department."""

    schemes = []
    inside_department = False

    for raw_line in lines:
        line = clean_line(raw_line)

        if not line:
            continue

        # Begin extracting when the target heading is encountered.
        if line == DEPARTMENT:
            inside_department = True
            continue

        if not inside_department:
            continue

        # Stop at website footer content.
        if line.startswith((
            "Content owned and Maintained by:",
            "Site Designed and Developed by:",
            "Queries/Comments regarding",
        )):
            break

        if line in IGNORE_LINES:
            continue

        # Ignore short, likely non-scheme text.
        if len(line) < 4:
            continue

        # Keep unique scheme names while preserving source order.
        if line not in schemes:
            schemes.append(line)

    return schemes


# --------------------------------------------------
# Main preparation process
# --------------------------------------------------

def prepare_documents():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Source file not found: {INPUT_FILE}"
        )

    # Load source text through LangChain.
    loader = TextLoader(
        str(INPUT_FILE),
        encoding="utf-8",
    )

    documents = loader.load()
    source_text = documents[0].page_content

    # Extract the scheme list.
    schemes = extract_schemes(source_text.splitlines())

    if not schemes:
        raise ValueError(
            "No schemes found. Check the department heading "
            "in tn_schemes.txt."
        )

    # Save the extracted schemes.
    scheme_data = {
        "department": DEPARTMENT,
        "scheme_count": len(schemes),
        "schemes": schemes,
    }

    SCHEMES_FILE.write_text(
        json.dumps(
            scheme_data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # Create department-aware source text for RAG.
    cleaned_text = (
        f"Department: {DEPARTMENT}\n\n"
        + "\n".join(
            f"Scheme: {scheme}"
            for scheme in schemes
        )
    )

    # Split text into chunks for retrieval.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.create_documents(
        [cleaned_text],
        metadatas=[{
            "department": DEPARTMENT,
            "source": INPUT_FILE.name,
        }],
    )

    # Save chunks as JSON.
    chunk_data = []

    for index, chunk in enumerate(chunks, start=1):
        chunk_data.append({
            "chunk_id": index,
            "department": DEPARTMENT,
            "source": INPUT_FILE.name,
            "text": chunk.page_content,
        })

    OUTPUT_FILE.write_text(
        json.dumps(
            chunk_data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # Display results.
    print("\nDocument preparation completed!")
    print("-" * 45)
    print(f"Department: {DEPARTMENT}")
    print(f"Unique schemes extracted: {len(schemes)}")
    print(f"Expected scheme count: {EXPECTED_SCHEME_COUNT}")
    print(
        f"Count matches: "
        f"{len(schemes) == EXPECTED_SCHEME_COUNT}"
    )
    print(f"Original characters: {len(source_text)}")
    print(f"Chunks created: {len(chunks)}")
    print(f"Scheme list saved: {SCHEMES_FILE}")
    print(f"Chunks saved: {OUTPUT_FILE}")

    print("\n--- Extracted schemes ---")

    for index, scheme in enumerate(schemes, start=1):
        print(f"{index}. {scheme}")


if __name__ == "__main__":
    prepare_documents()
