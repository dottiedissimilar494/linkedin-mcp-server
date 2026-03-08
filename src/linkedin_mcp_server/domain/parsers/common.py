"""Common parsing utilities shared across parser modules."""

import re

from bs4 import BeautifulSoup, Tag

# ── Shared regex patterns ─────────────────────────────────────────────────────

JOB_VIEW_RE = re.compile(r"/jobs/view/(\d+)/?")

# ── Text extraction helpers ───────────────────────────────────────────────────


def text(element: Tag | None) -> str | None:
    """Extract visible text from an element, stripping and collapsing whitespace."""
    if element is None:
        return None
    txt = element.get_text(separator=" ", strip=True)
    # Collapse multiple whitespace
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt or None


def aria_hidden_text(element: Tag | None) -> str | None:
    """Extract the aria-hidden='true' span text for display values."""
    if element is None:
        return None
    span = element.find("span", attrs={"aria-hidden": "true"})
    return text(span) if span else text(element)


def soup(html: str, *, parser: str = "lxml") -> BeautifulSoup:
    """Create a BeautifulSoup instance from HTML.

    Args:
        html: HTML content to parse
        parser: Parser backend. Defaults to "lxml" for robust parsing.
            Use "html.parser" for lightweight / SDUI pages.
    """
    return BeautifulSoup(html, parser)
