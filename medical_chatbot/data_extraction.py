# data_extraction.py
import json
import logging
from typing import Dict, List, Any
from .utils import validate_and_normalize_extracted_data

logger = logging.getLogger(__name__)

class DataExtractor:
    def __init__(self, chatbot):
        self.chatbot = chatbot

    def extract_information(self, message: str, history: Any, context: List[str]) -> Dict[str, Any]:
        """
        Extract relevant medical information from the patient's response.
        
        Args:
            message (str): The patient's response.
            history (PatientHistory): The patient's medical history.
            context (List[str]): Relevant conversation history for context.
        
        Returns:
            Dict[str, Any]: Extracted information in a structured format.
        """
        section = history.current_section
        context_str = "\n".join(context)

        # Generate the extraction prompt based on the current section
        prompt = self._get_extraction_prompt(section, message, context_str)
        
        try:
            # Get the completion from the chatbot's language model
            response = self.chatbot.get_completion(
                messages=[
                    {"role": "system", "content": "You are a medical information extraction assistant. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1  # Low temperature for deterministic responses
            )
            
            # Log the raw response for debugging
            logger.debug(f"Raw extraction response for {section}: {response}")
            
            try:
                # Parse the JSON response
                extracted_data = json.loads(response)
                logger.info(f"Successfully parsed JSON for {section}")
            except json.JSONDecodeError as e:
                # Handle invalid JSON responses
                logger.error(f"Invalid JSON response for {section}: {response}")
                logger.error(f"JSON error: {str(e)}")
                return {
                    "extracted": {"items": [] if section != "basic_info" else {}},
                    "is_complete": False,
                    "needs_clarification": True
                }
            
            # Validate and normalize the extracted data structure
            return validate_and_normalize_extracted_data(extracted_data, section)
        except Exception as e:
            # Handle any errors during extraction
            logger.error(f"Error extracting information for {section}: {e}", exc_info=True)
            return {
                "extracted": {"items": [] if section != "basic_info" else {}},
                "is_complete": False,
                "needs_clarification": True
            }

    def _get_extraction_prompt(self, section: str, message: str, context_str: str) -> str:
        """
        Generate the extraction prompt based on the current section.
        
        Args:
            section (str): The current section of the medical history (e.g., "basic_info").
            message (str): The patient's response.
            context_str (str): Relevant conversation history as a string.
        
        Returns:
            str: The extraction prompt for the language model.
        """
        if section == "basic_info":
            return f"""
            Based on the patient's response: "{message}"
            And considering this context: "{context_str}"
            Extract relevant basic medical information.
            Return a JSON object with the extracted information.
            Format the response as: {{"extracted": {{"name": "string or null", "age": number or null, "gender": "string or null", "height": "string or null", "weight": "string or null"}}, "is_complete": bool, "needs_clarification": bool}}
            """
        elif section == "medications":
            return f"""
            Based on the patient's response: "{message}"
            And considering this context: "{context_str}"
            Extract relevant medication information including:
            - Medication name
            - Dosage
            - Frequency
            Return a JSON object with the extracted information.
            Format the response as: {{"extracted": {{"items": [{{"name": "string", "dosage": "string", "frequency": "string"}}]}}, "is_complete": bool, "needs_clarification": bool}}
            """
        elif section == "allergies":
            return f"""
            Based on the patient's response: "{message}"
            And considering this context: "{context_str}"
            Extract relevant allergy information including:
            - Allergy type (e.g., food, medication, environmental)
            - Specific allergen (e.g., mushrooms, dust, pollen)
            - Severity (e.g., mild, moderate, severe)
            - Reaction type (e.g., rash, difficulty breathing)
            Return a JSON object with the extracted information.
            Format the response as: {{"extracted": {{"items": [{{"type": "string", "name": "string", "severity": "string", "reaction": "string"}}]}}, "is_complete": bool, "needs_clarification": bool}}
            """
        elif section == "chronic_conditions":
            return f"""
            Based on the patient's response: "{message}"
            And considering this context: "{context_str}"
            Extract relevant chronic condition information including:
            - Condition name
            - Diagnosis date
            - Current status
            - Treatments
            Return a JSON object with the extracted information.
            Format the response as: {{"extracted": {{"items": [{{"name": "string", "diagnosis_date": "string", "status": "string", "treatments": "string"}}]}}, "is_complete": bool, "needs_clarification": bool}}
            """
        elif section == "surgeries":
            return f"""
            Based on the patient's response: "{message}"
            And considering this context: "{context_str}"
            Extract relevant surgical history information including:
            - Surgery type
            - Date or timeframe
            - Complications
            Return a JSON object with the extracted information.
            Format the response as: {{"extracted": {{"items": [{{"type": "string", "date": "string", "complications": "string"}}]}}, "is_complete": bool, "needs_clarification": bool}}
            """
        elif section == "family_history":
            return f"""
            Based on the patient's response: "{message}"
            And considering this context: "{context_str}"
            Extract relevant family history information including:
            - Relation (e.g., mother, father)
            - Condition
            - Age of onset
            Return a JSON object with the extracted information.
            Format the response as: {{"extracted": {{"items": [{{"relation": "string", "condition": "string", "age_of_onset": "string"}}]}}, "is_complete": bool, "needs_clarification": bool}}
            """
        else:
            return f"""
            Based on the patient's response: "{message}"
            And considering this context: "{context_str}"
            Extract relevant medical information for the {section} section.
            Return a JSON object with the extracted information.
            Format the response as: {{"extracted": {{"items": []}}, "is_complete": bool, "needs_clarification": bool}}
            """