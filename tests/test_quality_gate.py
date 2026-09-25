from lumina.engine import VisualEngine
from lumina.vision import SemanticObservation


def test_quality_gated_revision_stops_after_passing_observation(tmp_path):
    engine = VisualEngine(tmp_path)
    initial = engine.create("canvas", 16, 16)
    observations = iter(
        [
            SemanticObservation(required_elements_found=["circle"], missing_elements=["contrast"]),
            SemanticObservation(required_elements_found=["circle", "contrast"]),
        ]
    )

    def provider(_result):
        return next(observations)

    final, report = engine.revise_until_quality_gate(initial, provider, max_attempts=2)
    assert final.revision == initial.revision + 1
    assert report["attempts"] == 1
    assert report["passed"] is True
