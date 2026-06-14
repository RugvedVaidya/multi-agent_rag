"""
app.py — Production Streamlit UI for Multi-Agent RAG Assistant
Run: streamlit run app.py
"""

import sys
import time
import streamlit as st
from pathlib import Path
import tempfile
import os

# ── Page config (must be first Streamlit call) ─────────────────
st.set_page_config(
    page_title="RAG Assistant",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background: #0A0F1E !important;
    color: #E2E8F0 !important;
    font-family: 'Inter', sans-serif !important;
}

[data-testid="stSidebar"] {
    background: #0D1425 !important;
    border-right: 1px solid #1E2D4A !important;
}

[data-testid="stHeader"] { background: transparent !important; }

/* ── Sidebar header ── */
.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 0 24px;
    border-bottom: 1px solid #1E2D4A;
    margin-bottom: 24px;
}
.sidebar-logo .icon {
    width: 36px; height: 36px;
    background: linear-gradient(135deg, #3B82F6, #6366F1);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
}
.sidebar-logo .title {
    font-size: 15px; font-weight: 600;
    color: #F1F5F9; letter-spacing: -0.3px;
}
.sidebar-logo .sub {
    font-size: 11px; color: #64748B; margin-top: 1px;
}

/* ── Stats strip ── */
.stat-strip {
    display: flex; gap: 8px; margin-bottom: 20px;
}
.stat-card {
    flex: 1; background: #111827;
    border: 1px solid #1E2D4A;
    border-radius: 8px; padding: 10px 12px;
    text-align: center;
}
.stat-card .val {
    font-size: 20px; font-weight: 700;
    color: #3B82F6; line-height: 1;
}
.stat-card .lbl {
    font-size: 10px; color: #64748B;
    text-transform: uppercase; letter-spacing: 0.5px;
    margin-top: 3px;
}

/* ── Section labels ── */
.section-label {
    font-size: 10px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1px;
    color: #475569; margin-bottom: 8px;
}

/* ── Chat messages ── */
.chat-wrap {
    display: flex; flex-direction: column; gap: 16px;
    padding: 8px 0;
}
.msg {
    display: flex; gap: 12px; align-items: flex-start;
}
.msg.user { flex-direction: row-reverse; }
.avatar {
    width: 32px; height: 32px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; flex-shrink: 0; margin-top: 2px;
}
.avatar.ai {
    background: linear-gradient(135deg, #3B82F6, #6366F1);
}
.avatar.user {
    background: #1E2D4A; border: 1px solid #2D3F5A;
}
.bubble {
    max-width: 82%;
    padding: 12px 16px;
    border-radius: 14px;
    font-size: 14px; line-height: 1.65;
}
.bubble.ai {
    background: #111827;
    border: 1px solid #1E2D4A;
    border-top-left-radius: 4px;
    color: #E2E8F0;
}
.bubble.user {
    background: #1D4ED8;
    border-top-right-radius: 4px;
    color: #fff;
}
.bubble code {
    font-family: 'JetBrains Mono', monospace;
    background: #0A0F1E; padding: 2px 5px;
    border-radius: 3px; font-size: 12px;
}

/* ── Pipeline trace ── */
.pipeline-wrap {
    background: #080D1A;
    border: 1px solid #1E2D4A;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
}
.pipeline-title {
    font-size: 10px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1px;
    color: #475569; margin-bottom: 14px;
}
.agent-row {
    display: flex; align-items: center; gap: 10px;
    padding: 8px 10px; border-radius: 8px;
    margin-bottom: 6px; transition: all 0.2s;
}
.agent-row.idle { background: #0D1425; }
.agent-row.active {
    background: #0F2040;
    border: 1px solid #1D4ED8;
    animation: pulse 1.5s infinite;
}
.agent-row.done { background: #0A1F0F; border: 1px solid #166534; }
.agent-row.pass { background: #0A1F0F; }
.agent-row.revise { background: #1F0A0A; border: 1px solid #991B1B; }

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}
.agent-dot {
    width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}
.agent-dot.idle { background: #1E2D4A; }
.agent-dot.active { background: #3B82F6; box-shadow: 0 0 6px #3B82F6; }
.agent-dot.done { background: #22C55E; }
.agent-dot.revise { background: #EF4444; }
.agent-name {
    font-size: 12px; font-weight: 500; color: #94A3B8; flex: 1;
}
.agent-status {
    font-size: 10px; color: #475569;
    font-family: 'JetBrains Mono', monospace;
}

/* ── Source cards ── */
.source-card {
    background: #0D1425;
    border: 1px solid #1E2D4A;
    border-radius: 8px; padding: 10px 12px;
    margin-bottom: 8px;
    display: flex; align-items: center; gap: 10px;
}
.source-icon {
    font-size: 16px; flex-shrink: 0;
}
.source-name {
    font-size: 12px; font-weight: 500;
    color: #94A3B8; font-family: 'JetBrains Mono', monospace;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.score-badge {
    margin-left: auto; flex-shrink: 0;
    font-size: 10px; font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
    padding: 2px 7px; border-radius: 20px;
}
.score-badge.pass { background: #14532D; color: #4ADE80; }
.score-badge.revise { background: #450A0A; color: #F87171; }
.score-badge.neutral { background: #1E2D4A; color: #64748B; }

/* ── Input area ── */
[data-testid="stChatInput"] {
    background: #111827 !important;
    border: 1px solid #1E2D4A !important;
    border-radius: 12px !important;
    color: #E2E8F0 !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15) !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: #0D1425 !important;
    border: 1px dashed #1E2D4A !important;
    border-radius: 10px !important;
}

/* ── Buttons ── */
.stButton > button {
    background: #1D4ED8 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    padding: 6px 14px !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    background: #2563EB !important;
    transform: translateY(-1px) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #1E2D4A; border-radius: 2px; }

/* ── Empty state ── */
.empty-state {
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    padding: 60px 20px; text-align: center;
}
.empty-icon {
    font-size: 48px; margin-bottom: 16px; opacity: 0.4;
}
.empty-title {
    font-size: 18px; font-weight: 600;
    color: #475569; margin-bottom: 8px;
}
.empty-sub {
    font-size: 13px; color: #334155; max-width: 300px; line-height: 1.6;
}
.suggestion-chips {
    display: flex; flex-wrap: wrap; gap: 8px;
    justify-content: center; margin-top: 20px;
}
.chip {
    background: #111827; border: 1px solid #1E2D4A;
    border-radius: 20px; padding: 6px 14px;
    font-size: 12px; color: #64748B; cursor: pointer;
}

/* ── Verdict badge ── */
.verdict-row {
    display: flex; align-items: center; gap: 8px;
    margin-top: 10px; padding-top: 10px;
    border-top: 1px solid #1E2D4A;
    font-size: 11px; color: #475569;
}
.verdict-badge {
    font-size: 10px; font-weight: 700;
    padding: 2px 8px; border-radius: 20px;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.5px;
}
.verdict-badge.pass { background: #14532D; color: #4ADE80; }
.verdict-badge.revise { background: #450A0A; color: #F87171; }
.verdict-badge.chat { background: #1E2D4A; color: #64748B; }
</style>
""", unsafe_allow_html=True)


# ── Session state init ─────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pipeline_state" not in st.session_state:
    st.session_state.pipeline_state = None
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "db_count" not in st.session_state:
    st.session_state.db_count = 0


# ── Backend imports ────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_backend():
    import orchestrator
    from ingest import ingest_path, get_collection
    return orchestrator, ingest_path, get_collection

try:
    orchestrator_mod, ingest_path_fn, get_collection_fn = load_backend()
    backend_ok = True
except Exception as e:
    backend_ok = False
    backend_error = str(e)


def get_db_count():
    try:
        col = get_collection_fn()
        return col.count()
    except:
        return 0


def get_file_icon(fname: str) -> str:
    ext = Path(fname).suffix.lower()
    return {"pdf": "📄", "txt": "📝", "md": "📋",
            "py": "🐍", "js": "🟨", "ts": "🔷",
            "cpp": "⚙️", "java": "☕"}.get(ext.lstrip("."), "📁")


# ── Sidebar ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div class="icon">⬡</div>
        <div>
            <div class="title">RAG Assistant</div>
            <div class="sub">Multi-Agent · Groq · ChromaDB</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Stats
    db_count = get_db_count()
    msg_count = len([m for m in st.session_state.messages if m["role"] == "user"])
    st.markdown(f"""
    <div class="stat-strip">
        <div class="stat-card">
            <div class="val">{db_count}</div>
            <div class="lbl">Chunks</div>
        </div>
        <div class="stat-card">
            <div class="val">{msg_count}</div>
            <div class="lbl">Queries</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Upload
    st.markdown('<div class="section-label">Knowledge Base</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Upload documents",
        accept_multiple_files=True,
        type=["pdf", "txt", "md", "py", "js", "ts", "java", "cpp", "c", "go"],
        label_visibility="collapsed",
    )

    if uploaded and backend_ok:
        if st.button("⬆ Ingest Documents", use_container_width=True):
            with st.spinner("Ingesting..."):
                with tempfile.TemporaryDirectory() as tmp:
                    for f in uploaded:
                        dest = os.path.join(tmp, f.name)
                        with open(dest, "wb") as out:
                            out.write(f.getbuffer())
                    ingest_path_fn(tmp)
            st.success(f"Ingested {len(uploaded)} file(s)")
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Pipeline legend
    st.markdown('<div class="section-label">Agent Pipeline</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:12px; color:#475569; line-height:2;">
        <span style="color:#3B82F6">⬡</span> Researcher — query rewriting + retrieval<br>
        <span style="color:#6366F1">⬡</span> Analyst — synthesis + citations<br>
        <span style="color:#8B5CF6">⬡</span> Critic — hallucination detection
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🗑 Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_result = None
        st.rerun()

    if not backend_ok:
        st.error(f"Backend error: {backend_error}")


# ── Main layout ────────────────────────────────────────────────
col_chat, col_trace = st.columns([3, 2], gap="large")

# ── RIGHT: Pipeline trace + sources ───────────────────────────
with col_trace:
    st.markdown('<div class="section-label">Pipeline Trace</div>', unsafe_allow_html=True)

    result = st.session_state.last_result
    ps     = st.session_state.pipeline_state  # "idle" | "running" | "done"

    if result and ps == "done":
        is_rag  = result.get("pipeline") == "rag"
        verdict = result.get("critic_verdict", "PASS")
        score   = result.get("critic_score", 1.0)
        queries = result.get("queries_used", [])

        # Researcher
        st.markdown(f"""
        <div class="pipeline-wrap">
            <div class="pipeline-title">Last query trace</div>
            <div class="agent-row done">
                <div class="agent-dot done"></div>
                <div class="agent-name">Researcher</div>
                <div class="agent-status">{"✓ " + str(len(queries)) + " quer" + ("y" if len(queries)==1 else "ies") if is_rag else "skipped"}</div>
            </div>
            <div class="agent-row {'done' if is_rag else 'idle'}">
                <div class="agent-dot {'done' if is_rag else 'idle'}"></div>
                <div class="agent-name">Analyst</div>
                <div class="agent-status">{"✓ answer drafted" if is_rag else "skipped"}</div>
            </div>
            <div class="agent-row {'pass' if verdict == 'PASS' else 'revise' if is_rag else 'idle'}">
                <div class="agent-dot {'done' if verdict == 'PASS' and is_rag else 'revise' if is_rag else 'idle'}"></div>
                <div class="agent-name">Critic</div>
                <div class="agent-status">{"✓ " + verdict + " · " + str(round(score,2)) if is_rag else "skipped"}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Queries used
        if queries:
            st.markdown('<div class="section-label">Queries used</div>', unsafe_allow_html=True)
            for q in queries:
                st.markdown(f"""
                <div style="background:#0D1425; border:1px solid #1E2D4A; border-radius:6px;
                            padding:7px 10px; margin-bottom:6px;
                            font-size:12px; color:#64748B;
                            font-family:'JetBrains Mono',monospace;">
                    {q}
                </div>
                """, unsafe_allow_html=True)

        # Sources
        sources = result.get("sources", [])
        if sources:
            st.markdown('<div class="section-label" style="margin-top:14px;">Sources</div>', unsafe_allow_html=True)
            for s in sources:
                icon = get_file_icon(s)
                badge_cls = "pass" if verdict == "PASS" else "revise"
                badge_txt = verdict
                st.markdown(f"""
                <div class="source-card">
                    <div class="source-icon">{icon}</div>
                    <div class="source-name">{s}</div>
                    <div class="score-badge {badge_cls}">{badge_txt}</div>
                </div>
                """, unsafe_allow_html=True)

        # Faithfulness score bar
        if is_rag:
            st.markdown('<div class="section-label" style="margin-top:14px;">Faithfulness</div>', unsafe_allow_html=True)
            bar_color = "#22C55E" if score >= 0.7 else "#F59E0B" if score >= 0.4 else "#EF4444"
            st.markdown(f"""
            <div style="background:#0D1425; border-radius:6px; overflow:hidden;
                        height:6px; margin-bottom:6px;">
                <div style="width:{int(score*100)}%; height:100%;
                            background:{bar_color}; border-radius:6px;
                            transition: width 0.5s ease;"></div>
            </div>
            <div style="font-size:11px; color:#475569; font-family:'JetBrains Mono',monospace;">
                {round(score*100)}% · {verdict}
            </div>
            """, unsafe_allow_html=True)

    else:
        # Idle state
        st.markdown("""
        <div class="pipeline-wrap">
            <div class="pipeline-title">Waiting for query</div>
            <div class="agent-row idle">
                <div class="agent-dot idle"></div>
                <div class="agent-name">Researcher</div>
                <div class="agent-status">idle</div>
            </div>
            <div class="agent-row idle">
                <div class="agent-dot idle"></div>
                <div class="agent-name">Analyst</div>
                <div class="agent-status">idle</div>
            </div>
            <div class="agent-row idle">
                <div class="agent-dot idle"></div>
                <div class="agent-name">Critic</div>
                <div class="agent-status">idle</div>
            </div>
        </div>
        <div style="font-size:12px; color:#334155; text-align:center; padding:8px 0;">
            Ask a question to see the pipeline run
        </div>
        """, unsafe_allow_html=True)


# ── LEFT: Chat ─────────────────────────────────────────────────
with col_chat:
    st.markdown('<div class="section-label">Conversation</div>', unsafe_allow_html=True)

    # Chat history
    chat_container = st.container()
    with chat_container:
        if not st.session_state.messages:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-icon">⬡</div>
                <div class="empty-title">Ready to research</div>
                <div class="empty-sub">
                    Upload documents using the sidebar, then ask anything about them.
                </div>
                <div class="suggestion-chips">
                    <div class="chip">What are the main findings?</div>
                    <div class="chip">Summarize chapter 1</div>
                    <div class="chip">What does this code do?</div>
                    <div class="chip">List all recommendations</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for msg in st.session_state.messages:
                role    = msg["role"]
                content = msg["content"]
                avatar  = "⬡" if role == "assistant" else "→"
                cls     = "ai" if role == "assistant" else "user"

                st.markdown(f"""
                <div class="msg {cls}">
                    <div class="avatar {cls}">{avatar}</div>
                    <div class="bubble {cls}">{content}</div>
                </div>
                """, unsafe_allow_html=True)

                # Show verdict under assistant messages
                if role == "assistant" and msg.get("meta"):
                    meta    = msg["meta"]
                    verdict = meta.get("critic_verdict", "")
                    score   = meta.get("critic_score", 1.0)
                    pipeline= meta.get("pipeline", "chat")
                    badge_cls = "pass" if verdict == "PASS" else "revise" if verdict == "REVISE" else "chat"
                    badge_txt = verdict if verdict else "CHAT"
                    st.markdown(f"""
                    <div class="verdict-row" style="padding-left:44px;">
                        <span class="verdict-badge {badge_cls}">{badge_txt}</span>
                        {"<span>faithfulness · " + str(round(score*100)) + "%</span>" if pipeline == "rag" else "<span>direct response</span>"}
                    </div>
                    """, unsafe_allow_html=True)

    # ── Chat input ─────────────────────────────────────────────
    if prompt := st.chat_input("Ask anything about your documents…"):
        if not backend_ok:
            st.error("Backend not loaded. Check your configuration.")
        else:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.pipeline_state = "running"

            # Build history for context
            history = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages[:-1]
            ]

            # Run pipeline
            with st.spinner(""):
                result = orchestrator_mod.run(
                    question=prompt,
                    history=history,
                    verbose=False,
                )

            # Store result
            st.session_state.last_result   = result
            st.session_state.pipeline_state = "done"
            st.session_state.messages.append({
                "role":    "assistant",
                "content": result["answer"],
                "meta":    result,
            })
            st.rerun()