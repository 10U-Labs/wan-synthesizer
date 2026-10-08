from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from repo_utils import REPO_ROOT

DEFAULT_API = "https://api.10ulabs.com"
API_KEY_VARIABLE = "API_KEY"
NO_COMMIT = "0" * 40
RETRIED = frozenset({429, 502, 503, 504})
ATTEMPTS = 5
RETRY_PAUSE_SECONDS = 1.0
SETTLE_PAUSE_SECONDS = 5.0
DEFAULT_SETTLE_SECONDS = 300.0
NO_KEY = 2

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

    def listing(self, path: str) -> list[dict[str, Any]]:
        listed: list[dict[str, Any]] = self.get(path)
        return listed

    def post(self, path: str, body: Any) -> Any:
        return self._call("POST", path, body)

    def put(self, path: str, body: Any) -> Any:
        return self._call("PUT", path, body)

    def delete(self, path: str) -> Any:
        return self._call("DELETE", path)


def key() -> str:
    return os.environ.get(API_KEY_VARIABLE, "")


def keyed_api(base: str, sleep: Sleep) -> Api | None:
    bearer = key()
    if not bearer:
        print("the environment carries no key for the API", file=sys.stderr, flush=True)
        return None
    return Api(base, bearer, sleep)


def started(
        argv: Sequence[str], sleep: Sleep, prog: str, description: str,
        appended: Sequence[str] = ()) -> tuple[argparse.Namespace, Api | None]:
    parser = argparse.ArgumentParser(prog=prog, description=description)
    parser.add_argument("--api", default=DEFAULT_API)
    parser.add_argument("--repository", type=Path, default=REPO_ROOT)
    parser.add_argument("--since", default="")
    parser.add_argument("--settle-seconds", type=float, default=DEFAULT_SETTLE_SECONDS)
    for option in appended:
        parser.add_argument(option, action="append", default=[])
    args = parser.parse_args(argv)
    return args, keyed_api(args.api, sleep)


def place_body(row: dict[str, str]) -> dict[str, Any]:
    return {
        "name": row["Name"],
        "municipality": row["Municipality"],
        "state": row["State"],
        "country": row["Country"],
        "latitude": float(row["Latitude"]),
        "longitude": float(row["Longitude"]),
    }


def sorted_without_ids(listed: list[dict[str, Any]]) -> list[str]:
    return sorted(
        json.dumps({name: value for name, value in row.items() if name != "id"}, sort_keys=True)
        for row in listed)


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
