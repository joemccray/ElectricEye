import os

import pytest
import requests


@pytest.fixture(autouse=True)
def _block_external_http(monkeypatch):
    if os.getenv("NO_EXTERNAL_HTTP") != "1":
        return

    def _blocked(*args, **kwargs):
        raise RuntimeError(
            "External HTTP is disabled in tests (set NO_EXTERNAL_HTTP=0 to allow)."
        )

    for method in ("get", "post", "put", "delete", "patch", "head", "options"):
        monkeypatch.setattr(requests, method, _blocked)
