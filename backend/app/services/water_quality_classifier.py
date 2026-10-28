"""
AquaWatch AI - Water Quality Status & Safety Classification Service

Provides rule-based water safety screening based on authoritative regulatory criteria:
1. Central Pollution Control Board (CPCB) Designated Best Use Water Quality Criteria
   - Class C: Drinking water source after conventional treatment and disinfection
2. Bureau of Indian Standards (BIS) IS 10500:2012 (Drinking Water Specification - Acceptable Limits)

Configurable Thresholds (Overridable via environment variables):
- pH: 6.5 to 8.5 (CPCB Class C / BIS IS 10500)
- Dissolved Oxygen (DO): >= 4.0 mg/L (CPCB Class C minimum limit)
- Biochemical Oxygen Demand (BOD): <= 3.0 mg/L (CPCB Class C permissible limit)
- Turbidity: <= 5.0 NTU (IS 10500 permissible screening threshold)
- Total Dissolved Solids (TDS): <= 500.0 mg/L (IS 10500 acceptable limit)

Classification Behavior:
- SAFE: Only when all required parameters pass the configured criteria and the system
        is explicitly configured with an established assessment standard.
- HARMFUL: When one or more parameters fail an applicable configured criterion.
           Specifies which parameter(s) failed and why.
- INCONCLUSIVE: When measurements are missing, invalid, conflicting, or when the
                applicable safety standard is not established/enabled.

Scientific Disclosure & Limitations:
Passing these five measurements does NOT prove water is safe to drink. They do not
cover microbial contamination (e.g., E. coli, coliform bacteria), toxic heavy metals,
or agricultural pesticides. The feature is labeled as a DEMO assessment.
"""

import os
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv

from app.models import WaterQualityRecord

load_dotenv()


# ==========================================================
# 1. Configurable Standards & Thresholds
# ==========================================================

def get_safety_configuration() -> Dict[str, Any]:
    """
    Retrieves the active water safety screening configuration and thresholds.
    Allows dynamic runtime updates via environment variables without code modification.
    """
    standard_name = os.getenv(
        "WATER_SAFETY_STANDARD_NAME",
        "CPCB Class C & BIS IS 10500:2012 Baseline",
    )
    intended_use = os.getenv(
        "WATER_SAFETY_INTENDED_USE",
        "Surface water source for drinking water after conventional treatment & disinfection",
    )
    enabled = os.getenv("WATER_SAFETY_STANDARD_ENABLED", "true").strip().lower() in (
        "true",
        "1",
        "yes",
    )

    try:
        ph_min = float(os.getenv("WATER_SAFETY_PH_MIN", "6.5"))
        ph_max = float(os.getenv("WATER_SAFETY_PH_MAX", "8.5"))
        do_min = float(os.getenv("WATER_SAFETY_DO_MIN", "4.0"))
        bod_max = float(os.getenv("WATER_SAFETY_BOD_MAX", "3.0"))
        turbidity_max = float(os.getenv("WATER_SAFETY_TURBIDITY_MAX", "5.0"))
        tds_max = float(os.getenv("WATER_SAFETY_TDS_MAX", "500.0"))
    except ValueError:
        ph_min, ph_max, do_min, bod_max, turbidity_max, tds_max = 6.5, 8.5, 4.0, 3.0, 5.0, 500.0

    return {
        "enabled": enabled,
        "standard_name": standard_name,
        "intended_use": intended_use,
        "thresholds": {
            "ph": {"min": ph_min, "max": ph_max, "unit": "Dimensionless"},
            "dissolved_oxygen": {"min": do_min, "unit": "mg/L"},
            "bod": {"max": bod_max, "unit": "mg/L"},
            "turbidity": {"max": turbidity_max, "unit": "NTU"},
            "tds": {"max": tds_max, "unit": "mg/L"},
        },
    }


# ==========================================================
# 2. Rule-Based Water Safety Evaluator
# ==========================================================

LIMITATIONS_DISCLOSURE = (
    "DEMO RULE-BASED SCREENING ASSESSMENT ONLY. This evaluation tests five physical and chemical "
    "parameters against CPCB Class C and BIS IS 10500:2012 baseline guidelines. It does NOT analyze "
    "microbial pathogens (such as E. coli, fecal coliforms, Giardia, or enteric viruses), toxic heavy "
    "metals (arsenic, lead, mercury, cadmium), or agricultural/industrial chemicals (pesticides, PFAS). "
    "A 'SAFE' screening result indicates only that the five measured physical-chemical parameters meet "
    "baseline criteria; it does NOT certify that the water is potable or safe for direct human drinking "
    "without full accredited laboratory testing and authorized municipal disinfection."
)


def evaluate_sample_safety(
    measurements: Dict[str, Optional[float]],
    sample_name: str = "Test Sample",
    force_enabled: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Evaluates a water quality sample against configured water safety standards.

    Returns:
        dict containing:
        - classification: 'SAFE', 'HARMFUL', or 'INCONCLUSIVE'
        - result_type: 'DEMO_RULE_BASED'
        - standard_name: Name of regulatory standard
        - standard_intended_use: Description of intended water use
        - parameter_assessments: Detailed per-parameter evaluation
        - failed_parameters: List of parameters that failed
        - passed_parameters: List of parameters that passed
        - reasons: Comprehensive list of reasons
        - warnings: Boundary or caution warnings
        - limitations: Scientific limitations disclaimer
    """
    config = get_safety_configuration()
    is_enabled = force_enabled if force_enabled is not None else config["enabled"]
    thresholds = config["thresholds"]
    standard_name = config["standard_name"]
    intended_use = config["intended_use"]

    parameter_assessments: List[Dict[str, Any]] = []
    failed_params: List[str] = []
    passed_params: List[str] = []
    reasons: List[str] = []
    warnings: List[str] = []

    # 1. Verify Standard Availability
    if not is_enabled or not intended_use:
        return {
            "classification": "INCONCLUSIVE",
            "result_type": "DEMO_RULE_BASED",
            "standard_name": standard_name if is_enabled else "Unspecified / Disabled Standard",
            "standard_intended_use": intended_use if is_enabled else "Unspecified Intended Use",
            "parameter_assessments": [],
            "failed_parameters": [],
            "passed_parameters": [],
            "reasons": [
                "Water safety standard is not established or enabled on this system. "
                "In strict accordance with scientific integrity, the classification is INCONCLUSIVE "
                "rather than claiming the water is safe."
            ],
            "warnings": ["System is not currently configured for safety classification."],
            "limitations": LIMITATIONS_DISCLOSURE,
        }

    # 2. Check for Missing Required Core Parameters
    core_keys = ["ph", "dissolved_oxygen", "bod", "turbidity", "tds"]
    missing_keys = [k for k in core_keys if measurements.get(k) is None]

    # 3. Check for Physically Invalid Parameters
    invalid_params = []
    ph_val = measurements.get("ph")
    if ph_val is not None and (ph_val < 0.0 or ph_val > 14.0):
        invalid_params.append(f"pH {ph_val} (outside scale 0.0 - 14.0)")

    for k in ["dissolved_oxygen", "bod", "turbidity", "tds"]:
        v = measurements.get(k)
        if v is not None and v < 0.0:
            invalid_params.append(f"{k} {v} (cannot be negative)")

    # 4. If measurements are missing or invalid, result must be INCONCLUSIVE
    if missing_keys or invalid_params:
        if missing_keys:
            reasons.append(
                f"Missing required core measurement(s): {', '.join(missing_keys)}. "
                "All 5 core parameters (pH, DO, BOD, Turbidity, TDS) are required for a conclusive assessment."
            )
        if invalid_params:
            reasons.append(
                f"Physically invalid value(s) detected: {', '.join(invalid_params)}. "
                "Data conflict prevents reliable classification."
            )

        # Build partial parameter assessments
        for key in core_keys:
            val = measurements.get(key)
            if val is None:
                parameter_assessments.append({
                    "parameter": key,
                    "display_name": _get_display_name(key),
                    "unit": _get_unit(key),
                    "value": None,
                    "standard_range": _get_standard_range(key, thresholds),
                    "status": "INSUFFICIENT",
                    "message": "Missing measurement. Parameter was not provided in input.",
                })
            elif (key == "ph" and (val < 0.0 or val > 14.0)) or (key != "ph" and val < 0.0):
                parameter_assessments.append({
                    "parameter": key,
                    "display_name": _get_display_name(key),
                    "unit": _get_unit(key),
                    "value": val,
                    "standard_range": _get_standard_range(key, thresholds),
                    "status": "FAIL",
                    "message": f"Value {val} is outside physically possible scientific bounds.",
                })
            else:
                parameter_assessments.append({
                    "parameter": key,
                    "display_name": _get_display_name(key),
                    "unit": _get_unit(key),
                    "value": val,
                    "standard_range": _get_standard_range(key, thresholds),
                    "status": "PASS",
                    "message": "Measurement provided but overall evaluation is incomplete.",
                })

        return {
            "classification": "INCONCLUSIVE",
            "result_type": "DEMO_RULE_BASED",
            "standard_name": standard_name,
            "standard_intended_use": intended_use,
            "parameter_assessments": parameter_assessments,
            "failed_parameters": invalid_params,
            "passed_parameters": [],
            "reasons": reasons,
            "warnings": ["Incomplete or invalid input data received."],
            "limitations": LIMITATIONS_DISCLOSURE,
        }

    # 5. Evaluate Complete Parameter Vector
    # A. pH Evaluation (6.5 - 8.5)
    ph = measurements["ph"]
    ph_min = thresholds["ph"]["min"]
    ph_max = thresholds["ph"]["max"]
    if ph < ph_min:
        failed_params.append("ph")
        msg = f"Acidic: pH {ph} is below the minimum limit ({ph_min}). Increases corrosive potential and metal leaching."
        parameter_assessments.append(_make_param("ph", ph, f"{ph_min} - {ph_max}", "FAIL", msg))
        reasons.append(msg)
    elif ph > ph_max:
        failed_params.append("ph")
        msg = f"Alkaline: pH {ph} exceeds the maximum limit ({ph_max}). Can cause bitter taste and decreased chlorination efficiency."
        parameter_assessments.append(_make_param("ph", ph, f"{ph_min} - {ph_max}", "FAIL", msg))
        reasons.append(msg)
    else:
        passed_params.append("ph")
        msg = f"pH {ph} is within acceptable standard range ({ph_min} - {ph_max})."
        parameter_assessments.append(_make_param("ph", ph, f"{ph_min} - {ph_max}", "PASS", msg))

    # B. Dissolved Oxygen Evaluation (>= 4.0 mg/L)
    do = measurements["dissolved_oxygen"]
    do_min = thresholds["dissolved_oxygen"]["min"]
    if do < do_min:
        failed_params.append("dissolved_oxygen")
        msg = f"Depleted Oxygen: DO {do} mg/L is below minimum required threshold ({do_min} mg/L). Indicates high organic decomposition and hypoxia."
        parameter_assessments.append(_make_param("dissolved_oxygen", do, f">= {do_min} mg/L", "FAIL", msg))
        reasons.append(msg)
    else:
        passed_params.append("dissolved_oxygen")
        msg = f"Dissolved Oxygen {do} mg/L meets the minimum standard (>= {do_min} mg/L)."
        parameter_assessments.append(_make_param("dissolved_oxygen", do, f">= {do_min} mg/L", "PASS", msg))

    # C. BOD Evaluation (<= 3.0 mg/L)
    bod = measurements["bod"]
    bod_max = thresholds["bod"]["max"]
    if bod > bod_max:
        failed_params.append("bod")
        msg = f"Excessive Organic Load: BOD {bod} mg/L exceeds the permissible threshold ({bod_max} mg/L). Indicates significant biodegradable pollution."
        parameter_assessments.append(_make_param("bod", bod, f"<= {bod_max} mg/L", "FAIL", msg))
        reasons.append(msg)
    else:
        passed_params.append("bod")
        msg = f"BOD {bod} mg/L meets the permissible threshold (<= {bod_max} mg/L)."
        if bod == bod_max:
            warnings.append(f"BOD ({bod} mg/L) is exactly at the permissible threshold limit ({bod_max} mg/L).")
        parameter_assessments.append(_make_param("bod", bod, f"<= {bod_max} mg/L", "PASS", msg))

    # D. Turbidity Evaluation (<= 5.0 NTU)
    turbidity = measurements["turbidity"]
    turb_max = thresholds["turbidity"]["max"]
    if turbidity > turb_max:
        failed_params.append("turbidity")
        msg = f"High Turbidity: Turbidity {turbidity} NTU exceeds permissible limit ({turb_max} NTU). Suspended matter impairs clarity and shields pathogens."
        parameter_assessments.append(_make_param("turbidity", turbidity, f"<= {turb_max} NTU", "FAIL", msg))
        reasons.append(msg)
    else:
        passed_params.append("turbidity")
        msg = f"Turbidity {turbidity} NTU meets the permissible limit (<= {turb_max} NTU)."
        if turbidity == turb_max:
            warnings.append(f"Turbidity ({turbidity} NTU) is at the permissible threshold boundary ({turb_max} NTU).")
        parameter_assessments.append(_make_param("turbidity", turbidity, f"<= {turb_max} NTU", "PASS", msg))

    # E. TDS Evaluation (<= 500.0 mg/L)
    tds = measurements["tds"]
    tds_max = thresholds["tds"]["max"]
    if tds > tds_max:
        failed_params.append("tds")
        msg = f"Elevated Dissolved Solids: TDS {tds} mg/L exceeds the baseline limit ({tds_max} mg/L). Indicates elevated dissolved mineral ions."
        parameter_assessments.append(_make_param("tds", tds, f"<= {tds_max} mg/L", "FAIL", msg))
        reasons.append(msg)
    else:
        passed_params.append("tds")
        msg = f"TDS {tds} mg/L is within the acceptable baseline limit (<= {tds_max} mg/L)."
        if tds == tds_max:
            warnings.append(f"TDS ({tds} mg/L) is at the baseline limit boundary ({tds_max} mg/L).")
        parameter_assessments.append(_make_param("tds", tds, f"<= {tds_max} mg/L", "PASS", msg))

    # 6. Optional Parameters (Conductivity, Nitrate, Temperature) if provided
    ec = measurements.get("electrical_conductivity")
    if ec is not None:
        ec_status = "PASS" if ec <= 1000.0 else "FAIL"
        if ec_status == "FAIL":
            warnings.append(f"Conductivity ({ec} µS/cm) is elevated (> 1000 µS/cm).")
        parameter_assessments.append({
            "parameter": "electrical_conductivity",
            "display_name": "Electrical Conductivity",
            "unit": "µS/cm",
            "value": ec,
            "standard_range": "<= 1000.0 µS/cm (Informational)",
            "status": ec_status,
            "message": f"Conductivity is {ec} µS/cm.",
        })

    nitrate = measurements.get("nitrate")
    if nitrate is not None:
        nitrate_status = "PASS" if nitrate <= 45.0 else "FAIL"
        if nitrate_status == "FAIL":
            failed_params.append("nitrate")
            msg = f"Nitrate {nitrate} mg/L exceeds the permissible limit (45.0 mg/L). Potential agricultural runoff / risk of methemoglobinemia."
            reasons.append(msg)
        else:
            passed_params.append("nitrate")
        parameter_assessments.append({
            "parameter": "nitrate",
            "display_name": "Nitrate",
            "unit": "mg/L",
            "value": nitrate,
            "standard_range": "<= 45.0 mg/L (IS 10500)",
            "status": nitrate_status,
            "message": f"Nitrate is {nitrate} mg/L.",
        })

    temp = measurements.get("temperature")
    if temp is not None:
        parameter_assessments.append({
            "parameter": "temperature",
            "display_name": "Water Temperature",
            "unit": "°C",
            "value": temp,
            "standard_range": "Ambient (Informational)",
            "status": "PASS",
            "message": f"Sample temperature is {temp} °C.",
        })

    # 7. Final Classification Decision
    if failed_params:
        classification = "HARMFUL"
        reasons.insert(0, f"Sample fails {len(failed_params)} configured safety criteria ({', '.join(failed_params)}).")
    else:
        classification = "SAFE"
        reasons.insert(
            0,
            f"All {len(passed_params)} monitored parameters pass the configured {standard_name} criteria for {intended_use}."
        )

    return {
        "classification": classification,
        "result_type": "DEMO_RULE_BASED",
        "standard_name": standard_name,
        "standard_intended_use": intended_use,
        "parameter_assessments": parameter_assessments,
        "failed_parameters": failed_params,
        "passed_parameters": passed_params,
        "reasons": reasons,
        "warnings": warnings,
        "limitations": LIMITATIONS_DISCLOSURE,
    }


def _make_param(key: str, value: float, standard_range: str, status: str, message: str) -> Dict[str, Any]:
    return {
        "parameter": key,
        "display_name": _get_display_name(key),
        "unit": _get_unit(key),
        "value": value,
        "standard_range": standard_range,
        "status": status,
        "message": message,
    }


def _get_display_name(key: str) -> str:
    names = {
        "ph": "pH",
        "dissolved_oxygen": "Dissolved Oxygen",
        "bod": "Biochemical Oxygen Demand (BOD)",
        "turbidity": "Turbidity",
        "tds": "Total Dissolved Solids (TDS)",
        "electrical_conductivity": "Electrical Conductivity",
        "nitrate": "Nitrate",
        "temperature": "Temperature",
    }
    return names.get(key, key)


def _get_unit(key: str) -> str:
    units = {
        "ph": "Dimensionless",
        "dissolved_oxygen": "mg/L",
        "bod": "mg/L",
        "turbidity": "NTU",
        "tds": "mg/L",
        "electrical_conductivity": "µS/cm",
        "nitrate": "mg/L",
        "temperature": "°C",
    }
    return units.get(key, "")


def _get_standard_range(key: str, thresholds: Dict[str, Any]) -> str:
    if key == "ph":
        return f"{thresholds['ph']['min']} - {thresholds['ph']['max']}"
    elif key == "dissolved_oxygen":
        return f">= {thresholds['dissolved_oxygen']['min']} mg/L"
    elif key == "bod":
        return f"<= {thresholds['bod']['max']} mg/L"
    elif key == "turbidity":
        return f"<= {thresholds['turbidity']['max']} NTU"
    elif key == "tds":
        return f"<= {thresholds['tds']['max']} mg/L"
    return "Standard Baseline"


# ==========================================================
# 3. GIS Marker Indicator Service (Preserved for Map & Day 5)
# ==========================================================

def classify_water_quality(latest_record: Optional[WaterQualityRecord]) -> Tuple[str, str]:
    """
    Evaluates the water quality status for a monitoring location based on its latest measurement.
    Preserved for GIS map markers (returns 'UNKNOWN' to prevent uncertified map safety indicators).

    Returns:
        tuple[str, str]: (water_quality_status, status_reason)
    """
    if latest_record is None:
        return (
            "UNKNOWN",
            "No water quality measurements have been recorded for this location yet.",
        )

    # In strict accordance with platform requirements:
    # We do not invent arbitrary thresholds for geographic map markers without formal adoption.
    return (
        "UNKNOWN",
        "Status pending adoption of approved regulatory water quality standards.",
    )
