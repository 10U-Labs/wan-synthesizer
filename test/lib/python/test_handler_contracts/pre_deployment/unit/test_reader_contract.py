from __future__ import annotations

from typing import Any

from test_handler_contracts import ReaderContract

_CFG: dict[str, Any] = {
    "endpoint": "providers",
    "stored_key": "providers/regions.json",
    "stored": [{"id": "denver-1"}],
    "serve_event": {"path": "/x/providers/regions"},
    "serve_expect": [{"id": "denver-1"}],
    "unknown_event": {"path": "/x/providers/bogus"},
    "notbuilt_event": {"path": "/x/providers/regions"},
}


class TestTheReadContract(ReaderContract):
    CFG = _CFG
