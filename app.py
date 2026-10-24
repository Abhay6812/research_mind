"""Portfolio-ready Streamlit interface for the Gemini research workflow."""

from __future__ import annotations

import importlib
import re
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from config import get_setting


load_dotenv()

st.set_page_config(
    page_title="ResearchMind | AI Research Studio",
    page_icon="R",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
      :root { --ink:#e9f0f2; --muted:#92a2a8; --panel:#111a1e; --line:#25363b;
              --accent:#80e0c0; --accent-dark:#153c35; --gold:#efc77a; }
      .stApp { background: radial-gradient(ellipse at 12% 0%, #17302e 0%, #0a1115 43%);
               color:var(--ink); font-family:'DM Sans',sans-serif; }
      .block-container { max-width:1220px; padding-top:1.3rem; padding-bottom:3rem; }
      h1,h2,h3 { font-family:'Manrope',sans-serif !important; letter-spacing:-.035em; }
      .topbar { display:flex; align-items:center; justify-content:space-between; padding:.45rem 0 2.6rem;
                border-bottom:1px solid rgba(146,162,168,.16); margin-bottom:2.4rem; }
      .brand { display:flex; gap:.75rem; align-items:center; color:var(--ink); font-weight:700; letter-spacing:.02em; }
      .brand-mark { display:grid; place-items:center; width:34px; height:34px; border-radius:10px;
                    color:#09201b; background:var(--accent); font:800 1rem 'Manrope',sans-serif; }
      .top-meta { color:var(--muted); font: .72rem 'DM Mono',monospace; letter-spacing:.11em; text-transform:uppercase; }
      .hero-kicker { color:var(--accent); font:500 .72rem 'DM Mono',monospace; letter-spacing:.16em; text-transform:uppercase; }
      .hero-title { color:var(--ink); font:800 clamp(2.6rem,6vw,4.5rem)/1.04 'Manrope',sans-serif;
                    letter-spacing:-.065em; margin:.65rem 0 1rem; max-width:850px; }
      .hero-title span { color:var(--accent); }
      .hero-copy { color:#a6b5b8; font-size:1.08rem; line-height:1.7; max-width:760px; margin-bottom:2.2rem; }
      .section-label { color:var(--muted); font:500 .7rem 'DM Mono',monospace; text-transform:uppercase;
                       letter-spacing:.13em; margin:0 0 .55rem; }
      .panel { background:rgba(17,26,30,.82); border:1px solid var(--line); border-radius:16px;
               padding:1.2rem 1.3rem; }
      .step { display:flex; gap:.85rem; align-items:flex-start; padding:.9rem 0;
              border-bottom:1px solid rgba(146,162,168,.12); }
      .step:last-child { border-bottom:0; padding-bottom:.1rem; }
      .step-num { display:grid; place-items:center; flex:none; width:27px; height:27px; border-radius:8px;
                  background:#1b292e; color:#a9bbc0; font:500 .7rem 'DM Mono',monospace; }
      .step.done .step-num { background:var(--accent-dark); color:var(--accent); }
      .step-title { color:var(--ink); font-weight:600; font-size:.92rem; }
      .step-desc { color:var(--muted); font-size:.79rem; margin-top:.15rem; }
      .info-card { background:rgba(17,26,30,.62); border:1px solid rgba(146,162,168,.15);
                   padding:.9rem 1rem; border-radius:12px; height:100%; }
      .info-title { color:var(--ink); font-weight:600; font-size:.88rem; margin-bottom:.25rem; }
      .info-copy { color:var(--muted); font-size:.78rem; line-height:1.55; }
      .result-head { padding:1rem 0 .4rem; }
      .result-topic { color:var(--muted); font-size:.9rem; margin-top:-.6rem; }
      .stTextInput input { background:#10191d !important; color:var(--ink) !important;
        border:1px solid #34474b !important; border-radius:10px !important; min-height:3rem; }
      .stTextInput input:focus { border-color:var(--accent) !important; box-shadow:0 0 0 1px var(--accent) !important; }
      div.stButton > button[kind="primary"] { background:var(--accent); color:#09201b; border:0;
        border-radius:10px; min-height:3rem; font-weight:700; }
      div.stButton > button[kind="primary"]:hover { background:#a3efd7; color:#09201b; }
      div[data-testid="stDownloadButton"] button { border-color:#42615a; color:var(--accent); border-radius:9px; }
      div[data-testid="stTabs"] button { color:#9fb0b4; }
      div[data-testid="stTabs"] button[aria-selected="true"] { color:var(--accent); }
      .footer { border-top:1px solid rgba(146,162,168,.16); margin-top:3rem; padding-top:1.1rem;
                display:flex; justify-content:space-between; color:#718187; font:.68rem 'DM Mono',monospace;
                letter-spacing:.06em; text-transform:uppercase; }
      .stCaption { color:var(--muted) !important; }
    </style>
    <div class="topbar">
      <div class="brand"><div class="brand-mark">R</div><span>RESEARCHMIND</span></div>
      <div class="top-meta">AI research studio &nbsp; / &nbsp; Gemini + Tavily</div>
    </div>
    <div class="hero-kicker">A source-first multi-agent research workflow</div>
    <div class="hero-title">From a question to a<br><span>research-ready brief.</span></div>
    <div class="hero-copy">ResearchMind searches current web sources, reads a relevant page, then uses Gemini to write and review a concise, evidence-led report. Every run keeps the source trail visible.</div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([1.15, 0.85], gap="large")
with left:
    st.markdown('<div class="section-label">Start a research run</div>', unsafe_allow_html=True)
    with st.container(border=True):
        topic = st.text_input(
            "Research question",
            placeholder="For example: What changed in international cricket this week?",
            label_visibility="collapsed",
            key="research_topic",
        )
        run_clicked = st.button("Run research", type="primary", use_container_width=True)
        quick_mode = st.checkbox(
            "Quick mode — call search and scraping tools directly",
            value=True,
            help="Skips Gemini tool-selection calls. Gemini still writes and reviews the report.",
        )
        st.caption("Quick mode reduces model round trips while preserving the report and review stages.")

with right:
    st.markdown('<div class="section-label">How it works</div>', unsafe_allow_html=True)
    stage_defs = [
        ("search", "Discover sources", "Tavily finds current web results."),
        ("reader", "Read the evidence", "BeautifulSoup extracts readable page text."),
        ("writer", "Draft the brief", "A Gemini LCEL runnable writes from gathered evidence."),
        ("critic", "Review the report", "A second Gemini runnable checks clarity and support."),
    ]
    completed = st.session_state.get("completed_stages", [])
    steps_html = '<div class="panel">'
    for index, (key, title, detail) in enumerate(stage_defs, start=1):
        step_state = "done" if key in completed else "pending"
        steps_html += (
            f'<div class="step {step_state}"><div class="step-num">{index:02}</div>'
            f'<div><div class="step-title">{title}</div><div class="step-desc">{detail}</div></div></div>'
        )
    steps_html += "</div>"
    st.markdown(steps_html, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
info_cols = st.columns(3)
for col, title, copy in zip(
    info_cols,
    ("Traceable", "Composable", "Practical"),
    (
        "Search results and scraped source notes stay available beside the final report.",
        "The workflow combines tool-using agents with LCEL report-writing runnables.",
        "Export the finished brief as Markdown for sharing or further editing.",
    ),
):
    with col:
        st.markdown(
            f'<div class="info-card"><div class="info-title">{title}</div>'
            f'<div class="info-copy">{copy}</div></div>',
            unsafe_allow_html=True,
        )

if run_clicked:
    if not topic.strip():
        st.warning("Add a research question to start.")
    elif not (get_setting("GEMINI_API_KEY") or get_setting("GOOGLE_API_KEY")):
        st.error("Gemini API key not found. Add GEMINI_API_KEY to .env or Streamlit secrets.")
    elif not get_setting("TAVILY_API_KEY"):
        st.error("Tavily API key not found. Add TAVILY_API_KEY to .env or Streamlit secrets.")
    else:
        import pipeline

        pipeline = importlib.reload(pipeline)
        results: dict[str, str] = {}
        st.session_state.completed_stages = []
        st.session_state.results = {}
        st.session_state.last_topic = topic.strip()
        status = st.status("Preparing your research run…", expanded=True)
        stage_labels = {
            "search": "Source discovery complete",
            "reader": "Source reading complete",
            "writer": "Research brief drafted",
            "critic": "Editorial review complete",
        }

        def on_step(name: str, value: str) -> None:
            results[name] = value
            st.session_state.results = dict(results)
            st.session_state.completed_stages = list(results)
            status.write(f"✓ {stage_labels[name]}")

        def on_progress(message: str) -> None:
            status.write(message)

        try:
            pipeline.run_research_pipeline(
                topic.strip(),
                on_step=on_step,
                fast_mode=quick_mode,
                on_progress=on_progress,
            )
            status.update(label="Research brief is ready", state="complete", expanded=False)
            st.rerun()
        except Exception as exc:
            status.update(label="Research run stopped", state="error", expanded=True)
            st.error(str(exc))

results = st.session_state.get("results", {})
if results:
    st.markdown("## Research brief")
    st.markdown(
        f'<div class="result-topic">Topic: {st.session_state.get("last_topic", "")}</div>',
        unsafe_allow_html=True,
    )
    source_count = len(set(re.findall(r"https?://[^\s)]+", results.get("search", ""))))
    meta_a, meta_b, meta_c = st.columns(3)
    meta_a.metric("Web sources found", source_count)
    meta_b.metric("Research stages", f'{len(st.session_state.get("completed_stages", []))} / 4')
    meta_c.metric("Generated", datetime.now().strftime("%d %b %Y, %H:%M"))

    report_tab, review_tab, sources_tab = st.tabs(["Report", "Reviewer notes", "Source material"])
    with report_tab:
        if "writer" in results:
            st.markdown(results["writer"])
            file_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                "Download report as Markdown",
                data=results["writer"],
                file_name=f"research_brief_{file_stamp}.md",
                mime="text/markdown",
            )
    with review_tab:
        if "critic" in results:
            st.markdown(results["critic"])
        else:
            st.info("The reviewer notes will appear after the report review stage finishes.")
    with sources_tab:
        if "search" in results:
            st.markdown("#### Search results")
            st.markdown(results["search"])
        if "reader" in results:
            st.markdown("#### Scraped source notes")
            st.markdown(results["reader"])

st.markdown(
    '<div class="footer"><span>ResearchMind · Gemini / Tavily / LangChain</span>'
    '<span>Built for transparent, source-backed research</span></div>',
    unsafe_allow_html=True,
)
