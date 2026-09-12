"""
Mock OCR Provider.

Used when AI_PROVIDER=mock (the default for local development).

What this does:
- If the uploaded file is a readable image, it reads its pixel dimensions.
- It runs the full LandRecordExtractionParser on a realistic Hindi Khasra sample
  text so that all downstream field extraction, validation, and verification
  flows work correctly without an external API.

This is intentionally transparent – the logs will clearly say "MockOCRProvider".
The extracted data will always be the same predefined text (since there's no
real OCR), so the pipeline is functional but the values are synthetic.

To get real OCR, set AI_PROVIDER=sarvam and provide a valid SARVAM_API_KEY.
"""
import os
import hashlib
import logging
from typing import Optional, List, Tuple

import cv2

from app.ai.ocr_interface import OCRProvider, OCRResponsePayload, OCRToken, FieldExtractionResult
from app.ai.extraction import LandRecordExtractionParser

logger = logging.getLogger(__name__)

# Predefined pools for generating realistic document-specific mock land records
VILLAGES = ["खजूरी कलां", "रामपुर", "बिलखिरिया", "सुहागपुर", "शाहपुरा", "बैरसिया"]
TEHSILS = ["हुजूर", "गोविंदपुरा", "कोशांबी", "बैरसिया", "कोलार"]
DISTRICTS = ["भोपाल", "सीहोर", "रायसेन", "विदिशा", "इंदौर"]
KHATA_NOS = ["45", "78", "112", "204", "15", "89", "302"]
KHASRA_NOS = ["123/4", "45/2", "89/1", "210/A", "67/3", "14/1", "156/9"]
OWNERS = [
    "राम सहाय पुत्र श्याम लाल",
    "सुरेश कुमार पुत्र रमेश चंद्र",
    "महेश शर्मा पुत्र देवदत्त",
    "राजेश पटेल पुत्र मोहन लाल",
    "अमित सिंह पुत्र विक्रम सिंह",
    "श्रीमती सुनीता देवी पत्नी रामपाल",
]
AREAS = ["1.250", "2.150", "0.850", "3.400", "1.750", "0.500", "2.900"]
CROPS = ["गेहूँ", "धान", "चना", "सोयाबीन", "मक्का"]


def generate_document_mock_data(image_path: str) -> Tuple[str, List[Tuple[str, float, List[int]]]]:
    """Generates document-specific Hindi land record text and tokens seeded by filename."""
    seed_str = os.path.basename(image_path) if image_path else "default_mock"
    seed = int(hashlib.md5(seed_str.encode("utf-8")).hexdigest(), 16)

    v = VILLAGES[seed % len(VILLAGES)]
    t = TEHSILS[(seed >> 2) % len(TEHSILS)]
    d = DISTRICTS[(seed >> 4) % len(DISTRICTS)]
    khata = KHATA_NOS[(seed >> 6) % len(KHATA_NOS)]
    khasra = KHASRA_NOS[(seed >> 8) % len(KHASRA_NOS)]
    owner = OWNERS[(seed >> 10) % len(OWNERS)]
    area = AREAS[(seed >> 12) % len(AREAS)]
    crop = CROPS[(seed >> 14) % len(CROPS)]

    full_text = (
        "राजस्व विभाग, मध्यप्रदेश शासन\n"
        "प्रारूप खसरा / खेसरा पंजी\n"
        f"ग्राम: {v}   तहसील: {t}   जिला: {d}\n"
        f"खाता संख्या: {khata}   खसरा नं: {khasra}\n"
        f"खातेदार का नाम: {owner}\n"
        f"क्षेत्रफल: {area} हेक्टेयर\n"
        "भूमि प्रकार: सिंचित कृषि भूमि\n"
        f"फसल: {crop}\n"
    )

    owner_first = owner.split()[0]
    tokens = [
        ("ग्राम:", 0.98, [40, 120, 100, 145]),
        (v, 0.96, [105, 120, 175, 145]),
        ("तहसील:", 0.97, [250, 120, 325, 145]),
        (t, 0.95, [330, 120, 390, 145]),
        ("जिला:", 0.97, [410, 120, 460, 145]),
        (d, 0.96, [465, 120, 535, 145]),
        ("खाता", 0.98, [40, 175, 95, 198]),
        ("संख्या:", 0.98, [100, 175, 175, 198]),
        (khata, 0.91, [180, 175, 215, 198]),
        ("खसरा", 0.97, [230, 175, 290, 198]),
        ("नं:", 0.97, [295, 175, 325, 198]),
        (khasra, 0.94, [330, 175, 400, 198]),
        ("खातेदार", 0.94, [40, 230, 140, 255]),
        ("नाम:", 0.93, [145, 230, 195, 255]),
        (owner_first, 0.78, [200, 230, 250, 255]),
        ("क्षेत्रफल:", 0.92, [40, 285, 160, 310]),
        (area, 0.88, [165, 285, 225, 310]),
        ("हेक्टेयर", 0.93, [230, 285, 335, 310]),
    ]
    return full_text, tokens


class MockOCRProvider(OCRProvider):
    """
    Mock OCR provider for local development and testing.

    Outputs dynamic document-specific Hindi Khasra text so that each uploaded document
    has distinct extracted field values, bounding boxes, and validation checks.
    """

    def __init__(self):
        self.provider_name = "BhoomiSetu Mock OCR (Development Mode)"

    def process_image(self, image_path: str, language_hint: Optional[str] = None) -> OCRResponsePayload:
        img_w, img_h = 600, 800
        if image_path and os.path.exists(image_path):
            img = cv2.imread(image_path)
            if img is not None:
                img_h, img_w = img.shape[:2]
                logger.info(
                    f"[MockOCR] Uploaded image: {os.path.basename(image_path)} "
                    f"({img_w}×{img_h}px)."
                )

        full_text, raw_tokens = generate_document_mock_data(image_path)

        scale_x = img_w / 600.0
        scale_y = img_h / 800.0

        tokens: List[OCRToken] = [
            OCRToken(
                text=text,
                confidence=conf,
                bbox=[
                    int(x1 * scale_x),
                    int(y1 * scale_y),
                    int(x2 * scale_x),
                    int(y2 * scale_y),
                ],
            )
            for text, conf, (x1, y1, x2, y2) in raw_tokens
        ]

        extracted_fields = LandRecordExtractionParser.extract_fields_from_ocr(
            full_text=full_text,
            tokens=tokens,
            page_number=1,
            provider_name="mock_local",
        )

        logger.info(
            f"[MockOCR] Extraction complete: {len(extracted_fields)} fields parsed "
            f"for file '{os.path.basename(image_path or '')}'."
        )

        return OCRResponsePayload(
            full_text=full_text,
            detected_language="hi",
            tokens=tokens,
            extracted_fields=extracted_fields,
            provider_name=self.provider_name,
        )
