import pytest
import os
from app.ai.factory import get_ocr_provider
from app.ai.mock_provider import MockOCRProvider

def test_ocr_provider_factory():
    os.environ["AI_PROVIDER"] = "mock"
    provider = get_ocr_provider()
    assert isinstance(provider, MockOCRProvider)

def test_ocr_mock_extraction():
    provider = MockOCRProvider()
    res = provider.process_image("dummy_path.png")
    
    assert res.detected_language == "hi"
    assert len(res.extracted_fields) >= 7
    
    survey_field = next(f for f in res.extracted_fields if f.field_name == "survey_number")
    assert survey_field.value == "123/4"
    assert len(survey_field.bounding_box) == 4
    assert survey_field.confidence >= 0.80
