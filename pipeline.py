"""Run the Search → Reader → Writer → Critic research workflow."""

from __future__ import annotations

from collections.abc import Callable
import re
from typing import Any

from agents import (
    build_reader_agent,
    build_search_agent,
    critic_runnable,
    writer_runnable,
)
from tools import scrape_url, web_search


StepCallback = Callable[[str, str], None]
ProgressCallback = Callable[[str], None]


def _message_text(message: Any) -> str:
    """Extract plain text from a LangChain message's content."""
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("text"):
                parts.append(str(item["text"]))
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts).strip()
    return str(content)


def _run_agent(agent: Any, prompt: str) -> str:
    result = agent.invoke({"messages": [("user", prompt)]})
    messages = result.get("messages", [])
    if not messages:
        return "The agent returned no messages."
    return _message_text(messages[-1])


def _is_recent_query(topic: str) -> bool:
    return bool(re.search(r"\b(recent|latest|today|current|updates|news|live)\b", topic, re.I))


def run_research_pipeline(
    topic: str,
    on_step: StepCallback | None = None,
    fast_mode: bool = True,
    on_progress: ProgressCallback | None = None,
) -> dict[str, str]:
    """Run the four stages; fast mode skips Gemini tool selection for tools."""
    topic = topic.strip()
    if not topic:
        raise ValueError("Enter a research topic before starting the pipeline.")

    state: dict[str, str] = {}

    print("\n" + "=" * 56)
    print("STEP 1 — SEARCH AGENT")
    print("=" * 56)
    if on_progress:
        on_progress("Searching the web with Tavily…" if fast_mode else "Gemini search agent is searching…")
    if fast_mode:
        search_topic = "news" if _is_recent_query(topic) else "general"
        state["search"] = web_search.invoke(
            {"query": topic, "max_results": 3, "topic": search_topic}
        )
    else:
        state["search"] = _run_agent(
            build_search_agent(),
            f"Find recent, reliable, detailed information about: {topic}",
        )
    if on_step:
        on_step("search", state["search"])

    print("\n" + "=" * 56)
    print("STEP 2 — READER AGENT")
    print("=" * 56)
    if on_progress:
        on_progress("Scraping the selected source…" if fast_mode else "Gemini reader agent is reviewing a source…")
    if fast_mode:
        match = re.search(r"^URL:\s*(https?://\S+)", state["search"], re.MULTILINE)
        state["reader"] = (
            scrape_url.invoke({"url": match.group(1)})
            if match
            else "No scrapeable URL was returned by web search."
        )
    else:
        state["reader"] = _run_agent(
            build_reader_agent(),
            (
                f"For the research topic '{topic}', choose the most relevant URL "
                "from these search results and scrape it for deeper evidence. "
                "Summarize the evidence and retain its source URL.\n\n"
                f"Search results:\n{state['search'][:8_000]}"
            ),
        )
    if on_step:
        on_step("reader", state["reader"])

    print("\n" + "=" * 56)
    print("STEP 3 — WRITER")
    print("=" * 56)
    if on_progress:
        on_progress("Gemini is drafting the research report…")
    combined_research = (
        f"SEARCH RESULTS:\n{state['search']}\n\n"
        f"DETAILED SCRAPED CONTENT:\n{state['reader']}"
    )
    state["writer"] = writer_runnable.invoke(
        {"topic": topic, "research": combined_research}
    )
    if on_step:
        on_step("writer", state["writer"])

    print("\n" + "=" * 56)
    print("STEP 4 — CRITIC")
    print("=" * 56)
    if on_progress:
        on_progress("Gemini is reviewing the report…")
    state["critic"] = critic_runnable.invoke({"report": state["writer"]})
    if on_step:
        on_step("critic", state["critic"])

    return state


if __name__ == "__main__":
    try:
        research_topic = input("\nEnter a research topic: ")
        output = run_research_pipeline(research_topic)
        print("\nFinal report\n")
        print(output["writer"])
        print("\nCritic feedback\n")
        print(output["critic"])
    except (RuntimeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
