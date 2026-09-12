"""
OCR Provider Factory.

Selection logic (evaluated at runtime for each request):
  1. Read AI_PROVIDER env var (overrides settings)
  2. If "sarvam" and SARVAM_API_KEY is non-empty → SarvamOCRProvider
  3. Otherwise → MockOCRProvider (safe default for development)
"""
import os
import logging
from app.ai.ocr_interface import OCRProvider
from app.ai.sarvam_provider import SarvamOCRProvider
from app.ai.mock_provider import MockOCRProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_ocr_provider() -> OCRProvider:
    """
    Factory: returns the appropriate OCR provider based on environment config.

    Environment variables:
        AI_PROVIDER   - "sarvam" | "mock"  (default: value from .env / settings)
        SARVAM_API_KEY - required when AI_PROVIDER=sarvam
    """
    provider_setting = os.getenv("AI_PROVIDER", settings.AI_PROVIDER).lower().strip()
    api_key = os.getenv("SARVAM_API_KEY", settings.SARVAM_API_KEY or "").strip()

    # Treat placeholder values as unset
    _PLACEHOLDER_KEYS = {"your_sarvam_api_key_here", "mock_sarvam_key", "placeholder"}
    if api_key.lower() in _PLACEHOLDER_KEYS:
        api_key = ""

    if provider_setting == "sarvam":
        if not api_key:
            logger.warning(
                "AI_PROVIDER=sarvam but SARVAM_API_KEY is not set (or is a placeholder). "
                "Falling back to MockOCRProvider. "
                "→ Set a real key in .env: SARVAM_API_KEY=your_actual_key"
            )
            return MockOCRProvider()
        logger.info("Using SarvamOCRProvider (Sarvam Vision 1.5 Doc AI SDK)")
        return SarvamOCRProvider(api_key=api_key)

    # Default: mock
    logger.info(f"Using MockOCRProvider (AI_PROVIDER='{provider_setting}')")
    return MockOCRProvider()
