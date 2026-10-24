"""Custom web research tools for the multi-agent research system."""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool

from config import get_setting


TAVILY_SEARCH_URL = "https://api.tavily.com/search"
REQUEST_TIMEOUT_SECONDS = 20
MAX_PAGE_BYTES = 2_000_000
MAX_PAGE_TEXT_CHARS = 12_000


def _validate_public_http_url(url: str) -> str | None:
    """Return an error message for invalid or clearly local URLs."""
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return "Please provide a complete http:// or https:// URL."

    hostname = parsed.hostname.rstrip(".").lower()
    if hostname == "localhost" or hostname.endswith(".localhost"):
        return "Localhost URLs cannot be scraped."

    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return None

    if not address.is_global:
        return "Private or local IP addresses cannot be scraped."
    return None


@tool
def web_search(query: str, max_results: int = 5, topic: str = "general") -> str:
    """Search the live web with Tavily and return titles, URLs, and snippets.

    Args:
        query: A focused web search query.
        max_results: Number of results to return, from 1 to 10.
        topic: Search category: general, news, or finance.
    """
    api_key = get_setting("TAVILY_API_KEY")
    if not api_key:
        return "Tavily API key is missing. Add TAVILY_API_KEY to the project .env file."

    if not query.strip():
        return "Search query cannot be empty."
    if not 1 <= max_results <= 10:
        return "max_results must be between 1 and 10."
    if topic not in {"general", "news", "finance"}:
        return "topic must be one of: general, news, finance."

    try:
        response = requests.post(
            TAVILY_SEARCH_URL,
            json={
                "api_key": api_key,
                "query": query,
                "max_results": max_results,
                "topic": topic,
                "search_depth": "basic",
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status:
            return f"Tavily search failed with HTTP {status}. Check the API key and try again."
        return f"Tavily search request failed: {exc}"
    except ValueError:
        return "Tavily returned a response that could not be read as JSON."

    results = payload.get("results", [])
    if not results:
        return "Tavily found no results for that query."

    lines = []
    for index, result in enumerate(results[:max_results], start=1):
        title = result.get("title") or "Untitled result"
        result_url = result.get("url") or ""
        snippet = re.sub(r"\s+", " ", result.get("content") or "").strip()
        lines.append(f"{index}. {title}\nURL: {result_url}\nSnippet: {snippet}")
    return "\n\n".join(lines)


@tool
def scrape_url(url: str) -> str:
    """Fetch a public web page and extract its readable text with BeautifulSoup.

    Args:
        url: The complete http:// or https:// URL of the page to read.
    """
    url_error = _validate_public_http_url(url)
    if url_error:
        return url_error

    try:
        with requests.get(
            url,
            headers={"User-Agent": "MultiAgentResearchBot/1.0 (web page text extraction)"},
            timeout=REQUEST_TIMEOUT_SECONDS,
            stream=True,
        ) as response:
            response.raise_for_status()
            content = bytearray()
            for chunk in response.iter_content(chunk_size=64_000):
                content.extend(chunk)
                if len(content) > MAX_PAGE_BYTES:
                    return "The page is too large to scrape (limit: 2 MB)."
    except requests.RequestException as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status:
            return f"Could not fetch the page (HTTP {status}): {url}"
        return f"Could not fetch the page: {exc}"

    soup = BeautifulSoup(bytes(content), "html.parser")
    for element in soup(
        ["script", "style", "noscript", "svg", "nav", "header", "footer", "aside", "form"]
    ):
        element.decompose()

    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return f"No readable page text was found at {url}."
    if len(text) > MAX_PAGE_TEXT_CHARS:
        text = text[:MAX_PAGE_TEXT_CHARS].rsplit(" ", 1)[0] + "… [text truncated]"
    return f"Source URL: {url}\n\n{text}"
