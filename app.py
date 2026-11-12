"""Streamlit chat interface for repository explanations and debugging hints."""

from __future__ import annotations

import os
import re
import time
from pathlib import Path

import streamlit as st

from debug_mode import debug_with_repo
from demo_script import DEMO_STEPS, SAMPLE_NOTE
from explain_mode import explain_repo
from repo_loader import RepoLoaderError, load_repo


PACE = 1.0
DEMO_STEP_SECONDS = 11.0
DEMO_TICK_SECONDS = 0.5

AUDIO_CLIP_PATHS = tuple(
    Path(__file__).resolve().parent / "static" / "audio" / f"step_{step:02d}.mp3"
    for step in range(1, 10)
)
AUDIO_CLIPS_AVAILABLE = all(path.is_file() for path in AUDIO_CLIP_PATHS)

NARRATION_CONTROLLER_HTML = r"""
<style>
  #codebuddy-demo-audio-enable {
    position: fixed;
    left: 12px;
    bottom: 12px;
    z-index: 10000;
    border: 0;
    border-radius: 6px;
    padding: 8px 12px;
    color: white;
    background: #2457a7;
    font: inherit;
    cursor: pointer;
  }
  #codebuddy-demo-audio-enable[hidden] {
    display: none !important;
  }
</style>
<button id="codebuddy-demo-audio-enable" type="button" hidden>
  Tap to enable sound
</button>
<script>
(() => {
  const singletonKey = "__codebuddyNarration";
  if (window[singletonKey]) return;

  const urls = [
    "/app/static/audio/step_01.mp3",
    "/app/static/audio/step_02.mp3",
    "/app/static/audio/step_03.mp3",
    "/app/static/audio/step_04.mp3",
    "/app/static/audio/step_05.mp3",
    "/app/static/audio/step_06.mp3",
    "/app/static/audio/step_07.mp3",
    "/app/static/audio/step_08.mp3",
    "/app/static/audio/step_09.mp3"
  ];
  const controller = {
    clips: [],
    lastStep: null,
    currentStep: null,
    currentAudio: null,
    markerAbsentSince: Date.now(),
    stopped: false,
    observer: null
  };
  window[singletonKey] = controller;

  const debug = (...parts) => {
    if (window.__codebuddyAudioDebug === true) {
      console.log("[codebuddy-audio]", ...parts);
    }
  };
  const tapButton = () => document.getElementById("codebuddy-demo-audio-enable");
  const hideTapButton = () => {
    const button = tapButton();
    if (button) button.hidden = true;
  };
  const showTapButton = () => {
    const button = tapButton();
    if (button) button.hidden = false;
  };
  const resetClip = (clip) => {
    try {
      clip.pause();
      clip.currentTime = 0;
    } catch (error) {
      debug("clip-reset-error", error && error.message);
    }
  };
  const pauseAndResetAll = () => {
    controller.clips.forEach(resetClip);
    controller.currentAudio = null;
    controller.currentStep = null;
  };
  const pauseAndResetOthers = (current) => {
    controller.clips.forEach((clip) => {
      if (clip !== current) resetClip(clip);
    });
  };
  const playStep = (step, reason) => {
    const clip = controller.clips[step - 1];
    if (!clip) return;

    pauseAndResetOthers(clip);
    try {
      clip.currentTime = 0;
    } catch (error) {
      debug("clip-seek-error", step, error && error.message);
    }
    controller.currentStep = step;
    controller.currentAudio = clip;
    controller.lastStep = step;

    const onRejected = (error) => {
      if (controller.currentAudio !== clip) return;
      showTapButton();
      debug("play-rejected", step, error && error.name);
    };
    try {
      const playback = clip.play();
      if (playback && typeof playback.then === "function") {
        playback.then(() => {
          if (controller.currentAudio === clip) hideTapButton();
          debug("play-started", step, reason);
        }).catch(onRejected);
      } else {
        hideTapButton();
        debug("play-requested", step, reason);
      }
    } catch (error) {
      onRejected(error);
    }
  };
  const startNewRun = (reason, observedStep) => {
    pauseAndResetAll();
    controller.lastStep = null;
    controller.markerAbsentSince = null;
    controller.stopped = false;
    playStep(observedStep, reason);
    debug("new-run-started", reason, observedStep);
  };

  controller.clips = urls.map((url, index) => {
    const clip = new Audio();
    clip.preload = "auto";
    clip.src = url;
    clip.addEventListener("error", () => {
      console.error("[codebuddy-audio] clip load error", index + 1, clip.error && clip.error.message);
    });
    clip.addEventListener("playing", () => {
      if (controller.currentAudio === clip) hideTapButton();
    });
    clip.load();
    return clip;
  });

  const scanMarker = () => {
    const markers = document.querySelectorAll("[data-codebuddy-demo-step]");
    if (markers.length === 0) {
      if (controller.markerAbsentSince === null) controller.markerAbsentSince = Date.now();
      debug("marker-absent");
      return;
    }

    const marker = markers[markers.length - 1];
    const step = Number(marker.getAttribute("data-codebuddy-demo-step"));
    if (!Number.isInteger(step) || step < 1 || step > 9) return;

    if (controller.stopped) {
      if (controller.markerAbsentSince === null) return;
      startNewRun("after-stop", step);
      return;
    }

    if (controller.lastStep !== null && step < controller.lastStep) {
      startNewRun("step-went-backward", step);
      return;
    }

    controller.markerAbsentSince = null;
    if (step !== controller.lastStep) {
      playStep(step, "step-marker");
    } else {
      debug("repeat-ignored", step);
    }
  };

  document.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;
    const button = target.closest("button");
    if (!button || button.textContent.trim() !== "Stop demo") return;

    pauseAndResetAll();
    controller.lastStep = null;
    controller.markerAbsentSince = null;
    controller.stopped = true;
    hideTapButton();
    debug("stopped-by-user");
  }, true);

  document.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof Element) || !target.closest("#codebuddy-demo-audio-enable")) return;
    event.preventDefault();
    if (controller.currentStep !== null && !controller.stopped) {
      playStep(controller.currentStep, "tap-to-enable");
    }
  }, true);

  controller.observer = new MutationObserver(() => {
    try {
      scanMarker();
    } catch (error) {
      debug("observer-error", error && error.message);
    }
  });
  controller.observer.observe(document.body, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["data-codebuddy-demo-step"]
  });
  scanMarker();
  debug("controller-installed");
})();
</script>
"""


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
    entered_key = st.session_state.get("user_api_key", "")
    api_key = entered_key.strip() if isinstance(entered_key, str) else ""
    api_key = api_key or None
    if _looks_like_error(message):
        return "debug", debug_with_repo(message, repo_data, hint_level, api_key=api_key)
    return "explain", explain_repo(repo_data, message, api_key=api_key)


def _friendly_error(exc: Exception, action: str) -> str:
    message = str(exc)
    entered_key = st.session_state.get("user_api_key", "")
    if isinstance(entered_key, str) and entered_key:
        message = message.replace(entered_key, "[hidden]")
    if isinstance(exc, RepoLoaderError):
        return message
    if "GEMINI_API_KEY" in message:
        return "Gemini is not configured yet. Set GEMINI_API_KEY, then try again. Enter a key in the sidebar or use the Run demo button."
    if "Your Gemini API key was rejected." in message:
        if not (isinstance(entered_key, str) and entered_key.strip()) and not os.getenv("GEMINI_API_KEY"):
            return "Gemini is not configured yet. Set GEMINI_API_KEY, then try again. Enter a key in the sidebar or use the Run demo button."
        return "Gemini could not use that key. Check the key field in the sidebar, or use the Run demo button."
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
        run_demo_col, sound_col = st.columns([1, 1])
        sound_enabled = sound_col.checkbox(
            "Play narration",
            value=False,
            help="Optional voice-over. If you hear nothing, your browser may be blocking autoplay.",
        )
        if run_demo_col.button("Run demo"):
            st.session_state["demo_active"] = True
            st.session_state["demo_started_at"] = time.monotonic()
            st.session_state["demo_step"] = -1
            st.session_state["demo_sound"] = bool(sound_enabled)
            st.rerun()
        return

    run_demo_col, sound_col = st.columns([1, 1])
    run_demo_col.button("Run demo", disabled=True)
    sound_col.checkbox(
        "Play narration",
        value=st.session_state.get("demo_sound", False),
        disabled=True,
        help="Optional voice-over. If you hear nothing, your browser may be blocking autoplay.",
    )

    started_at = st.session_state["demo_started_at"]
    elapsed = max(0.0, time.monotonic() - started_at)
    narration_on = bool(st.session_state.get("demo_sound", False))
    narration_pause_seconds = 2.0 if narration_on else 0.0
    step_duration = (DEMO_STEP_SECONDS - narration_pause_seconds) * PACE
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

        if narration_on and AUDIO_CLIPS_AVAILABLE:
            st.html(
                f'<span data-codebuddy-demo-step="{step_index + 1}" style="display:none"></span>'
            )

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

    controller_active = bool(
        st.session_state.get("demo_active", False)
        and st.session_state.get("demo_sound", False)
        and AUDIO_CLIPS_AVAILABLE
    )
    if controller_active:
        st.html(NARRATION_CONTROLLER_HTML, unsafe_allow_javascript=True)

    _render_demo()
    demo_active = bool(st.session_state.get("demo_active", False))
    narration_on = demo_active and bool(st.session_state.get("demo_sound", False))

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
            disabled=narration_on,
        )
        st.caption("This setting applies when you paste an error or traceback.")
        st.text_input(
            "Your Gemini API key (optional)",
            type="password",
            key="user_api_key",
            help="Used only for this browser session. Not saved. Get a free key at aistudio.google.com/apikey.",
            disabled=narration_on,
        )

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
    if not demo_active:
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
