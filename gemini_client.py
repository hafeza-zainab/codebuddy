"""Shared, key-safe Gemini GenerateContent client with model fallback."""

from __future__ import annotations

import json
import os
import socket
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


MODEL_CHAIN = ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.5-flash"]

_KEY_ERROR = "Your Gemini API key was rejected. Check that it is correct."
_BUSY_ERROR = "Gemini is busy right now. Please try again in a minute."
_RATE_LIMIT_ERROR = "Gemini's free-tier rate limit was reached. Please try again later."
_GENERIC_ERROR = "I couldn't get an answer from Gemini just now."
_MAX_ATTEMPTS = 4
_RETRY_WAIT_SECONDS = 2
_TIMEOUT_SECONDS = 30
_GENERATE_CONTENT_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _client_error(message: str) -> RuntimeError:
    return RuntimeError(message)


def _send_request(
    model: str,
    prompt: str,
    system_prompt: str,
    temperature: float,
    max_output_tokens: int,
    api_key: str,
    include_low_thinking: bool,
) -> tuple[int | str, dict | None]:
    generation_config = {
        "temperature": temperature,
        "maxOutputTokens": max_output_tokens,
    }
    if include_low_thinking:
        generation_config["thinkingConfig"] = {"thinkingLevel": "LOW"}

    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": generation_config,
    }
    request = Request(
        _GENERATE_CONTENT_URL.format(model=model),
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )

    try:
        with urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            response_text = response.read().decode("utf-8")
        result = json.loads(response_text)
    except HTTPError as exc:
        try:
            exc.close()
        except Exception:
            pass
        return exc.code, None
    except (TimeoutError, socket.timeout):
        return "timeout", None
    except URLError as exc:
        if isinstance(exc.reason, (TimeoutError, socket.timeout)):
            return "timeout", None
        raise _client_error(_GENERIC_ERROR) from None
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise _client_error(_GENERIC_ERROR) from None
    except Exception:
        raise _client_error(_GENERIC_ERROR) from None

    if not isinstance(result, dict):
        raise _client_error(_GENERIC_ERROR) from None
    return response.status, result


def _extract_text(result: dict) -> str:
    candidates = result.get("candidates") or []
    if not candidates:
        raise _client_error(_GENERIC_ERROR) from None
    parts = candidates[0].get("content", {}).get("parts", [])
    answer = "\n".join(
        part["text"]
        for part in parts
        if isinstance(part, dict) and isinstance(part.get("text"), str) and part["text"]
    )
    if not answer:
        raise _client_error(_GENERIC_ERROR) from None
    return answer.strip()


def _failure_kind(status: int | str) -> str | None:
    if status == 429:
        return "rate_limit"
    if status in (500, 503, "timeout"):
        return "busy"
    return None


def _result_or_continue(
    status: int | str,
    result: dict | None,
) -> str | None:
    if status == 200 and result is not None:
        return _extract_text(result)
    if status in (401, 403):
        raise _client_error(_KEY_ERROR) from None
    return None


def generate_text(
    prompt: str,
    system_prompt: str,
    temperature: float,
    max_output_tokens: int,
    api_key: str | None = None,
) -> str:
    """Generate text with safe retries, fallback models, and key handling."""
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise _client_error(_KEY_ERROR) from None

    attempts = 0
    last_failure: str | None = None
    for model_index, model in enumerate(MODEL_CHAIN):
        if attempts >= _MAX_ATTEMPTS:
            break

        include_low_thinking = model == "gemini-3.5-flash"
        attempts += 1
        status, result = _send_request(
            model, prompt, system_prompt, temperature, max_output_tokens, api_key,
            include_low_thinking,
        )
        answer = _result_or_continue(status, result)
        if answer is not None:
            return answer

        if status == 404:
            last_failure = "model_unavailable"
            continue

        if status == 400 and include_low_thinking and attempts < _MAX_ATTEMPTS:
            # If LOW thinking is rejected, retry this same model once without that option.
            attempts += 1
            status, result = _send_request(
                model, prompt, system_prompt, temperature, max_output_tokens, api_key, False
            )
            answer = _result_or_continue(status, result)
            if answer is not None:
                return answer
            if status == 404:
                last_failure = "model_unavailable"
                continue

        failure = _failure_kind(status)
        if failure is not None:
            last_failure = failure
            has_next_model = model_index + 1 < len(MODEL_CHAIN)
            if attempts < _MAX_ATTEMPTS and has_next_model:
                time.sleep(_RETRY_WAIT_SECONDS)
                continue
            break

        raise _client_error(_GENERIC_ERROR) from None

    if last_failure == "rate_limit":
        raise _client_error(_RATE_LIMIT_ERROR) from None
    if last_failure == "busy":
        raise _client_error(_BUSY_ERROR) from None
    raise _client_error(_GENERIC_ERROR) from None
