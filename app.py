import os
import streamlit as st

st.set_page_config(page_title="Research Crew", page_icon="🔎", layout="wide")

# crew.py reads these at import time, so set them before importing it
for key in ("GROQ_API_KEY", "SERPER_API_KEY"):
    os.environ[key] = st.secrets[key]

from crew import ResearchCrew

# Same order as the tasks in crew.py: research -> analysis -> fact check -> report
AGENTS = [
    {"name": "Researcher",   "icon": "🔍", "color": "#2563EB", "desc": "Searches the web for sources"},
    {"name": "Analyst",      "icon": "📊", "color": "#7C3AED", "desc": "Picks the key claims, spots gaps"},
    {"name": "Fact-Checker", "icon": "✅", "color": "#059669", "desc": "Verifies each claim"},
    {"name": "Writer",       "icon": "✍️", "color": "#D97706", "desc": "Produces the final report"},
]
PURPLE_PURPOSE = "#0D9488"   # purpose
CREW_COLOR = "#F0584E"       # CrewAI backend
STREAMLIT_COLOR = "#E11D48"  # Streamlit

# ---------------------------------------------------------------- overview (right column)
OVERVIEW_CSS = """
<style>
.flow{display:flex;flex-direction:column}
.node{border-radius:12px;padding:12px 14px;line-height:1.35}
.node.mini{padding:8px 12px;border-radius:10px}
.node-head{display:flex;align-items:center;gap:12px}
.ico{font-size:1.6rem}
.mini .ico{font-size:1.2rem}
.ttl{font-weight:700}
.sub{font-size:.85rem;opacity:.8}
.chips{margin-top:8px;display:flex;flex-wrap:wrap;gap:6px}
.chip{font-size:.75rem;padding:2px 9px;border-radius:999px;background:rgba(128,128,128,.2)}
.group{position:relative;border:1.5px dashed rgba(128,128,128,.5);border-radius:14px;padding:36px 12px 12px}
.group-label{position:absolute;top:9px;left:14px;font-size:.7rem;letter-spacing:.09em;font-weight:700;opacity:.7}
.wire{position:relative;height:46px}
.wire.short{height:30px}
.wire::before{content:"";position:absolute;left:50%;top:0;bottom:7px;width:3px;margin-left:-1.5px;background:linear-gradient(to bottom,var(--a),var(--b));-webkit-mask:repeating-linear-gradient(to bottom,#000 0 7px,transparent 7px 13px);mask:repeating-linear-gradient(to bottom,#000 0 7px,transparent 7px 13px);-webkit-mask-size:100% 13px;mask-size:100% 13px;animation:flow .9s linear infinite}
.wire::after{content:"";position:absolute;left:50%;bottom:0;margin-left:-7px;border-left:7px solid transparent;border-right:7px solid transparent;border-top:9px solid var(--b)}
.pill{position:absolute;left:calc(50% + 16px);top:50%;transform:translateY(-50%);font-size:.72rem;opacity:.7;white-space:nowrap}
@keyframes flow{from{-webkit-mask-position:0 0;mask-position:0 0}to{-webkit-mask-position:0 13px;mask-position:0 13px}}
</style>
"""


def node(icon, title, subtitle, color, chips=(), mini=False):
    chip_html = "".join(f'<span class="chip">{c}</span>' for c in chips)
    chips_block = f'<div class="chips">{chip_html}</div>' if chips else ""
    return (
        f'<div class="node{" mini" if mini else ""}" style="background:{color}1f;'
        f'border:1px solid {color}66;border-left:5px solid {color}">'
        f'<div class="node-head"><span class="ico">{icon}</span>'
        f'<div><div class="ttl">{title}</div><div class="sub">{subtitle}</div></div></div>'
        f'{chips_block}</div>'
    )


def wire(label, c_from, c_to, short=False):
    return (
        f'<div class="wire{" short" if short else ""}" style="--a:{c_from};--b:{c_to}">'
        f'<span class="pill">{label}</span></div>'
    )


def overview_html():
    parts = [
        node("🎯", "Project purpose",
             "Ask any question and get a researched, fact-checked report from a team of AI agents.",
             PURPLE_PURPOSE),
        wire("powered by", PURPLE_PURPOSE, CREW_COLOR),
        node("🧠", "CrewAI backend",
             "Orchestrates the agents as a sequential pipeline",
             CREW_COLOR,
             chips=["CrewAI", "Sequential process", "Groq · gpt-oss-120b", "Serper web search"]),
        wire("runs", CREW_COLOR, AGENTS[0]["color"]),
        '<div class="group"><div class="group-label">AGENTS</div>',
    ]
    labels = ["findings", "key claims", "verified claims"]
    for i, a in enumerate(AGENTS):
        parts.append(node(a["icon"], a["name"], a["desc"], a["color"], mini=True))
        if i < len(AGENTS) - 1:
            parts.append(wire(labels[i], a["color"], AGENTS[i + 1]["color"], short=True))
    parts.append("</div>")
    parts.append(wire("streams results to", AGENTS[-1]["color"], STREAMLIT_COLOR))
    parts.append(
        node("🖥️", "Streamlit frontend",
             "You ask, watch each agent's output appear live, and download the report.",
             STREAMLIT_COLOR)
    )
    return '<div class="flow">' + "".join(parts) + "</div>"


# ---------------------------------------------------------------- layout
st.title("🔎 Multi-Agent Research")

left, right = st.columns([3, 2], gap="large")

# Render the overview first so it still shows when the password gate stops the script
with right:
    st.markdown(OVERVIEW_CSS, unsafe_allow_html=True)
    st.markdown("#### How it works")
    st.markdown(overview_html(), unsafe_allow_html=True)

with left:
   

    question = st.text_area("What do you want researched?", max_chars=300)
    run = st.button("Run research", disabled=not question.strip())

    # Outputs live in session_state so they survive reruns (e.g. clicking Download)
    if "outputs" not in st.session_state:
        st.session_state.outputs = [None] * len(AGENTS)
        st.session_state.error = None

    def draw(slot, i, state):
        """Render one agent card. state: 'done' | 'working' | 'waiting'."""
        a = AGENTS[i]
        with slot.container():
            st.markdown(
                f'<div style="background:{a["color"]};color:white;padding:6px 14px;'
                f'border-radius:8px 8px 0 0;font-weight:600">{a["icon"]} {a["name"]}</div>',
                unsafe_allow_html=True,
            )
            with st.container(border=True):
                if state == "done":
                    st.markdown(st.session_state.outputs[i])
                elif state == "working":
                    st.markdown("⏳ *Working...*")
                else:
                    st.caption("Waiting for previous agent...")

    slots = [st.empty() for _ in AGENTS]

    if run:
        st.session_state.outputs = [None] * len(AGENTS)
        st.session_state.error = None
        for i in range(len(AGENTS)):
            draw(slots[i], i, "working" if i == 0 else "waiting")

        crew = ResearchCrew().crew()

        def make_callback(i):
            def on_done(output):
                st.session_state.outputs[i] = output.raw
                draw(slots[i], i, "done")
                if i + 1 < len(AGENTS):
                    draw(slots[i + 1], i + 1, "working")
            return on_done

        for i, task in enumerate(crew.tasks):
            task.callback = make_callback(i)

        try:
            crew.kickoff(inputs={"question": question.strip()})
        except Exception as e:
            st.session_state.error = str(e)
            # Clear the "working" card of whichever agent was interrupted
            for i in range(len(AGENTS)):
                if st.session_state.outputs[i] is None:
                    slots[i].empty()
    else:
        # Not running: redraw any saved results
        for i in range(len(AGENTS)):
            if st.session_state.outputs[i]:
                draw(slots[i], i, "done")

    if st.session_state.error:
        msg = st.session_state.error
        if "RateLimit" in msg or "rate limit" in msg.lower():
            st.warning("Groq's rate limit stopped the run. Wait a minute and try again. Completed steps are shown above.")
        else:
            st.error(f"The crew failed: {msg}")

    final = st.session_state.outputs[-1]
    if final:
        st.download_button("Download report (.md)", final, file_name="report.md")
