"""
Basic unit tests for BhoomiSetu.

Tests the core data models, the OCR provider factory, and the extraction parser.
"""
import os
import pytest

os.environ["AI_PROVIDER"] = "mock"
os.environ["SARVAM_API_KEY"] = ""

from app.models.enums import UserRole, DocumentStatus
from app.ai.factory import get_ocr_provider
from app.ai.mock_provider import MockOCRProvider
from app.ai.extraction import LandRecordExtractionParser
from app.ai.ocr_interface import OCRToken


def test_user_roles():
    assert UserRole.ADMIN.value == "ADMIN"
    assert UserRole.VERIFIER.value == "VERIFIER"
    assert UserRole.SUPERVISOR.value == "SUPERVISOR"


def test_document_statuses():
    assert DocumentStatus.UPLOADED.value == "UPLOADED"
    assert DocumentStatus.NEEDS_VERIFICATION.value == "NEEDS_VERIFICATION"
    assert DocumentStatus.APPROVED.value == "APPROVED"
    assert DocumentStatus.REJECTED.value == "REJECTED"
    assert DocumentStatus.FAILED.value == "FAILED"


def test_mock_provider_returned_by_factory():
    provider = get_ocr_provider()
    assert isinstance(provider, MockOCRProvider), f"Expected MockOCRProvider, got {type(provider).__name__}"


def test_mock_ocr_returns_8_core_fields():
    provider = MockOCRProvider()
    result = provider.process_image("")
    field_names = {f.field_name for f in result.extracted_fields}

    expected = {"owner_name", "survey_number", "khata_number", "plot_area", "area_unit", "village", "tehsil", "district"}
    assert expected.issubset(field_names), f"Missing fields: {expected - field_names}"


def test_extraction_parser_survey_number():
    text = "खसरा नं 456/2"
    tokens = [OCRToken(text="456/2", confidence=0.95, bbox=[10, 10, 50, 30])]
    fields = LandRecordExtractionParser.extract_fields_from_ocr(text, tokens, 1, "test")
    survey_fields = [f for f in fields if f.field_name == "survey_number"]
    assert len(survey_fields) > 0, "Survey number not extracted"
    assert survey_fields[0].value == "456/2"


def test_extraction_parser_area():
    text = "क्षेत्रफल: 3.750 हेक्टेयर"
    tokens = [OCRToken(text="3.750", confidence=0.90, bbox=[10, 10, 50, 30])]
    fields = LandRecordExtractionParser.extract_fields_from_ocr(text, tokens, 1, "test")
    area_fields = [f for f in fields if f.field_name == "plot_area"]
    assert len(area_fields) > 0, "Area not extracted"
    assert area_fields[0].value == "3.750"


def test_confidence_scores_are_valid():
    provider = MockOCRProvider()
    result = provider.process_image("")
    for f in result.extracted_fields:
        assert 0.0 <= f.confidence <= 1.0, f"Invalid confidence {f.confidence} for {f.field_name}"
        assert f.value is not None and len(f.value) > 0, f"Empty value for {f.field_name}"
