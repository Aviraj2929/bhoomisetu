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
import logging
from typing import Optional, List

import cv2

from app.ai.ocr_interface import OCRProvider, OCRResponsePayload, OCRToken, FieldExtractionResult
from app.ai.extraction import LandRecordExtractionParser

logger = logging.getLogger(__name__)

# Representative Hindi Khasra sample text for the mock pipeline.
# This is not derived from the uploaded file – it is a fixed test corpus.
MOCK_FULL_TEXT = (
    "राजस्व विभाग, मध्यप्रदेश शासन\n"
    "प्रारूप खसरा / खेसरा पंजी\n"
    "ग्राम: खजूरी कलां   तहसील: हुजूर   जिला: भोपाल\n"
    "खाता संख्या: 45   खसरा नं: 123/4\n"
    "खातेदार का नाम: राम सहाय पुत्र श्याम लाल\n"
    "क्षेत्रफल: 1.250 हेक्टेयर\n"
    "भूमि प्रकार: सिंचित कृषि भूमि\n"
    "फसल: गेहूँ\n"
)

MOCK_TOKENS = [
    ("ग्राम:", 0.98, [40, 120, 100, 145]),
    ("खजूरी", 0.96, [105, 120, 175, 145]),
    ("कलां", 0.95, [180, 120, 235, 145]),
    ("तहसील:", 0.97, [250, 120, 325, 145]),
    ("हुजूर", 0.95, [330, 120, 390, 145]),
    ("जिला:", 0.97, [410, 120, 460, 145]),
    ("भोपाल", 0.96, [465, 120, 535, 145]),
    ("खाता", 0.98, [40, 175, 95, 198]),
    ("संख्या:", 0.98, [100, 175, 175, 198]),
    ("45", 0.91, [180, 175, 215, 198]),
    ("खसरा", 0.97, [230, 175, 290, 198]),
    ("नं:", 0.97, [295, 175, 325, 198]),
    ("123/4", 0.94, [330, 175, 400, 198]),
    ("खातेदार", 0.94, [40, 230, 140, 255]),
    ("नाम:", 0.93, [145, 230, 195, 255]),
    ("राम", 0.78, [200, 230, 250, 255]),
    ("सहाय", 0.82, [255, 230, 320, 255]),
    ("क्षेत्रफल:", 0.92, [40, 285, 160, 310]),
    ("1.250", 0.88, [165, 285, 225, 310]),
    ("हेक्टेयर", 0.93, [230, 285, 335, 310]),
]


class MockOCRProvider(OCRProvider):
    """
    Mock OCR provider for local development and testing.

    Outputs a fixed Hindi Khasra document text so the full extraction,
    validation, and verification pipeline can be exercised without calling
    the Sarvam API.
    """

    def __init__(self):
        self.provider_name = "BhoomiSetu Mock OCR (Development Mode)"

    def process_image(self, image_path: str, language_hint: Optional[str] = None) -> OCRResponsePayload:
        # Read image dimensions if a real file was provided (for bbox scaling)
        img_w, img_h = 600, 800
        if image_path and os.path.exists(image_path):
            img = cv2.imread(image_path)
            if img is not None:
                img_h, img_w = img.shape[:2]
                logger.info(
                    f"[MockOCR] Uploaded image: {os.path.basename(image_path)} "
                    f"({img_w}×{img_h}px). "
                    "NOTE: Using predefined Hindi Khasra text (mock mode – no real OCR)."
                )
            else:
                logger.warning(
                    f"[MockOCR] Could not decode '{image_path}' as an image. "
                    "Using default dimensions."
                )
        else:
            logger.info("[MockOCR] No image path provided, using default mock text.")

        # Scale bounding boxes proportionally to the uploaded image size
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
            for text, conf, (x1, y1, x2, y2) in MOCK_TOKENS
        ]

        extracted_fields = LandRecordExtractionParser.extract_fields_from_ocr(
            full_text=MOCK_FULL_TEXT,
            tokens=tokens,
            page_number=1,
            provider_name="mock_local",
        )

        logger.info(
            f"[MockOCR] Extraction complete: {len(extracted_fields)} fields parsed "
            f"from predefined mock text."
        )

        return OCRResponsePayload(
            full_text=MOCK_FULL_TEXT,
            detected_language="hi",
            tokens=tokens,
            extracted_fields=extracted_fields,
            provider_name=self.provider_name,
        )
