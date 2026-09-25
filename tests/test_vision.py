from lumina.vision import SemanticObservation, quality_gate


def test_semantic_observation_serializes_structured_feedback():
    observation = SemanticObservation(
        caption="a red circle",
        objects=["circle"],
        ocr_text="LUMINA",
        required_elements_found=["circle"],
        missing_elements=[],
    )
    assert observation.as_dict()["objects"] == ["circle"]


def test_quality_gate_passes_only_when_requirements_are_covered():
    passed = quality_gate(SemanticObservation(required_elements_found=["circle", "text"]))
    failed = quality_gate(
        SemanticObservation(required_elements_found=["circle"], missing_elements=["flag"])
    )
    assert passed["passed"] is True
    assert failed["passed"] is False
    assert failed["missing_elements"] == ["flag"]
