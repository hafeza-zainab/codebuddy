"""Load a public GitHub repository's text files and README."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
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
    ".7z", ".a", ".avi", ".bin", ".bmp", ".class", ".dll", ".dylib",
    ".exe", ".gif", ".gz", ".ico", ".jar", ".jpeg", ".jpg", ".mp3",
    ".mp4", ".o", ".pdf", ".png", ".so", ".sqlite", ".tar", ".tif",
    ".tiff", ".webp", ".woff", ".woff2", ".zip",
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
            raise RepoLoaderError("GitHub API rate limit reached. Set GITHUB_TOKEN and try again later.") from exc
        if exc.code == 403:
            raise RepoLoaderError("GitHub denied the request. Check repository access and try again.") from exc
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


def _parse_repo_url(url: str) -> tuple[str, str]:
    try:
        parsed = urlparse(url.strip())
    except (AttributeError, ValueError) as exc:
        raise RepoLoaderError("Invalid GitHub URL. Use https://github.com/owner/repository.") from exc
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if (parsed.scheme != "https" or parsed.netloc.lower() not in {"github.com", "www.github.com"}
            or len(parts) != 2 or parsed.query or parsed.fragment):
        raise RepoLoaderError("Invalid GitHub URL. Use https://github.com/owner/repository.")
    owner, repo = parts
    repo = re.sub(r"\.git$", "", repo, flags=re.IGNORECASE)
    if not owner or not repo:
        raise RepoLoaderError("Invalid GitHub URL. Use https://github.com/owner/repository.")
    return owner, repo


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
    owner, repo = _parse_repo_url(url)
    encoded_owner, encoded_repo = quote(owner, safe=""), quote(repo, safe="")
    repo_endpoint = f"{API_ROOT}/repos/{encoded_owner}/{encoded_repo}"
    try:
        metadata = _api_json(repo_endpoint)
    except RepoLoaderError as exc:
        if "not found" in str(exc).lower():
            raise RepoLoaderError("Repository not found or private. Confirm the public GitHub URL.") from exc
        raise

    branch = metadata.get("default_branch")
    if not branch:
        raise RepoLoaderError("This repository is empty; it has no default branch yet.")
    branch_ref = quote(branch, safe="")
    tree_data = _api_json(f"{repo_endpoint}/git/trees/{branch_ref}?recursive=1")
    entries = tree_data.get("tree", [])
    blobs = {
        item["path"]: item
        for item in entries
        if item.get("type") == "blob"
        and not _is_ignored_path(item.get("path", ""), item.get("size", 0), item.get("mode", ""))
    }
    if not blobs:
        raise RepoLoaderError("This repository is empty or has no eligible text files.")

    ref = quote(branch, safe="")
    raw_base = f"{RAW_ROOT}/{encoded_owner}/{encoded_repo}/{ref}"
    content_cache: dict[str, str] = {}

    def get_file(path: str) -> str:
        """Fetch one eligible text file from the loaded repository."""
        if path not in blobs:
            raise RepoLoaderError(f"'{path}' is not an eligible file in this repository.")
        if path not in content_cache:
            raw_path = "/".join(quote(part, safe="") for part in path.split("/"))
            content, _ = _request(f"{raw_base}/{raw_path}")
            if len(content) > MAX_FILE_SIZE:
                raise RepoLoaderError(f"'{path}' exceeds the 100 KB file size limit.")
            try:
                decoded = content.decode("utf-8")
            except UnicodeDecodeError:
                decoded = None
            has_binary_control = any(byte < 32 and byte not in (9, 10, 12, 13) for byte in content)
            if b"\0" in content or decoded is None or has_binary_control:
                blobs.pop(path, None)
                raise RepoLoaderError(f"'{path}' is a binary file and cannot be returned as text.")
            content_cache[path] = decoded
        return content_cache[path]

    # Probe candidates once so binary files are excluded from the returned tree.
    text_paths: list[str] = []
    for path in sorted(blobs):
        try:
            get_file(path)
            text_paths.append(path)
        except RepoLoaderError as exc:
            if "binary file" not in str(exc):
                raise
    if not text_paths:
        raise RepoLoaderError("This repository has no eligible text files.")

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
