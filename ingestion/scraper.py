from dataclasses import dataclass
from datetime import date

from bs4 import BeautifulSoup

from .http_client import polite_get

DOE_BASE_URL = "https://doe.gov.ph"
DOE_LISTING_PATH = "/articles/group/liquid-fuels"
DOE_LISTING_URL = f"{DOE_BASE_URL}{DOE_LISTING_PATH}?category=Retail%20Pump%20Prices&display_type=Card"


@dataclass
class PublicationLink:
    url: str
    title: str
    publication_date: date | None


def discover_publications() -> list[PublicationLink]:
    response = polite_get(DOE_LISTING_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    results: list[PublicationLink] = []

    for card in soup.select("div.article-card, div.card, article"):
        link_tag = card.find("a", href=True)
        if link_tag is None:
            continue
        href = str(link_tag["href"])
        if not href.startswith("http"):
            href = DOE_BASE_URL + href

        title = link_tag.get_text(strip=True)

        pub_date: date | None = None
        date_tag = card.select_one("time, span.date, .article-date")
        if date_tag:
            try:
                pub_date = date.fromisoformat(
                    str(date_tag.get("datetime", date_tag.text.strip()))
                )
            except ValueError:
                pass

        if href.lower().endswith(".pdf") or "pdf" in href.lower():
            results.append(
                PublicationLink(url=href, title=title, publication_date=pub_date)
            )

    return results
