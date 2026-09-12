import re
from typing import Dict, Any, List, Optional, Tuple
from app.ai.ocr_interface import OCRToken, FieldExtractionResult

class FieldNormalizer:
    """Normalizes Vernacular Numerals, Dates, and Area Units across Indic languages."""

    DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
    BENGALI_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
    GUJARATI_DIGITS = str.maketrans("૦૧૨૩૪૫૬૭૮૯", "0123456789")

    @classmethod
    def normalize_numerals(cls, text: str) -> str:
        if not text:
            return ""
        translated = text.translate(cls.DEVANAGARI_DIGITS).translate(cls.BENGALI_DIGITS).translate(cls.GUJARATI_DIGITS)
        return translated

    @classmethod
    def normalize_area_unit(cls, unit_str: str) -> Tuple[str, str]:
        """Returns (normalized_unit, standard_english_unit)."""
        u = unit_str.lower().strip()
        if "हेक्टेयर" in u or "hectare" in u:
            return "हेक्टेयर", "Hectare"
        elif "बीघा" in u or "bigha" in u:
            return "बीघा", "Bigha"
        elif "एकड़" in u or "acre" in u:
            return "एकड़", "Acre"
        elif "गुंठा" in u or "guntha" in u:
            return "गुंठा", "Guntha"
        return unit_str, unit_str


class LandRecordExtractionParser:
    """
    NLP & Heuristic Parser that inspects raw OCR tokens and text 
    to extract actual MVP land record fields with confidence scores & bounding boxes.
    """

    @classmethod
    def extract_fields_from_ocr(
        self, 
        full_text: str, 
        tokens: List[OCRToken], 
        page_number: int = 1,
        provider_name: str = "sarvam"
    ) -> List[FieldExtractionResult]:
        
        results: List[FieldExtractionResult] = []
        normalized_full_text = FieldNormalizer.normalize_numerals(full_text)

        # 1. Extract Survey / Khasra Number
        survey_res = self._extract_survey_number(full_text, normalized_full_text, tokens, page_number, provider_name)
        if survey_res:
            results.append(survey_res)

        # 2. Extract Khata Number
        khata_res = self._extract_khata_number(full_text, normalized_full_text, tokens, page_number, provider_name)
        if khata_res:
            results.append(khata_res)

        # 3. Extract Owner Name
        owner_res = self._extract_owner_name(full_text, tokens, page_number, provider_name)
        if owner_res:
            results.append(owner_res)

        # 4. Extract Plot Area & Area Unit
        area_res, unit_res = self._extract_area_and_unit(full_text, normalized_full_text, tokens, page_number, provider_name)
        if area_res:
            results.append(area_res)
        if unit_res:
            results.append(unit_res)

        # 5. Extract Village, Tehsil, District
        geo_results = self._extract_location_fields(full_text, tokens, page_number, provider_name)
        results.extend(geo_results)

        return results

    @classmethod
    def _extract_survey_number(
        cls, full_text: str, norm_text: str, tokens: List[OCRToken], page: int, provider: str
    ) -> Optional[FieldExtractionResult]:
        patterns = [
            r"(?:खसरा|गाटा|सर्वे|सर्वेक्षण|survey|khasra|gata)\s*(?:संख्या|नं|न0|no|num)?\s*[:\.-]?\s*([0-9]+(?:\/[0-9]+)?)",
            r"([0-9]+\/[0-9]+)"
        ]
        for pat in patterns:
            match = re.search(pat, norm_text, re.IGNORECASE)
            if match:
                raw_snippet = match.group(0)
                extracted_val = match.group(1)
                bbox, token_conf = cls._find_bbox_and_conf(extracted_val, tokens)
                
                # Estimate confidence based on token OCR confidence + regex match quality
                conf = min(round(token_conf * 0.95, 2), 0.99) if token_conf > 0 else 0.85

                return FieldExtractionResult(
                    field_name="survey_number",
                    value=extracted_val,
                    normalized_value=extracted_val,
                    confidence=conf,
                    raw_text=raw_snippet,
                    source_page=page,
                    bounding_box=bbox,
                    extraction_method=f"{provider}_regex",
                    model_version="NLP_Extractor_v1.0"
                )
        return None

    @classmethod
    def _extract_khata_number(
        cls, full_text: str, norm_text: str, tokens: List[OCRToken], page: int, provider: str
    ) -> Optional[FieldExtractionResult]:
        pattern = r"(?:खाता|खेवट|khata|khewaut)\s*(?:संख्या|नं|न0|no)?\s*[:\.-]?\s*([0-9]+)"
        match = re.search(pattern, norm_text, re.IGNORECASE)
        if match:
            raw_snippet = match.group(0)
            val = match.group(1)
            bbox, token_conf = cls._find_bbox_and_conf(val, tokens)
            conf = min(round(token_conf * 0.95, 2), 0.98) if token_conf > 0 else 0.88
            
            return FieldExtractionResult(
                field_name="khata_number",
                value=val,
                normalized_value=val,
                confidence=conf,
                raw_text=raw_snippet,
                source_page=page,
                bounding_box=bbox,
                extraction_method=f"{provider}_regex",
                model_version="NLP_Extractor_v1.0"
            )
        return None

    @classmethod
    def _extract_owner_name(
        cls, full_text: str, tokens: List[OCRToken], page: int, provider: str
    ) -> Optional[FieldExtractionResult]:
        keywords = r"(?:खातेदार|भूमिस्वामी|मालिक|काश्तकार|पट्टेदार|स्वामी|स्वामिनी|कृषक|owner|landowner|holder)\s*(?:का\s*नाम|नाम|name)?"
        pattern = keywords + r"\s*[:\.-]?\s*([^\n\r,;:]+)"
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            raw_snippet = match.group(0)
            raw_val = match.group(1).strip()
            # Truncate if raw_val matched into next field keywords
            stop_keywords = ["क्षेत्रफल", "रकबा", "खाता", "खसरा", "सर्वे", "फसल", "area", "khata", "khasra", "survey"]
            for sk in stop_keywords:
                if sk in raw_val.lower():
                    raw_val = raw_val.lower().split(sk)[0].strip()

            name_val = raw_val.strip()
            if len(name_val) >= 2:
                first_word = name_val.split()[0]
                bbox, token_conf = cls._find_bbox_and_conf(first_word, tokens)
                norm_name = FieldNormalizer.normalize_numerals(name_val)
                conf = min(round(token_conf * 0.95, 2), 0.95) if token_conf > 0 else 0.88

                return FieldExtractionResult(
                    field_name="owner_name",
                    value=name_val,
                    normalized_value=norm_name,
                    confidence=conf,
                    raw_text=raw_snippet,
                    source_page=page,
                    bounding_box=bbox,
                    extraction_method=f"{provider}_nlp",
                    model_version="NLP_Extractor_v1.0"
                )
        return None

    @classmethod
    def _extract_area_and_unit(
        cls, full_text: str, norm_text: str, tokens: List[OCRToken], page: int, provider: str
    ) -> Tuple[Optional[FieldExtractionResult], Optional[FieldExtractionResult]]:
        pattern = r"(?:क्षेत्रफल|रकबा|area)\s*[:\.-]?\s*([0-9\.]+)\s*([A-Za-z\u0900-\u097F]+)?"
        match = re.search(pattern, norm_text, re.IGNORECASE)
        
        area_res = None
        unit_res = None

        if match:
            raw_snippet = match.group(0)
            area_val = match.group(1)
            unit_val = match.group(2) or "Hectare"

            bbox, token_conf = cls._find_bbox_and_conf(area_val, tokens)
            conf = min(round(token_conf * 0.92, 2), 0.95) if token_conf > 0 else 0.82

            area_res = FieldExtractionResult(
                field_name="plot_area",
                value=area_val,
                normalized_value=area_val,
                confidence=conf,
                raw_text=raw_snippet,
                source_page=page,
                bounding_box=bbox,
                extraction_method=f"{provider}_regex",
                model_version="NLP_Extractor_v1.0"
            )

            raw_u, norm_u = FieldNormalizer.normalize_area_unit(unit_val)
            unit_res = FieldExtractionResult(
                field_name="area_unit",
                value=raw_u,
                normalized_value=norm_u,
                confidence=0.92,
                raw_text=unit_val,
                source_page=page,
                bounding_box=bbox,
                extraction_method=f"{provider}_dict",
                model_version="NLP_Extractor_v1.0"
            )

        return area_res, unit_res

    @classmethod
    def _extract_location_fields(
        cls, full_text: str, tokens: List[OCRToken], page: int, provider: str
    ) -> List[FieldExtractionResult]:
        results = []

        # Village
        v_match = re.search(r"(?:ग्राम|मौजा|गांव|village)\s*[:\.-]?\s*([\u0900-\u097F\sA-Za-z]+)", full_text, re.IGNORECASE)
        if v_match:
            val = v_match.group(1).split()[0].strip()
            bbox, conf = cls._find_bbox_and_conf(val, tokens)
            results.append(FieldExtractionResult(
                field_name="village",
                value=val,
                normalized_value=val,
                confidence=0.94 if conf > 0 else 0.85,
                raw_text=v_match.group(0),
                source_page=page,
                bounding_box=bbox,
                extraction_method=f"{provider}_regex",
                model_version="NLP_Extractor_v1.0"
            ))

        # Tehsil
        t_match = re.search(r"(?:तहसील|तालुका|tehsil|taluka)\s*[:\.-]?\s*([\u0900-\u097F\sA-Za-z]+)", full_text, re.IGNORECASE)
        if t_match:
            val = t_match.group(1).split()[0].strip()
            bbox, conf = cls._find_bbox_and_conf(val, tokens)
            results.append(FieldExtractionResult(
                field_name="tehsil",
                value=val,
                normalized_value=val,
                confidence=0.94 if conf > 0 else 0.85,
                raw_text=t_match.group(0),
                source_page=page,
                bounding_box=bbox,
                extraction_method=f"{provider}_regex",
                model_version="NLP_Extractor_v1.0"
            ))

        # District
        d_match = re.search(r"(?:जिला|जनपद|district)\s*[:\.-]?\s*([\u0900-\u097F\sA-Za-z]+)", full_text, re.IGNORECASE)
        if d_match:
            val = d_match.group(1).split()[0].strip()
            bbox, conf = cls._find_bbox_and_conf(val, tokens)
            results.append(FieldExtractionResult(
                field_name="district",
                value=val,
                normalized_value=val,
                confidence=0.95 if conf > 0 else 0.88,
                raw_text=d_match.group(0),
                source_page=page,
                bounding_box=bbox,
                extraction_method=f"{provider}_regex",
                model_version="NLP_Extractor_v1.0"
            ))

        return results

    @classmethod
    def _find_bbox_and_conf(cls, search_str: str, tokens: List[OCRToken]) -> Tuple[List[int], float]:
        if not search_str or not tokens:
            return [0, 0, 0, 0], 0.0
        
        search_clean = FieldNormalizer.normalize_numerals(search_str).lower()
        for t in tokens:
            t_clean = FieldNormalizer.normalize_numerals(t.text).lower()
            if search_clean in t_clean or t_clean in search_clean:
                return t.bbox, t.confidence

        return [0, 0, 0, 0], 0.0
