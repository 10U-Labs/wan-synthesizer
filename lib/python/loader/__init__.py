from __future__ import annotations

import csv
import json
import os
import subprocess
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

DEFAULT_API = "https://api.10ulabs.com"
API_KEY_VARIABLE = "API_KEY"
NO_COMMIT = "0" * 40
RETRIED = frozenset({429, 502, 503, 504})
ATTEMPTS = 5
RETRY_PAUSE_SECONDS = 1.0
SETTLE_PAUSE_SECONDS = 5.0
DEFAULT_SETTLE_SECONDS = 300.0

Sleep = Callable[[float], None]


class Api:
    def __init__(self, base: str, bearer: str, sleep: Sleep) -> None:
        self._base = base.rstrip("/")
        self._headers = {"Authorization": f"Bearer {bearer}", "Content-Type": "application/json"}
        self._sleep = sleep

    def _once(self, method: str, path: str, body: bytes | None) -> Any:
        request = urllib.request.Request(
            f"{self._base}/{path}", data=body, method=method, headers=self._headers)
        with urllib.request.urlopen(request, timeout=60) as response:
            answer = response.read()
        return json.loads(answer) if answer else None

    def _call(self, method: str, path: str, body: Any = None) -> Any:
        encoded = None if body is None else json.dumps(body).encode()
        for attempt in range(ATTEMPTS - 1):
            try:
                return self._once(method, path, encoded)
            except urllib.error.HTTPError as refusal:
                if refusal.code not in RETRIED:
                    raise
                print(f"  {method} /{path} -> {refusal.code}, trying again", flush=True)
                self._sleep(RETRY_PAUSE_SECONDS * 2 ** attempt)
        return self._once(method, path, encoded)

    def get(self, path: str) -> Any:
        return self._call("GET", path)

    def post(self, path: str, body: Any) -> Any:
        return self._call("POST", path, body)

    def delete(self, path: str) -> None:
        self._call("DELETE", path)


def key() -> str:
    return os.environ.get(API_KEY_VARIABLE, "")


def rows(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def changed_paths(repository: Path, since: str, under: Sequence[str]) -> list[str] | None:
    if not since or since == NO_COMMIT:
        return None
    completed = subprocess.run(
        ["git", "diff", "--name-only", "--no-renames", since, "HEAD", "--", *under],
        cwd=repository, capture_output=True, text=True, check=True)
    return completed.stdout.split()


def settled(
        read: Callable[[], Any], agrees: Callable[[Any], bool], settle_seconds: float,
        sleep: Sleep) -> bool:
    for _ in range(int(settle_seconds // SETTLE_PAUSE_SECONDS) + 1):
        if agrees(read()):
            return True
        print("the listing has not caught up yet", flush=True)
        sleep(SETTLE_PAUSE_SECONDS)
    return False
