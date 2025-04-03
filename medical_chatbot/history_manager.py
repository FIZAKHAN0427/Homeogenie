# history_manager.py
import logging
from datetime import datetime
from typing import Dict, Any, List
from .models import PatientHistory

logger = logging.getLogger(__name__)

class HistoryManager:
    def __init__(self, sections: List[str]):
        self.sections = sections

    def clean_patient_history(self, history: PatientHistory) -> PatientHistory:
        """Clean up duplicate entries and invalid data in patient history."""
        logger.info(f"Cleaning patient history for patient ID: {history.patient_id}")
        
        history.medications = self._clean_list(history.medications, "medications")
        history.allergies = self._clean_allergies(history.allergies)
        history.chronic_conditions = self._clean_list(history.chronic_conditions, "chronic conditions")
        history.surgeries = self._clean_list(history.surgeries, "surgeries")
        history.family_history = self._clean_list(history.family_history, "family history")
        
        logger.info(f"Cleaned history now has: " + 
                  f"Medications: {len(history.medications)}, " +
                  f"Allergies: {len(history.allergies)}, " +
                  f"Conditions: {len(history.chronic_conditions)}, " +
                  f"Surgeries: {len(history.surgeries)}, " +
                  f"Family history: {len(history.family_history)}")
        
        return history

    def _clean_list(self, items: List[str], item_type: str) -> List[str]:
        """Remove duplicates from a list while preserving order."""
        seen = set()
        unique_items = []
        for item in items:
            if item not in seen and item.strip():
                seen.add(item)
                unique_items.append(item)
        logger.info(f"Removed {len(items) - len(unique_items)} duplicate {item_type}")
        return unique_items

    def _clean_allergies(self, allergies: List[str]) -> List[str]:
        """Special handling for allergies to deal with 'Unknown' entries."""
        if all(a == "Unknown" for a in allergies):
            return ["Unknown"] if allergies else []
        else:
            seen = set()
            unique_allergies = []
            for allergy in allergies:
                if allergy not in seen and allergy.strip():
                    if allergy == "Unknown" and len(seen) > 0:
                        continue
                    seen.add(allergy)
                    unique_allergies.append(allergy)
            logger.info(f"Removed {len(allergies) - len(unique_allergies)} duplicate/invalid allergies")
            return unique_allergies

    def update_history(self, history: PatientHistory, extracted_info: Dict[str, Any]) -> bool:
        """Update the patient history based on extracted information."""
        section = history.current_section
        if not extracted_info.get("extracted"):
            logger.warning(f"No extracted data for {section}")
            return False

        extracted_data = extracted_info["extracted"]
        logger.info(f"Updating history for section {section}")

        if section == "basic_info":
            self._update_basic_info(history, extracted_data)
        elif section == "medications":
            self._update_medications(history, extracted_data)
        elif section == "allergies":
            self._update_allergies(history, extracted_data)
        elif section == "chronic_conditions":
            self._update_chronic_conditions(history, extracted_data)
        elif section == "surgeries":
            self._update_surgeries(history, extracted_data)
        elif section == "family_history":
            self._update_family_history(history, extracted_data)

        if extracted_info.get("is_complete", False):
            self._mark_section_complete(history, section)

        history.last_updated = datetime.now()
        logger.info(f"Updated history for section {section}. Current status: " + 
                    f"Medications: {len(history.medications)}, " +
                    f"Allergies: {len(history.allergies)}, " +
                    f"Conditions: {len(history.chronic_conditions)}, " +
                    f"Surgeries: {len(history.surgeries)}, " +
                    f"Family history: {len(history.family_history)}")
        return True

    def _update_basic_info(self, history: PatientHistory, extracted_data: Dict[str, Any]):
        """Update basic info fields (name, age, gender, height, weight)."""
        for key in ["name", "age", "gender", "height", "weight"]:
            if key in extracted_data and extracted_data[key] is not None:
                current_value = getattr(history, key)
                new_value = extracted_data[key]
                logger.info(f"Updating {key}: '{current_value}' -> '{new_value}'")
                setattr(history, key, new_value)

    def _update_medications(self, history: PatientHistory, extracted_data: Dict[str, Any]):
        """Add medications to the list."""
        new_medications = extracted_data.get("items", [])
        if not isinstance(new_medications, list):
            logger.warning(f"Medications items is not a list: {new_medications}")
            new_medications = [new_medications] if new_medications else []

        for med in new_medications:
            if isinstance(med, dict):
                med_name = med.get('name', 'Unknown medication')
                med_str = med_name
                if 'dosage' in med and med['dosage']:
                    med_str += f" - {med.get('dosage')}"
                if 'frequency' in med and med['frequency']:
                    med_str += f" - {med.get('frequency')}"
                if med_str not in history.medications:
                    logger.info(f"Adding medication: {med_str}")
                    history.medications.append(med_str)
            elif isinstance(med, str) and med.strip():
                if med not in history.medications:
                    logger.info(f"Adding medication: {med}")
                    history.medications.append(med)

    def _update_allergies(self, history: PatientHistory, extracted_data: Dict[str, Any]):
        """Add allergies to the list."""
        new_allergies = extracted_data.get("items", [])
        if not isinstance(new_allergies, list):
            logger.warning(f"Allergies items is not a list: {new_allergies}")
            new_allergies = [new_allergies] if new_allergies else []

        for allergy in new_allergies:
            if isinstance(allergy, dict):
                allergy_components = []
                if 'name' in allergy and allergy['name']:
                    allergy_components.append(allergy['name'])
                else:
                    allergy_components.append('Unknown allergy')
                if 'severity' in allergy and allergy['severity']:
                    allergy_components.append(f"Severity: {allergy['severity']}")
                if 'reaction' in allergy and allergy['reaction']:
                    allergy_components.append(f"Reaction: {allergy['reaction']}")
                allergy_str = " - ".join(allergy_components)
                if allergy_str not in history.allergies:
                    logger.info(f"Adding allergy: {allergy_str}")
                    history.allergies.append(allergy_str)
            elif isinstance(allergy, str) and allergy.strip():
                if allergy not in history.allergies:
                    logger.info(f"Adding allergy: {allergy}")
                    history.allergies.append(allergy)

    def _update_chronic_conditions(self, history: PatientHistory, extracted_data: Dict[str, Any]):
        """Add chronic conditions to the list."""
        new_conditions = extracted_data.get("items", [])
        if not isinstance(new_conditions, list):
            logger.warning(f"Chronic conditions items is not a list: {new_conditions}")
            new_conditions = [new_conditions] if new_conditions else []

        for condition in new_conditions:
            if isinstance(condition, dict):
                condition_components = []
                if 'name' in condition and condition['name']:
                    condition_components.append(condition['name'])
                else:
                    condition_components.append('Unknown condition')
                if 'diagnosis_date' in condition and condition['diagnosis_date']:
                    condition_components.append(f"Diagnosed: {condition['diagnosis_date']}")
                if 'status' in condition and condition['status']:
                    condition_components.append(f"Status: {condition['status']}")
                condition_str = " - ".join(condition_components)
                if condition_str not in history.chronic_conditions:
                    logger.info(f"Adding chronic condition: {condition_str}")
                    history.chronic_conditions.append(condition_str)
            elif isinstance(condition, str) and condition.strip():
                if condition not in history.chronic_conditions:
                    logger.info(f"Adding chronic condition: {condition}")
                    history.chronic_conditions.append(condition)

    def _update_surgeries(self, history: PatientHistory, extracted_data: Dict[str, Any]):
        """Add surgeries to the list."""
        new_surgeries = extracted_data.get("items", [])
        if not isinstance(new_surgeries, list):
            logger.warning(f"Surgeries items is not a list: {new_surgeries}")
            new_surgeries = [new_surgeries] if new_surgeries else []

        for surgery in new_surgeries:
            if isinstance(surgery, dict):
                surgery_components = []
                if 'type' in surgery and surgery['type']:
                    surgery_components.append(surgery['type'])
                elif 'name' in surgery and surgery['name']:
                    surgery_components.append(surgery['name'])
                else:
                    surgery_components.append('Unknown surgery')
                if 'date' in surgery and surgery['date']:
                    surgery_components.append(f"Date: {surgery['date']}")
                if 'complications' in surgery and surgery['complications']:
                    surgery_components.append(f"Complications: {surgery['complications']}")
                surgery_str = " - ".join(surgery_components)
                if surgery_str not in history.surgeries:
                    logger.info(f"Adding surgery: {surgery_str}")
                    history.surgeries.append(surgery_str)
            elif isinstance(surgery, str) and surgery.strip():
                if surgery not in history.surgeries:
                    logger.info(f"Adding surgery: {surgery}")
                    history.surgeries.append(surgery)

    def _update_family_history(self, history: PatientHistory, extracted_data: Dict[str, Any]):
        """Add family history to the list."""
        new_family_history = extracted_data.get("items", [])
        if not isinstance(new_family_history, list):
            logger.warning(f"Family history items is not a list: {new_family_history}")
            new_family_history = [new_family_history] if new_family_history else []

        for family_member in new_family_history:
            if isinstance(family_member, dict):
                history_components = []
                if 'relation' in family_member and family_member['relation']:
                    history_components.append(family_member['relation'])
                else:
                    history_components.append('Unknown relation')
                if 'condition' in family_member and family_member['condition']:
                    history_components.append(f"Condition: {family_member['condition']}")
                if 'age_of_onset' in family_member and family_member['age_of_onset']:
                    history_components.append(f"Age of onset: {family_member['age_of_onset']}")
                history_str = " - ".join(history_components)
                if history_str not in history.family_history:
                    logger.info(f"Adding family history: {history_str}")
                    history.family_history.append(history_str)
            elif isinstance(family_member, str) and family_member.strip():
                if family_member not in history.family_history:
                    logger.info(f"Adding family history: {family_member}")
                    history.family_history.append(family_member)

    def _mark_section_complete(self, history: PatientHistory, section: str):
        """Mark the section as complete and move to the next incomplete section."""
        logger.info(f"Marking section {section} as complete")
        history.completion_status[section] = True
        next_incomplete = next(
            (s for s in self.sections if not history.completion_status.get(s, False)),
            None
        )
        if next_incomplete:
            logger.info(f"Moving to next incomplete section: {next_incomplete}")
            history.current_section = next_incomplete
        else:
            logger.info("All sections complete")
            history.current_section = None