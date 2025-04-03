# utils.py
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def validate_and_normalize_extracted_data(extracted_data: Dict[str, Any], section: str) -> Dict[str, Any]:
    """Validate and normalize the structure of extracted data."""
    if "extracted" not in extracted_data:
        logger.warning(f"Missing 'extracted' key in response for {section}")
        extracted_data["extracted"] = {}

    if section == "basic_info":
        if not isinstance(extracted_data["extracted"], dict):
            logger.warning(f"'extracted' is not a dict for {section}")
            extracted_data["extracted"] = {}
        for field in ["name", "age", "gender", "height", "weight"]:
            if field not in extracted_data["extracted"]:
                extracted_data["extracted"][field] = None
    else:
        if "items" not in extracted_data["extracted"]:
            logger.warning(f"Missing 'items' key in 'extracted' for {section}")
            extracted_data["extracted"]["items"] = []
        elif not isinstance(extracted_data["extracted"]["items"], list):
            logger.warning(f"'items' is not a list for {section}, converting: {extracted_data['extracted']['items']}")
            if extracted_data["extracted"]["items"]:
                extracted_data["extracted"]["items"] = [extracted_data["extracted"]["items"]]
            else:
                extracted_data["extracted"]["items"] = []

    if "is_complete" not in extracted_data:
        extracted_data["is_complete"] = False
    if "needs_clarification" not in extracted_data:
        extracted_data["needs_clarification"] = False

    logger.debug(f"Normalized extracted data for {section}: {json.dumps(extracted_data)}")
    return extracted_data