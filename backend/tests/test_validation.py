import pytest
from app.validation.engine import BhoomiSetuValidationEngine, RuleSeverity, RuleStatus
from app.validation.duplicate_engine import DuplicateDetectionEngine

def test_validation_positive_area():
    engine = BhoomiSetuValidationEngine()
    
    # Test valid area
    results = engine.validate_fields({"plot_area": "1.250", "area_unit": "Hectare", "survey_number": "123/4"})
    area_res = next(r for r in results if r.field_name == "plot_area")
    assert area_res.status == RuleStatus.PASS

    # Test negative area
    fail_results = engine.validate_fields({"plot_area": "-5.0"})
    fail_res = next(r for r in fail_results if r.field_name == "plot_area")
    assert fail_res.status == RuleStatus.FAIL

def test_duplicate_detection_fuzzy_match():
    candidate = {"village": "Khajuri Kalan", "survey_number": "123/4", "khata_number": "45", "owner_name": "राम साहाय"}
    existing = [{"record_id": "r101", "village": "Khajuri Kalan", "survey_number": "123/4", "khata_number": "45", "owner_name": "राम सहाय"}]

    matches = DuplicateDetectionEngine.evaluate(candidate, existing)
    assert len(matches) == 1
    assert matches[0].is_duplicate_suspect is True
    assert matches[0].duplicate_probability >= 0.70
