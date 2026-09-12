import pytest
from app.models.enums import UserRole, DocumentStatus
from app.validation.engine import BhoomiSetuValidationEngine, RuleStatus
from app.validation.duplicate_engine import DuplicateDetectionEngine

def test_clean_printed_document():
    fields = {"plot_area": "2.500", "area_unit": "Hectare", "survey_number": "123/4", "khata_number": "45", "owner_name": "राम सहाय", "village": "Khajuri Kalan"}
    validator = BhoomiSetuValidationEngine()
    results = validator.validate_fields(fields)
    assert all(r.status == RuleStatus.PASS for r in results)

def test_faded_handwritten_document():
    # Low confidence field simulation
    fields = {"plot_area": "1.250", "area_unit": "Hectare", "survey_number": "123/4A", "khata_number": "45", "owner_name": "राम साहाय"}
    validator = BhoomiSetuValidationEngine()
    results = validator.validate_fields(fields)
    assert len(results) > 0

def test_invalid_area_validation_failure():
    fields = {"plot_area": "-10.0", "area_unit": "Hectare"}
    validator = BhoomiSetuValidationEngine()
    results = validator.validate_fields(fields)
    area_res = next(r for r in results if r.field_name == "plot_area")
    assert area_res.status == RuleStatus.FAIL

def test_duplicate_record_detection():
    candidate = {"village": "Khajuri Kalan", "survey_number": "123/4", "khata_number": "45", "owner_name": "राम साहाय"}
    existing = [{"record_id": "r101", "village": "Khajuri Kalan", "survey_number": "123/4", "khata_number": "45", "owner_name": "राम सहाय"}]

    matches = DuplicateDetectionEngine.evaluate(candidate, existing)
    assert len(matches) == 1
    assert matches[0].is_duplicate_suspect is True

def test_rbac_user_roles():
    assert UserRole.ADMIN.value == "ADMIN"
    assert UserRole.VERIFIER.value == "VERIFIER"
    assert UserRole.AUDITOR.value == "AUDITOR"
