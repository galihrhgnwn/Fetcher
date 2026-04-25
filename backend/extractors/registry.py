"""
Extractor Registry — manages all extractor plugins and auto-detects the right one per URL.

Usage:
    from backend.extractors.registry import registry
    extractor = registry.resolve("https://www.youtube.com/watch?v=...")
"""
from __future__ import annotations
from typing import Optional
from backend.extractors.base import IExtractor
from backend.extractors.ytdlp_extractor import YtDlpExtractor
from backend.extractors.direct_file_extractor import DirectFileExtractor
from backend.extractors.tikwm_extractor import TikWMExtractor
from backend.extractors.instagram_extractor import InstagramExtractor
from backend.logger import app_logger as log


class ExtractorRegistry:
    def __init__(self):
        self._extractors: list[IExtractor] = []

    def register(self, extractor: IExtractor) -> "ExtractorRegistry":
        """Register an extractor plugin. Returns self for chaining."""
        self._extractors.append(extractor)
        # Keep sorted by priority descending (highest first)
        self._extractors.sort(key=lambda e: e.priority, reverse=True)
        log.debug(f"[Registry] Registered extractor: {extractor.name} (priority={extractor.priority})")
        return self

    def resolve(self, url: str) -> IExtractor:
        """
        Return the highest-priority extractor that can handle the URL.
        Raises RuntimeError if no extractor matches.
        """
        for extractor in self._extractors:
            if extractor.can_handle(url):
                log.debug(f"[Registry] Resolved '{extractor.name}' for {url[:60]}")
                return extractor
        raise RuntimeError(f"No extractor available for URL: {url}")

    def list_extractors(self) -> list[dict]:
        return [
            {"name": e.name, "priority": e.priority}
            for e in self._extractors
        ]

    def __len__(self) -> int:
        return len(self._extractors)


# ─── Singleton registry (pre-loaded with built-in plugins) ────────────────────
registry = ExtractorRegistry()
registry.register(DirectFileExtractor())   # priority 5
registry.register(YtDlpExtractor())        # priority 10
registry.register(TikWMExtractor())        # priority 20
registry.register(InstagramExtractor())    # priority 20
