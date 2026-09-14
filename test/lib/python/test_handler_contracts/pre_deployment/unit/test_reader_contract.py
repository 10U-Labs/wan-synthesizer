from __future__ import annotations

from typing import Any

from test_handler_contracts import ReaderContract

_CFG: dict[str, Any] = {
    "endpoint": "carriers",
    "stored_key": "carriers/telia/pops.json",
    "stored": [{"id": "denver-1"}],
    "serve_event": {
        "pathParameters": {"carrier": "telia"},
        "path": "/x/carriers/telia/pops",
    },
    "serve_expect": [{"id": "denver-1"}],
    "unknown_event": {
        "pathParameters": {"carrier": "telia"},
        "path": "/x/carriers/telia/regions",
    },
    "notbuilt_event": {
        "pathParameters": {"carrier": "arelion"},
        "path": "/x/carriers/arelion/pops",
    },
}


class TestTheReadContract(ReaderContract):
    CFG = _CFG
