from difflib import SequenceMatcher
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

class DuplicateMatchCandidate(BaseModel):
    duplicate_probability: float
    is_duplicate_suspect: bool
    matching_features: List[str]
    explanation: str
    matched_record_id: Optional[str] = None

class DuplicateDetectionEngine:
    """Multi-Signal Duplicate Detector using Exact, Normalized, and Fuzzy String Matching."""

    @classmethod
    def evaluate(cls, candidate: Dict[str, Any], existing_records: List[Dict[str, Any]]) -> List[DuplicateMatchCandidate]:
        results = []
        for rec in existing_records:
            match_res = cls._compare_pair(candidate, rec)
            if match_res.is_duplicate_suspect:
                results.append(match_res)
        return results

    @classmethod
    def _compare_pair(cls, a: Dict[str, Any], b: Dict[str, Any]) -> DuplicateMatchCandidate:
        matching_features = []
        score = 0.0

        # Signal 1: Geographic Village Match (0.25 weight)
        v_a = str(a.get("village", "")).lower()
        v_b = str(b.get("village", "")).lower()
        if v_a and v_a == v_b:
            score += 0.25
            matching_features.append("VILLAGE_MATCH")

        # Signal 2: Khasra / Survey Number Match (0.25 weight)
        s_a = str(a.get("survey_number", "")).strip()
        s_b = str(b.get("survey_number", "")).strip()
        if s_a and s_a == s_b:
            score += 0.25
            matching_features.append("SURVEY_NUMBER_EXACT_MATCH")

        # Signal 3: Khata Number Match (0.20 weight)
        k_a = str(a.get("khata_number", "")).strip()
        k_b = str(b.get("khata_number", "")).strip()
        if k_a and k_a == k_b:
            score += 0.20
            matching_features.append("KHATA_NUMBER_EXACT_MATCH")

        # Signal 4: Fuzzy Owner Name Match (0.20 weight)
        o_a = str(a.get("owner_name", ""))
        o_b = str(b.get("owner_name", ""))
        similarity = SequenceMatcher(None, o_a, o_b).ratio()
        if similarity >= 0.80:
            score += 0.20 * similarity
            matching_features.append(f"OWNER_NAME_FUZZY_MATCH ({round(similarity*100)}%)")

        # Signal 5: Plot Area Proximity Match (0.10 weight)
        try:
            area_a = float(a.get("plot_area", 0))
            area_b = float(b.get("plot_area", 0))
            if area_a > 0 and area_b > 0 and abs(area_a - area_b) / max(area_a, area_b) <= 0.02:
                score += 0.10
                matching_features.append("PLOT_AREA_MATCH")
        except (ValueError, TypeError):
            pass

        is_suspect = score >= 0.70
        explanation = (
            f"Flagged suspect duplicate ({round(score*100, 1)}% probability) matching "
            f"features: {', '.join(matching_features)}." if is_suspect else "No duplicate conflict."
        )

        return DuplicateMatchCandidate(
            duplicate_probability=round(score, 3),
            is_duplicate_suspect=is_suspect,
            matching_features=matching_features,
            explanation=explanation,
            matched_record_id=b.get("record_id")
        )
