from cognition.sophia.eidos import ConstraintValidationResult, ConstraintViolation


class TestConstraintModels:
    def test_constraint_violation_creation(self):
        v = ConstraintViolation(constraint="NO_EMOJI", severity="critical", detail="Emoji detected")
        assert v.constraint == "NO_EMOJI"
        assert v.severity == "critical"
        assert v.detail == "Emoji detected"

    def test_validation_result_valid(self):
        r = ConstraintValidationResult(is_valid=True, violations=[], confidence=1.0)
        assert r.is_valid is True
        assert len(r.violations) == 0

    def test_validation_result_with_violations(self):
        v = ConstraintViolation(constraint="NO_EMOJI", severity="critical", detail="Emoji detected")
        r = ConstraintValidationResult(is_valid=False, violations=[v], confidence=0.9)
        assert r.is_valid is False
        assert len(r.violations) == 1
        assert r.violations[0].constraint == "NO_EMOJI"

    def test_validation_result_model_dump_json(self):
        v = ConstraintViolation(
            constraint="7GB VRAM", severity="warning", detail="VRAM limit exceeded"
        )
        r = ConstraintValidationResult(is_valid=False, violations=[v], confidence=0.8)
        json_str = r.model_dump_json()
        assert '"constraint"' in json_str
        assert '"7GB VRAM"' in json_str

    def test_validation_result_roundtrip(self):
        v = ConstraintViolation(
            constraint="NO_EMOJI", severity="critical", detail="Emoji detected in output"
        )
        original = ConstraintValidationResult(is_valid=False, violations=[v], confidence=0.95)
        json_str = original.model_dump_json()
        restored = ConstraintValidationResult.model_validate_json(json_str)
        assert restored.is_valid == original.is_valid
        assert len(restored.violations) == len(original.violations)
        assert restored.violations[0].constraint == "NO_EMOJI"
        assert restored.confidence == 0.95

    def test_gateway_prompt_includes_constraint_validation_result_schema(self):
        result = ConstraintValidationResult(is_valid=False, violations=[], confidence=1.0)
        schema = result.model_json_schema()
        assert "properties" in schema
        assert "is_valid" in schema["properties"]
        assert "violations" in schema["properties"]
        assert "confidence" in schema["properties"]
