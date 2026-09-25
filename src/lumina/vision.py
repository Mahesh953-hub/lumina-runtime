from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class SemanticObservation:
    caption: str = ""
    objects: list[str] = field(default_factory=list)
    relationships: list[dict] = field(default_factory=list)
    ocr_text: str = ""
    required_elements_found: list[str] = field(default_factory=list)
    missing_elements: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "caption": self.caption,
            "objects": self.objects,
            "relationships": self.relationships,
            "ocr_text": self.ocr_text,
            "required_elements_found": self.required_elements_found,
            "missing_elements": self.missing_elements,
        }


class SemanticVisionProvider(Protocol):
    def analyze(
        self, image_path: str, requirements: list[str] | None = None
    ) -> SemanticObservation:
        """Analyze an image without executing agent-provided code."""


def quality_gate(observation: SemanticObservation, minimum_coverage: float = 0.8) -> dict:
    required = len(observation.required_elements_found) + len(observation.missing_elements)
    coverage = len(observation.required_elements_found) / required if required else 1.0
    return {
        "passed": coverage >= minimum_coverage and not observation.missing_elements,
        "required_element_coverage": round(coverage, 4),
        "missing_elements": observation.missing_elements,
        "caption": observation.caption,
    }
