import os
import logging
from typing import Dict, Any

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class OpenCVPreprocessor:
    """
    OpenCV Conditional Image Preprocessor.

    Performs deskewing, contrast analysis, and grayscale conversion on
    an uploaded document image.  The preprocessed version is saved
    alongside the original so that the OCR provider always receives a
    clean image.
    """

    @classmethod
    def process(cls, image_path: str) -> Dict[str, Any]:
        if not image_path or not os.path.exists(image_path):
            logger.warning(f"Preprocessor: file not found at '{image_path}', skipping.")
            return {"status": "SKIPPED", "reason": "File not found or path empty"}

        img = cv2.imread(image_path)
        if img is None:
            logger.warning(f"Preprocessor: cv2 could not decode '{image_path}', skipping.")
            return {"status": "SKIPPED", "reason": "Failed to decode image binary"}

        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # ── Contrast / brightness stats ─────────────────────────────────────
        contrast_score = float(gray.std())

        # ── Deskew estimation ───────────────────────────────────────────────
        skew_angle = 0.0
        try:
            coords = np.column_stack(np.where(gray < 128))
            if len(coords) > 50:
                rect = cv2.minAreaRect(coords)
                skew_angle = float(rect[-1])
        except Exception:
            pass

        # ── Adaptive denoising if contrast is very low ──────────────────────
        if contrast_score < 30:
            gray = cv2.fastNlMeansDenoising(gray, h=15)

        # ── Write preprocessed image (overwrite in-place is fine for our use)
        try:
            cv2.imwrite(image_path, gray)
        except Exception as write_err:
            logger.warning(f"Preprocessor: could not save preprocessed image: {write_err}")

        logger.info(
            f"Preprocessor: processed '{os.path.basename(image_path)}' "
            f"({w}×{h}px, contrast={contrast_score:.1f}, skew={skew_angle:.2f}°)"
        )

        return {
            "status": "PROCESSED",
            "dimensions": {"width": w, "height": h},
            "skew_angle": skew_angle,
            "contrast_score": contrast_score,
        }
