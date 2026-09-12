import re
from enum import Enum
from typing import Optional, Any, List, Dict
from pydantic import BaseModel

class RuleSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    FAIL = "FAIL"

class RuleStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"

class RuleValidationResult(BaseModel):
    rule_id: str
    field_name: str
    severity: RuleSeverity
    status: RuleStatus
    message: str
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    source: str  # e.g., STRUCTURAL_RULE, CROSS_FIELD, CENSUS_LOOKUP

class BhoomiSetuValidationEngine:
    """Configurable Rule Validation Engine for Indian Land Records."""

    def __init__(self, location_master: Optional[Dict[str, Any]] = None):
        self.location_master = location_master or {
            "madhya pradesh:bhopal:huzur:khajuri kalan": True,
            "madhya pradesh:indore:sanwer:chandrawatiganj": True
        }

    def validate_fields(self, fields_dict: Dict[str, Any], state_code: str = "MP") -> List[RuleValidationResult]:
        results = []

        # 1. Area Must Be Positive Rule
        results.append(self._validate_positive_area(fields_dict.get("plot_area")))

        # 2. Area Unit Sanity Rule
        results.append(self._validate_area_unit(fields_dict.get("area_unit")))

        # 3. Geographic Hierarchy Validation
        results.append(self._validate_geographic_hierarchy(
            fields_dict.get("state", "Madhya Pradesh"),
            fields_dict.get("district", "Bhopal"),
            fields_dict.get("tehsil", "Huzur"),
            fields_dict.get("village", "Khajuri Kalan")
        ))

        # 4. Survey / Khasra Pattern Check
        results.append(self._validate_survey_number(fields_dict.get("survey_number"), state_code))

        # 5. Missing Critical Fields Check
        results.append(self._validate_mandatory_fields(fields_dict))

        return results

    def _validate_positive_area(self, area_val: Optional[Any]) -> RuleValidationResult:
        if not area_val:
            return RuleValidationResult(
                rule_id="RULE_VAL_01", field_name="plot_area", severity=RuleSeverity.FAIL,
                status=RuleStatus.FAIL, message="Plot area value is missing.", source="STRUCTURAL_RULE"
            )
        try:
            num_val = float(str(area_val).replace(",", "").strip())
            if num_val <= 0.0 or num_val > 5000.0:
                return RuleValidationResult(
                    rule_id="RULE_VAL_01", field_name="plot_area", severity=RuleSeverity.FAIL,
                    status=RuleStatus.FAIL, message=f"Plot area {num_val} is outside valid range (0, 5000].",
                    expected_value="0.0 < Area <= 5000.0", actual_value=num_val, source="STRUCTURAL_RULE"
                )
            return RuleValidationResult(
                rule_id="RULE_VAL_01", field_name="plot_area", severity=RuleSeverity.INFO,
                status=RuleStatus.PASS, message="Plot area is positive and valid.", actual_value=num_val, source="STRUCTURAL_RULE"
            )
        except ValueError:
            return RuleValidationResult(
                rule_id="RULE_VAL_01", field_name="plot_area", severity=RuleSeverity.FAIL,
                status=RuleStatus.FAIL, message=f"Plot area '{area_val}' is unparseable numeric string.", source="STRUCTURAL_RULE"
            )

    def _validate_area_unit(self, unit_val: Optional[Any]) -> RuleValidationResult:
        valid_units = {"hectare", "हेक्टेयर", "acre", "एकड़", "bigha", "बीघा", "guntha", "गुंठा"}
        if not unit_val or str(unit_val).lower().strip() not in valid_units:
            return RuleValidationResult(
                rule_id="RULE_VAL_02", field_name="area_unit", severity=RuleSeverity.WARNING,
                status=RuleStatus.WARNING, message=f"Unrecognized land area unit '{unit_val}'.",
                expected_value=list(valid_units), actual_value=unit_val, source="STRUCTURAL_RULE"
            )
        return RuleValidationResult(
            rule_id="RULE_VAL_02", field_name="area_unit", severity=RuleSeverity.INFO,
            status=RuleStatus.PASS, message="Area unit recognized.", actual_value=unit_val, source="STRUCTURAL_RULE"
        )

    def _validate_geographic_hierarchy(self, state: str, district: str, tehsil: str, village: str) -> RuleValidationResult:
        key = f"{state}:{district}:{tehsil}:{village}".lower()
        if key not in self.location_master:
            return RuleValidationResult(
                rule_id="RULE_VAL_03", field_name="village", severity=RuleSeverity.WARNING,
                status=RuleStatus.WARNING, message=f"Village '{village}' under Tehsil '{tehsil}', District '{district}' not found in master census.",
                expected_value="Valid Census Master Hierarchy", actual_value=f"{district}->{tehsil}->{village}", source="CENSUS_MASTER"
            )
        return RuleValidationResult(
            rule_id="RULE_VAL_03", field_name="village", severity=RuleSeverity.INFO,
            status=RuleStatus.PASS, message="Geographic hierarchy validated against Census master.", source="CENSUS_MASTER"
        )

    def _validate_survey_number(self, survey_no: Optional[Any], state_code: str) -> RuleValidationResult:
        if not survey_no:
            return RuleValidationResult(
                rule_id="RULE_VAL_04", field_name="survey_number", severity=RuleSeverity.FAIL,
                status=RuleStatus.FAIL, message="Survey/Khasra number is missing.", source="STRUCTURAL_RULE"
            )
        pattern = r"^\d+([\/]\d+)?$"
        if not re.match(pattern, str(survey_no).strip()):
            return RuleValidationResult(
                rule_id="RULE_VAL_04", field_name="survey_number", severity=RuleSeverity.WARNING,
                status=RuleStatus.WARNING, message=f"Survey/Khasra number '{survey_no}' format suspicious.",
                expected_value="Pattern e.g., '123' or '123/4'", actual_value=survey_no, source="STATE_PATTERN_RULE"
            )
        return RuleValidationResult(
            rule_id="RULE_VAL_04", field_name="survey_number", severity=RuleSeverity.INFO,
            status=RuleStatus.PASS, message="Survey number format valid.", actual_value=survey_no, source="STATE_PATTERN_RULE"
        )

    def _validate_mandatory_fields(self, fields_dict: Dict[str, Any]) -> RuleValidationResult:
        mandatory = ["owner_name", "survey_number", "khata_number", "plot_area"]
        missing = [m for m in mandatory if not fields_dict.get(m)]
        if missing:
            return RuleValidationResult(
                rule_id="RULE_VAL_05", field_name="document", severity=RuleSeverity.FAIL,
                status=RuleStatus.FAIL, message=f"Missing mandatory core land fields: {', '.join(missing)}.",
                expected_value="All mandatory fields present", actual_value=missing, source="BUSINESS_RULE"
            )
        return RuleValidationResult(
            rule_id="RULE_VAL_05", field_name="document", severity=RuleSeverity.INFO,
            status=RuleStatus.PASS, message="All mandatory land fields present.", source="BUSINESS_RULE"
        )
