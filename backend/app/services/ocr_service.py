from typing import Dict, Any, List
import random

class SarvamOCRAdapter:
    """Sarvam AI OCR Abstraction Adapter (Mock implementation for local MVP execution)"""

    def __init__(self, api_key: str = "mock_key"):
        self.api_key = api_key

    def extract_text_and_fields(self, image_path: str) -> Dict[str, Any]:
        """
        Simulates multilingual OCR & 8 MVP Land Fields Extraction:
        owner_name, survey_number, khata_number, plot_area, area_unit, village, tehsil, district
        """
        return {
            "full_text": "प्रारूप खसरा। खाता संख्या 45, खसरा नं 123/4, खातेदार: राम सहाय, क्षेत्रफल: 1.250 हेक्टेयर, ग्राम: खजूरी कलां, तहसील: हुजूर, जिला: भोपाल",
            "detected_language": "hi",
            "fields": [
                {
                    "field_name": "owner_name",
                    "value": "राम सहाय",
                    "normalized_value": "राम सहाय",
                    "confidence": 0.92,
                    "raw_text": "खातेदार: राम सहाय",
                    "source_bbox": [120, 220, 480, 260],
                    "source_page": 1
                },
                {
                    "field_name": "survey_number",
                    "value": "123/4",
                    "normalized_value": "123/4",
                    "confidence": 0.95,
                    "raw_text": "खसरा नं 123/4",
                    "source_bbox": [120, 280, 380, 320],
                    "source_page": 1
                },
                {
                    "field_name": "khata_number",
                    "value": "45",
                    "normalized_value": "45",
                    "confidence": 0.91,
                    "raw_text": "खाता संख्या 45",
                    "source_bbox": [120, 160, 350, 200],
                    "source_page": 1
                },
                {
                    "field_name": "plot_area",
                    "value": "1.250",
                    "normalized_value": "1.250",
                    "confidence": 0.88,
                    "raw_text": "क्षेत्रफल: 1.250",
                    "source_bbox": [120, 340, 450, 380],
                    "source_page": 1
                },
                {
                    "field_name": "area_unit",
                    "value": "हेक्टेयर",
                    "normalized_value": "Hectare",
                    "confidence": 0.94,
                    "raw_text": "हेक्टेयर",
                    "source_bbox": [360, 340, 480, 380],
                    "source_page": 1
                },
                {
                    "field_name": "village",
                    "value": "खजूरी कलां",
                    "normalized_value": "Khajuri Kalan",
                    "confidence": 0.96,
                    "raw_text": "ग्राम: खजूरी कलां",
                    "source_bbox": [120, 90, 300, 120],
                    "source_page": 1
                },
                {
                    "field_name": "tehsil",
                    "value": "हुजूर",
                    "normalized_value": "Huzur",
                    "confidence": 0.95,
                    "raw_text": "तहसील: हुजूर",
                    "source_bbox": [310, 90, 400, 120],
                    "source_page": 1
                },
                {
                    "field_name": "district",
                    "value": "भोपाल",
                    "normalized_value": "Bhopal",
                    "confidence": 0.98,
                    "raw_text": "जिला: भोपाल",
                    "source_bbox": [410, 90, 500, 120],
                    "source_page": 1
                }
            ]
        }
