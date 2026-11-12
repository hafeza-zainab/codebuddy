"""Load a public GitHub repository's text files and README."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlparse
from urllib.request import Request, urlopen


MAX_FILE_SIZE = 100 * 1024
API_ROOT = "https://api.github.com"
RAW_ROOT = "https://raw.githubusercontent.com"
LOCKFILES = {
    "bun.lock", "bun.lockb", "cargo.lock", "composer.lock", "gemfile.lock",
    "go.sum", "package-lock.json", "pipfile.lock", "pnpm-lock.yaml",
    "poetry.lock", "uv.lock", "yarn.lock", "packages.lock.json",
}
BINARY_EXTENSIONS = {
    ".7z", ".a", ".aac", ".ai", ".apk", ".avi", ".bin", ".bmp",
    ".bz2", ".class", ".dat", ".db", ".dll", ".dylib", ".doc", ".docx",
    ".eot", ".eps", ".exe", ".flac", ".flv", ".gif", ".gz", ".heic",
    ".ico", ".jar", ".jpeg", ".jpg", ".lib", ".m4a", ".m4v", ".mid",
    ".midi", ".mkv", ".mov", ".mp3", ".mp4", ".mpeg", ".mpg", ".o",
    ".obj", ".odt", ".ogg", ".otf", ".pdf", ".pdb", ".png", ".ppt",
    ".pptx", ".psd", ".pyc", ".pyo", ".pyd", ".rar", ".raw", ".so",
    ".sqlite", ".sqlite3", ".swf", ".tar", ".tif", ".tiff", ".ttf",
    ".wav", ".wasm", ".webm", ".webp", ".whl", ".woff", ".woff2",
    ".xls", ".xlsx", ".xz", ".zip", ".zst",
}


class RepoLoaderError(Exception):
    """A clear, user-facing error raised while loading a repository."""


def _request(url: str, *, api: bool = False) -> tuple[bytes, dict[str, str]]:
    headers = {"User-Agent": "CodeBuddy-RepoLoader", "Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if api and token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=20) as response:
            return response.read(), {k.lower(): v for k, v in response.headers.items()}
    except HTTPError as exc:
        if exc.code == 403 and exc.headers.get("X-RateLimit-Remaining") == "0":
            raise RepoLoaderError("GitHub is limiting requests from this host right now. Please wait a few minutes and try again, or run CodeBuddy locally with your own GITHUB_TOKEN (see the README).") from exc
        if exc.code == 403:
            raise RepoLoaderError("GitHub denied the request. Check repository access and try again.") from exc
        if exc.code == 429:
            raise RepoLoaderError("GitHub is limiting requests from this host right now. Please wait a few minutes and try again, or run CodeBuddy locally with your own GITHUB_TOKEN (see the README).") from exc
        if exc.code == 404:
            raise RepoLoaderError("File or repository not found; the repository may be private or the path may be invalid.") from exc
        raise RepoLoaderError(f"GitHub request failed (HTTP {exc.code}).") from exc
    except URLError as exc:
        raise RepoLoaderError(f"Could not reach GitHub: {exc.reason}") from exc


def _api_json(url: str) -> dict:
    payload, _ = _request(url, api=True)
    try:
        return json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RepoLoaderError("GitHub returned an unreadable API response.") from exc


def _parse_repo_url(url: str) -> tuple[str, str, str | None]:
    try:
        parsed = urlparse(url.strip())
    except (AttributeError, ValueError) as exc:
        raise RepoLoaderError("Invalid GitHub URL. Use https://github.com/owner/repository.") from exc
    parts = [unquote(part) for part in parsed.path.strip("/").split("/") if part]
    if (parsed.scheme != "https" or parsed.netloc.lower() not in {"github.com", "www.github.com"}
            or parsed.query or parsed.fragment):
        raise RepoLoaderError("Invalid GitHub URL. Use https://github.com/owner/repository.")
    requested_branch = None
    if len(parts) == 2:
        owner, repo = parts
    elif len(parts) == 4 and parts[2].lower() == "tree" and parts[3] and "/" not in parts[3]:
        owner, repo, _tree_segment, requested_branch = parts
    else:
        # Branch names containing slashes are intentionally not supported in URL paths.
        raise RepoLoaderError("Invalid GitHub URL. Use https://github.com/owner/repository.")
    repo = re.sub(r"\.git$", "", repo, flags=re.IGNORECASE)
    if not owner or not repo:
        raise RepoLoaderError("Invalid GitHub URL. Use https://github.com/owner/repository.")
    return owner, repo, requested_branch


def _is_binary_extension(path: str) -> bool:
    return os.path.splitext(path.lower())[1] in BINARY_EXTENSIONS


def _is_ignored_path(path: str, size: int, mode: str) -> bool:
    components = path.split("/")
    name = components[-1].lower()
    suffix = os.path.splitext(name)[1]
    return (
        size > MAX_FILE_SIZE
        or mode == "120000"
        or any(part.lower() in {".git", "node_modules"} for part in components)
        or name in LOCKFILES
        or name.endswith((".lock", ".lockb"))
        or suffix in BINARY_EXTENSIONS
    )


def load_repo(url: str) -> tuple[list[str], str, Callable[[str], str]]:
    """Return (text file paths, README text, get_file(path)) for a public repo."""
    owner, repo, requested_branch = _parse_repo_url(url)
    encoded_owner, encoded_repo = quote(owner, safe=""), quote(repo, safe="")
    repo_endpoint = f"{API_ROOT}/repos/{encoded_owner}/{encoded_repo}"
    try:
        metadata = _api_json(repo_endpoint)
    except RepoLoaderError as exc:
        if "not found" in str(exc).lower():
            raise RepoLoaderError("Repository not found or private. Confirm the public GitHub URL.") from exc
        raise

    branch = requested_branch or metadata.get("default_branch")
    if not branch:
        raise RepoLoaderError("This repository is empty; it has no default branch yet.")
    branch_ref = quote(branch, safe="")
    try:
        tree_data = _api_json(f"{repo_endpoint}/git/trees/{branch_ref}?recursive=1")
    except RepoLoaderError as exc:
        if requested_branch and "not found" in str(exc).lower():
            raise RepoLoaderError(f"Branch '{requested_branch}' was not found in this repository.") from exc
        raise
    if tree_data.get("truncated"):
        raise RepoLoaderError(
            "This repository is too large to load fully because GitHub truncated its recursive file tree."
        )
    entries = tree_data.get("tree", [])
    all_blobs = {
        item["path"]: item
        for item in entries
        if item.get("type") == "blob" and item.get("path")
    }
    blobs = {
        path: item for path, item in all_blobs.items()
        if not _is_ignored_path(path, item.get("size", 0), item.get("mode", ""))
    }
    if not blobs:
        raise RepoLoaderError("This repository is empty or has no eligible text files.")

    ref = quote(branch, safe="")
    raw_base = f"{RAW_ROOT}/{encoded_owner}/{encoded_repo}/{ref}"
    content_cache: dict[str, str] = {}

    def get_file(path: str) -> str:
        """Fetch one eligible text file from the loaded repository."""
        if path in content_cache:
            return content_cache[path]
        if path not in all_blobs:
            raise RepoLoaderError(f"'{path}' is not an eligible file in this repository.")
        item = all_blobs[path]
        if item.get("size", 0) > MAX_FILE_SIZE:
            return "This file is larger than the 100 KB display limit."
        if _is_binary_extension(path):
            return "This file is binary and cannot be displayed as text."
        if path not in blobs:
            raise RepoLoaderError(f"'{path}' is not an eligible file in this repository.")

        raw_path = "/".join(quote(part, safe="") for part in path.split("/"))
        content, _ = _request(f"{raw_base}/{raw_path}")
        if len(content) > MAX_FILE_SIZE:
            result = "This file is larger than the 100 KB display limit."
        else:
            try:
                decoded = content.decode("utf-8")
                has_binary_control = any(byte < 32 and byte not in (9, 10, 12, 13) for byte in content)
                if b"\0" in content or has_binary_control:
                    result = "This file is binary and cannot be displayed as text."
                else:
                    result = decoded
            except UnicodeDecodeError:
                result = "This file is binary or not UTF-8 text, so it cannot be displayed."
        content_cache[path] = result
        return result

    text_paths = sorted(blobs)

    readme_path = next(
        (path for path in text_paths if "/" not in path and os.path.splitext(path)[0].lower() == "readme"),
        None,
    )
    readme_text = get_file(readme_path) if readme_path else ""
    return text_paths, readme_text, get_file


def main() -> int:
    parser = argparse.ArgumentParser(description="List the text files and README in a public GitHub repository.")
    parser.add_argument("url", help="Public GitHub repository URL")
    args = parser.parse_args()
    try:
        file_tree, readme, _get_file = load_repo(args.url)
    except RepoLoaderError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("File tree:")
    for path in file_tree:
        print(path)
    print("\nREADME (first 20 lines):")
    print("\n".join(readme.splitlines()[:20]) or "(No README found.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
