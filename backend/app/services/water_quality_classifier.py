"""
AquaWatch AI - Water Quality Status Classification Service

Responsible for determining water-quality indicators and statuses for map markers.

Important Architectural & Compliance Guidelines:
1. No unapproved or invented thresholds: Without an officially approved regulatory
   standard (such as CPCB Designated Best Use Criteria or WHO guidelines) configured
   in the platform, this service returns 'UNKNOWN'.
2. Missing measurements are never assumed safe.
3. Indicators do not certify water as safe for drinking.
4. Classification is strictly rule-based/standard-based, NOT an ML prediction.
"""

from typing import Optional, Tuple
from app.models import WaterQualityRecord


def classify_water_quality(latest_record: Optional[WaterQualityRecord]) -> Tuple[str, str]:
    """
    Evaluates the water quality status for a monitoring location based on its latest measurement.

    Returns:
        tuple[str, str]: (water_quality_status, status_reason)
    """
    if latest_record is None:
        return (
            "UNKNOWN",
            "No water quality measurements have been recorded for this location yet.",
        )

    # In strict accordance with platform requirements:
    # We do not invent arbitrary thresholds. Awaiting adoption of approved regulatory standards
    # (e.g., Central Pollution Control Board (CPCB) water use criteria).
    return (
        "UNKNOWN",
        "Status pending adoption of approved regulatory water quality standards.",
    )
