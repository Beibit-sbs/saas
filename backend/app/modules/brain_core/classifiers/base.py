from __future__ import annotations

from typing import Any, Protocol


class Classifier(Protocol):
    def classify(self, signal: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        ...
