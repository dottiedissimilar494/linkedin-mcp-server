"""Company profile HTML parsers.

All functions receive HTML and return typed models.
"""

import re

from linkedin_mcp_server.domain.models.company import (
    CompanyAbout,
    CompanyJobEntry,
    CompanyJobsSection,
    CompanyPostEntry,
    CompanyPostsSection,
)
from linkedin_mcp_server.domain.parsers.common import (
    aria_hidden_text,
    soup,
    text,
)

# ── Helpers ──────────────────────────────────────────────────────────────────

_PROMO_URN_PREFIX = "urn:li:inAppPromotion"


# ── Company About parser ────────────────────────────────────────────────────


def parse_company_about(html: str, *, include_raw: bool = False) -> CompanyAbout:
    """Parse company about/overview page HTML.

    Extracts: name, overview, website, phone, industry, company_size,
    headquarters, type, founded, specialties, followers, employees_on_linkedin.
    """
    s = soup(html)

    # Company name — <h1> with org-top-card-summary__title class
    name: str | None = None
    h1 = s.find(
        "h1",
        class_=lambda c: c and "org-top-card-summary__title" in c,
    )
    if h1:
        name = text(h1)

    # Top card info items (industry, location, followers, employees)
    followers: str | None = None
    employees_on_linkedin: str | None = None
    info_items = s.find_all(
        "div",
        class_="org-top-card-summary-info-list__info-item",
    )
    for item in info_items:
        txt = text(item)
        if not txt:
            continue
        if "follower" in txt.lower():
            followers = txt.strip()
        elif "employee" in txt.lower():
            employees_on_linkedin = txt.strip()

    # Overview text — <p> with break-words class in the about section
    overview: str | None = None
    overview_el = s.find(
        "p",
        class_=lambda c: c and "break-words" in c and "white-space-pre-wrap" in c,
    )
    if overview_el:
        overview = text(overview_el)

    # Parse <dl> definition list for structured details
    details: dict[str, str] = {}
    dl = s.find("dl")
    if dl:
        dts = dl.find_all("dt")
        for dt in dts:
            h3 = dt.find("h3")
            key = text(h3) if h3 else text(dt)
            if not key:
                continue
            key_lower = key.lower().strip()

            # Find the next <dd> sibling(s)
            dd = dt.find_next_sibling("dd")
            if dd:
                # For links, extract the href text
                link = dd.find("a")
                if link and key_lower == "website":
                    span = link.find("span")
                    value = text(span) if span else text(link)
                else:
                    value = text(dd)

                if value:
                    details[key_lower] = value

                    # Company size may have a second <dd> with associated members
                    if key_lower == "company size":
                        dd2 = dd.find_next_sibling("dd")
                        if dd2:
                            assoc = text(dd2)
                            if assoc and "associated" in assoc.lower():
                                details["associated_members"] = assoc

    # Map details to model fields
    website = details.get("website")
    phone = details.get("phone")
    industry = details.get("industry")
    company_size = details.get("company size")
    if "associated_members" in details:
        company_size = (
            f"{company_size} ({details['associated_members']})"
            if company_size
            else details["associated_members"]
        )
    headquarters = details.get("headquarters")
    company_type = details.get("type")
    founded = details.get("founded")
    specialties = details.get("specialties")

    # Company logo URL from top card image
    logo_url: str | None = None
    logo_img = s.find(
        "img",
        class_=lambda c: c and "org-top-card-primary-content__logo" in c,
    )
    if not logo_img:
        # Fallback: any img in the top card section
        top_card = s.find("section", class_="org-top-card")
        if top_card:
            logo_img = top_card.find("img")
    if logo_img:
        src = logo_img.get("src", "")
        if src:
            logo_url = src

    return CompanyAbout(
        name=name,
        overview=overview,
        website=website,
        phone=phone,
        industry=industry,
        company_size=company_size,
        headquarters=headquarters,
        type=company_type,
        founded=founded,
        specialties=specialties,
        followers=followers,
        employees_on_linkedin=employees_on_linkedin,
        logo_url=logo_url,
        raw=html if include_raw else None,
    )


# ── Company Posts parser ─────────────────────────────────────────────────────


def parse_company_posts(html: str, *, include_raw: bool = False) -> CompanyPostsSection:
    """Parse company posts feed HTML.

    Extracts list of CompanyPostEntry (text, time_posted, reactions,
    comments, reposts).  Promotional items are skipped.
    """
    s = soup(html)
    entries: list[CompanyPostEntry] = []

    articles = s.find_all(
        "div",
        class_=lambda c: c and "feed-shared-update-v2" in c,
        attrs={"role": "article"},
    )

    for article in articles:
        # Skip promos
        urn = article.get("data-urn", "")
        if urn.startswith(_PROMO_URN_PREFIX):
            continue

        # Post text
        text_el = article.find(
            "div",
            class_=lambda c: c and "update-components-text" in c,
        )
        post_text: str | None = None
        if text_el:
            span = text_el.find("span", class_="break-words")
            post_text = text(span) if span else text(text_el)

        # Time posted
        time_el = article.find(
            "span",
            class_=lambda c: c and "update-components-actor__sub-description" in c,
        )
        time_posted = aria_hidden_text(time_el)
        # Clean trailing bullet / globe icon noise
        if time_posted:
            time_posted = re.sub(r"\s*•.*$", "", time_posted).strip()

        # Reactions count
        reactions_el = article.find(
            "span",
            class_=lambda c: c and "social-details-social-counts__reactions-count" in c,
        )
        reactions = text(reactions_el)

        # Comments count
        comments_btn = article.find(
            "button",
            attrs={"aria-label": lambda v: v and "comment" in v.lower()},
        )
        comments: str | None = None
        if comments_btn:
            span = comments_btn.find("span", attrs={"aria-hidden": "true"})
            comments = text(span) if span else None

        # Reposts count
        reposts_btn = article.find(
            "button",
            attrs={"aria-label": lambda v: v and "repost" in v.lower()},
        )
        reposts: str | None = None
        if reposts_btn:
            span = reposts_btn.find("span", attrs={"aria-hidden": "true"})
            reposts = text(span) if span else None

        entries.append(
            CompanyPostEntry(
                text=post_text,
                time_posted=time_posted,
                reactions=reactions,
                comments=comments,
                reposts=reposts,
            )
        )

    return CompanyPostsSection(
        posts=entries,
        raw=html if include_raw else None,
    )


# ── Company Jobs parser ──────────────────────────────────────────────────────

_COMPANY_JOB_ID_RE = re.compile(r"currentJobId=(\d+)")


def parse_company_jobs(html: str, *, include_raw: bool = False) -> CompanyJobsSection:
    """Parse company jobs page HTML.

    Extracts total_openings and a list of CompanyJobEntry from both the
    \"Recommended\" and \"Recently posted\" carousels.
    """
    s = soup(html)
    entries: list[CompanyJobEntry] = []

    # Total openings headline
    total_openings: str | None = None
    headline = s.find(
        "h4",
        class_=lambda c: c and "org-jobs-job-search-form-module__headline" in c,
    )
    if headline:
        total_openings = text(headline)

    # Job cards appear inside <section class="job-card-container ...">
    cards = s.find_all(
        "section",
        class_=lambda c: c and "job-card-container" in c,
    )

    for card in cards:
        # Title from aria-hidden span > strong
        title_div = card.find("div", class_="job-card-square__title")
        title: str | None = None
        if title_div:
            hidden_span = title_div.find("span", attrs={"aria-hidden": "true"})
            if hidden_span:
                strong = hidden_span.find("strong")
                title = text(strong) if strong else text(hidden_span)

        # Job ID and URL from href
        job_id: str | None = None
        job_url: str | None = None
        link = card.find("a", class_=lambda c: c and "job-card-square__link" in c)
        if link:
            href = link.get("href", "")
            m = _COMPANY_JOB_ID_RE.search(href)
            if m:
                job_id = m.group(1)
                job_url = f"https://www.linkedin.com/jobs/view/{job_id}/"

        # Company name
        company_div = card.find("div", class_="job-card-container__company-name")
        company = text(company_div)

        # Location
        location_span = card.find("span", class_="pJCTyyZHJEwdnAZhBTBVMaBZjcFmTQ")
        location = text(location_span)

        # Posted time from <time> element
        time_el = card.find("time")
        posted_time = text(time_el)

        entries.append(
            CompanyJobEntry(
                title=title,
                job_id=job_id,
                job_url=job_url,
                company=company,
                location=location,
                posted_time=posted_time,
            )
        )

    return CompanyJobsSection(
        total_openings=total_openings,
        jobs=entries,
        raw=html if include_raw else None,
    )
