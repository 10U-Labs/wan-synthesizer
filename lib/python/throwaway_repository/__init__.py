from __future__ import annotations

import subprocess
from pathlib import Path


def git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments], cwd=repository, capture_output=True, text=True, check=True)
    return completed.stdout.strip()


def commit(repository: Path, message: str) -> str:
    git(repository, "add", "--all")
    git(repository, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", message)
    return git(repository, "rev-parse", "HEAD")


def write(repository: Path, relative: str, text: str) -> None:
    path = repository / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
