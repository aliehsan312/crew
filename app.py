import os
import streamlit as st

st.set_page_config(page_title="Research Crew", page_icon="🔎")

# crew.py reads these at import time, so set them before importing it
for key in ("GROQ_API_KEY", "SERPER_API_KEY"):
    os.environ[key] = st.secrets[key]

from crew import ResearchCrew

# Same order as the tasks in crew.py: research -> analysis -> fact check -> report
AGENTS = [
    {"name": "Researcher",   "icon": "🔍", "color": "#2563EB"},
    {"name": "Analyst",      "icon": "📊", "color": "#7C3AED"},
    {"name": "Fact-Checker", "icon": "✅", "color": "#059669"},
    {"name": "Writer",       "icon": "✍️", "color": "#D97706"},
]

st.title("🔎 Multi-Agent Research")

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