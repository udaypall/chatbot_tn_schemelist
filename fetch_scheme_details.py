
import json
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent

LIST_URL = "https://www.tn.gov.in/scheme_list.php?dep_id=Mg=="
OUTPUT_FILE = BASE_DIR / "scheme_details.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
}


def get_page(session, url):
    response = session.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "lxml")


def main():
    schemes = []
    seen_urls = set()

    try:
        with requests.Session() as session:
            print("Loading government scheme list...")

            soup = get_page(session, LIST_URL)

            # Collect every scheme-details link, not just links
            # whose visible text contains selected keywords.
            for link in soup.find_all("a", href=True):
                url = urljoin(LIST_URL, link["href"])

                if "scheme_details.php" not in url:
                    continue

                if url in seen_urls:
                    continue

                seen_urls.add(url)

                name = link.get_text(" ", strip=True)

                if not name:
                    name = "Unnamed scheme"

                schemes.append({
                    "name": name,
                    "url": url,
                    "details": ""
                })

            print(f"Unique detail links found: {len(schemes)}")

            if not schemes:
                print("No scheme detail links found.")
                return

            # Fetch each detail page politely.
            for index, scheme in enumerate(schemes, start=1):
                try:
                    print(
                        f"[{index}/{len(schemes)}] "
                        f"Fetching: {scheme['name']}"
                    )

                    detail_soup = get_page(session, scheme["url"])

                    for element in detail_soup(
                        ["script", "style", "noscript", "nav", "footer"]
                    ):
                        element.decompose()

                    main_content = (
                        detail_soup.find("main")
                        or detail_soup.find("article")
                        or detail_soup.find("body")
                    )

                    if main_content:
                        scheme["details"] = main_content.get_text(
                            separator="\n",
                            strip=True
                        )

                    scheme["status"] = (
                        "success" if scheme["details"] else "empty"
                    )

                except requests.RequestException as error:
                    scheme["status"] = "failed"
                    scheme["error"] = str(error)
                    print(f"  Could not fetch page: {error}")

                time.sleep(0.5)

        OUTPUT_FILE.write_text(
            json.dumps(
                {
                    "source": LIST_URL,
                    "scheme_count": len(schemes),
                    "schemes": schemes
                },
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

        successful = sum(
            scheme.get("status") == "success"
            for scheme in schemes
        )

        print("\nExtraction completed.")
        print(f"Detail pages collected: {len(schemes)}")
        print(f"Pages with readable text: {successful}")
        print(f"Saved to: {OUTPUT_FILE}")

    except requests.RequestException as error:
        print(f"Unable to load the scheme list: {error}")


if __name__ == "__main__":
    main()
