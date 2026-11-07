"""Streamlit chat interface for repository explanations and debugging hints."""

from __future__ import annotations

import re
import time

import streamlit as st

from debug_mode import debug_with_repo
from demo_script import DEMO_STEPS, SAMPLE_NOTE
from explain_mode import explain_repo
from repo_loader import RepoLoaderError, load_repo


PACE = 1.0
DEMO_STEP_SECONDS = 11.0
DEMO_TICK_SECONDS = 0.1


ERROR_MARKERS = re.compile(
    r"Traceback \(most recent call last\):"
    r"|^\s*File \"[^\"]+\", line \d+"
    r"|^\s*[A-Za-z_][\w.]*?(?:Error|Exception)\s*:"
    r"|\b(?:SyntaxError|IndentationError|ImportError|ModuleNotFoundError|"
    r"NameError|TypeError|ValueError|KeyError|IndexError|AttributeError)\s*:",
    re.IGNORECASE | re.MULTILINE,
)


@st.cache_resource(show_spinner=False)
def _cached_load_repo(url: str):
    """Cache each loaded repository so chat turns reuse its file data."""
    return load_repo(url)


def _looks_like_error(message: str) -> bool:
    return bool(ERROR_MARKERS.search(message))


def _route_message(message: str, repo_data, hint_level: int) -> tuple[str, str]:
    """Send an error to debug mode and a question to repo explanation mode."""
    if _looks_like_error(message):
        return "debug", debug_with_repo(message, repo_data, hint_level)
    return "explain", explain_repo(repo_data, message)


def _friendly_error(exc: Exception, action: str) -> str:
    if isinstance(exc, RepoLoaderError):
        return str(exc)
    message = str(exc)
    if "GEMINI_API_KEY" in message:
        return "Gemini is not configured yet. Set GEMINI_API_KEY, then try again."
    if "free-tier rate limit" in message.lower():
        return "Gemini is busy or its free-tier limit was reached. Please try again later."
    if isinstance(exc, (ValueError, TypeError)):
        return message
    if action == "load":
        return "I couldn't load that repository. Check that the URL is a public GitHub repo and try again."
    return "I couldn't prepare an answer just now. Check your Gemini key and connection, then try again."


def _reset_chat_for_repo(url: str) -> None:
    if st.session_state.get("loaded_repo_url") != url:
        st.session_state["messages"] = []


def _clear_demo_state() -> None:
    """Remove every app-owned session value used by the demo."""
    for key in list(st.session_state.keys()):
        if key.startswith("demo_"):
            del st.session_state[key]


@st.fragment(run_every=DEMO_TICK_SECONDS * PACE)
def _render_demo() -> None:
    """Render and advance the isolated, sample-only demo replay."""
    if not st.session_state.get("demo_active", False):
        if st.button("Run demo"):
            st.session_state["demo_active"] = True
            st.session_state["demo_started_at"] = time.monotonic()
            st.session_state["demo_step"] = 0
            st.rerun()
        return

    started_at = st.session_state["demo_started_at"]
    elapsed = max(0.0, time.monotonic() - started_at)
    step_duration = DEMO_STEP_SECONDS * PACE
    total_duration = len(DEMO_STEPS) * step_duration

    if elapsed >= total_duration:
        _clear_demo_state()
        st.rerun()

    step_index = min(int(elapsed // step_duration), len(DEMO_STEPS) - 1)
    st.session_state["demo_step"] = step_index
    step = DEMO_STEPS[step_index]
    step_elapsed = elapsed - step_index * step_duration

    with st.container(border=True):
        caption_col, stop_col = st.columns([5, 1])
        caption_col.info(step["caption"])
        if stop_col.button("Stop demo"):
            _clear_demo_state()
            st.rerun()

        st.progress(
            min(elapsed / total_duration, 1.0),
            text=f"Elapsed {elapsed:.1f}s / {total_duration:.0f}s",
        )
        st.caption(SAMPLE_NOTE)

        for completed_step in DEMO_STEPS[:step_index]:
            user_text = completed_step["user_message"]
            if user_text:
                with st.chat_message("user"):
                    st.markdown(user_text)
            with st.chat_message("assistant"):
                if completed_step["mode"] == "explain":
                    st.caption("Repository explanation")
                elif completed_step["hint_level"] is not None:
                    st.caption(f"Debug help · hint level {completed_step['hint_level']}")
                st.markdown(completed_step["response"])

        user_text = step["user_message"]
        is_typing = False
        if user_text:
            typing_duration = min(6.0, len(user_text) * 0.035) * PACE
            is_typing = step_elapsed < typing_duration
            if is_typing:
                fraction = step_elapsed / typing_duration if typing_duration else 1.0
                visible_chars = max(1, int(len(user_text) * fraction))
                visible_text = user_text[:visible_chars] + "▌"
            else:
                visible_text = user_text
            with st.chat_message("user"):
                st.markdown(visible_text)

        if not is_typing:
            with st.chat_message("assistant"):
                if step["mode"] == "explain":
                    st.caption("Repository explanation")
                elif step["hint_level"] is not None:
                    st.caption(f"Debug help · hint level {step['hint_level']}")
                st.markdown(step["response"])


def main() -> None:
    st.set_page_config(page_title="CodeBuddy", page_icon="💬", layout="centered")
    st.title("CodeBuddy")
    st.caption("Explore a GitHub project or get beginner-friendly help with an error.")
    _render_demo()
    demo_active = bool(st.session_state.get("demo_active", False))

    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("loaded_repo_url", "")

    with st.sidebar:
        st.header("Repository")
        repo_url = st.text_input(
            "Public GitHub repo URL",
            placeholder="https://github.com/owner/repository",
            key="repo_url_input",
            disabled=demo_active,
        ).strip()
        load_clicked = st.button(
            "Load repository",
            type="primary",
            use_container_width=True,
            disabled=demo_active,
        )

        st.divider()
        hint_level = st.slider(
            "Debug hint level",
            min_value=1,
            max_value=3,
            value=2,
            help="1 = gentle nudge · 2 = where to look · 3 = full explanation and corrected code",
        )
        st.caption("This setting applies when you paste an error or traceback.")

        if load_clicked:
            if not repo_url:
                st.warning("Enter a public GitHub repository URL first.")
            else:
                _reset_chat_for_repo(repo_url)
                try:
                    with st.spinner("Loading the repository..."):
                        _cached_load_repo(repo_url)
                    st.session_state["loaded_repo_url"] = repo_url
                    st.success("Repository loaded. Ask about it or paste an error below.")
                except Exception as exc:
                    st.session_state["loaded_repo_url"] = ""
                    st.error(_friendly_error(exc, "load"))

    loaded_url = st.session_state.get("loaded_repo_url", "")
    repo_is_ready = bool(loaded_url and repo_url == loaded_url)
    if repo_is_ready:
        st.info(f"Using `{loaded_url}`")
    elif loaded_url and repo_url != loaded_url:
        st.warning("The URL changed. Load this repository before sending a message.")
    else:
        st.info("Enter a public GitHub URL in the sidebar and load it to begin.")

    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            if message.get("mode_label"):
                st.caption(message["mode_label"])
            st.markdown(message["content"])

    user_message = st.chat_input(
        "Ask a question or paste a Python error/traceback...",
        disabled=not repo_is_ready or demo_active,
    )
    if not user_message:
        return

    st.session_state["messages"].append({"role": "user", "content": user_message})
    with st.chat_message("user"):
        st.markdown(user_message)

    mode = "debug" if _looks_like_error(user_message) else "explain"
    with st.chat_message("assistant"):
        st.caption(f"Debug help · hint level {hint_level}" if mode == "debug" else "Repository explanation")
        try:
            with st.spinner("Reading the repository and preparing a helpful response..."):
                repo_data = _cached_load_repo(loaded_url)
                _mode, response = _route_message(user_message, repo_data, hint_level)
            st.markdown(response)
            mode_label = f"Debug help · hint level {hint_level}" if mode == "debug" else "Repository explanation"
            st.session_state["messages"].append(
                {"role": "assistant", "content": response, "mode_label": mode_label}
            )
        except Exception as exc:
            friendly_message = _friendly_error(exc, mode)
            st.error(friendly_message)
            mode_label = f"Debug help · hint level {hint_level}" if mode == "debug" else "Repository explanation"
            st.session_state["messages"].append(
                {"role": "assistant", "content": friendly_message, "mode_label": mode_label}
            )


if __name__ == "__main__":
    main()
