"""Base detector interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from lib.models import DetectedTechnology, DetectionTarget


class BaseDetector(ABC):
    """All detectors inherit from this."""

    name: str = "base"

    @abstractmethod
    async def detect(self, target: DetectionTarget) -> list[DetectedTechnology]:
        """Run detection and return a list of detected technologies."""
        raise NotImplementedError
