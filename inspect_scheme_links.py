
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin

URL = "https://www.tn.gov.in/scheme_list.php?dep_id=Mg=="

headers = {
    "User-Agent": "Mozilla/5.0"
}

try:
    response = requests.get(URL, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    print("Page title:", soup.title.get_text(strip=True) if soup.title else "Not found")
    print("\n--- Scheme-related links ---")

    found = 0

    for link in soup.find_all("a", href=True):
        name = link.get_text(" ", strip=True)
        href = urljoin(URL, link["href"])

        if name and any(word in name.lower() for word in [
            "scheme", "farmer", "seed", "subsidy", "training",
            "agriculture", "livelihood", "pest", "soil"
        ]):
            print(f"{name} -> {href}")
            found += 1

    print(f"\nLinks found: {found}")

    if found == 0:
        print("No matching links found. The page may use a different link structure.")

except requests.RequestException as error:
    print("Website request failed:", error)
