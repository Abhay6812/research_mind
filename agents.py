"""Gemini-backed agents and LCEL research/report runnables."""

from __future__ import annotations

from langchain.agents import create_agent
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from config import get_setting
from tools import scrape_url, web_search


def _build_model() -> ChatGoogleGenerativeAI:
    api_key = get_setting("GEMINI_API_KEY") or get_setting("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Gemini API key is missing. Add GEMINI_API_KEY to the project .env file."
        )

    return ChatGoogleGenerativeAI(
        model=get_setting("GEMINI_MODEL", "gemini-3.8-flash"),
        temperature=0,
        google_api_key=api_key,
        max_retries=2,
    )


llm = _build_model()


def build_search_agent():
    """Create the ReAct search agent, which can call Tavily web search."""
    return create_agent(
        model=llm,
        tools=[web_search],
        system_prompt=(
            "You are a web research agent. Search the web for recent, reliable, "
            "relevant sources. Use the web_search tool, then summarize findings "
            "with source titles and URLs. Do not invent sources."
        ),
    )


def build_reader_agent():
    """Create the ReAct reader agent, which can scrape a relevant URL."""
    return create_agent(
        model=llm,
        tools=[scrape_url],
        system_prompt=(
            "You are a research reader. Select the most relevant URL from the "
            "provided search results and use scrape_url to inspect it. Summarize "
            "the page's useful evidence and include the URL. If scraping fails, "
            "say so clearly."
        ),
    )


writer_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert research writer. Produce clear, structured, "
            "source-grounded reports. Distinguish evidence from uncertainty.",
        ),
        (
            "human",
            """Write a detailed research report on this topic.

Topic: {topic}

Research gathered:
{research}

Use these sections:
1. Introduction
2. Key Findings (at least three explained points)
3. Analysis
4. Conclusion
5. Sources (include the URLs present in the research)

Be factual and professional. Do not make up facts or citations.""",
        ),
    ]
)
writer_runnable = writer_prompt | llm | StrOutputParser()


critic_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a careful research reviewer. Be specific, constructive, "
            "and strict about evidence and citations.",
        ),
        (
            "human",
            """Review this research report:

{report}

Return this format:
Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One-line verdict:
...""",
        ),
    ]
)
critic_runnable = critic_prompt | llm | StrOutputParser()
