# data_extraction.py
import json
import logging
import re
from typing import Dict, List, Any, Optional, Union
from .utils import validate_and_normalize_extracted_data

logger = logging.getLogger(__name__)

class DataExtractionError(Exception):
    """Custom exception for data extraction errors"""
    pass

class DataExtractor:
    def __init__(self, chatbot):
        self.chatbot = chatbot
        self.required_basic_fields = ['name', 'age']  # Minimum required fields
        self.optional_basic_fields = ['gender', 'height', 'weight']

    def extract_information(self, message: str, history: Any, context: List[str]) -> Dict[str, Any]:
        """
        Extract relevant medical information from the patient's response with robust error handling.
        
        Args:
            message (str): The patient's response.
            history (PatientHistory): The patient's medical history.
            context (List[str]): Relevant conversation history for context.
        
        Returns:
            Dict[str, Any]: Extracted information in a structured format with error handling.
        """
        if not message or not isinstance(message, str):
            error_msg = "Invalid message input - must be non-empty string"
            logger.error(error_msg)
            return self._create_error_response("basic_info", error_msg)

        section = getattr(history, 'current_section', 'basic_info')
        context_str = "\n".join(context) if context and all(isinstance(c, str) for c in context) else "No context available"

        try:
            prompt = self._get_extraction_prompt(section, message, context_str)
            if not prompt:
                raise DataExtractionError("Failed to generate extraction prompt")

            # Get the completion from the chatbot's language model
            response = self._get_chatbot_response(prompt, section)
            
            # Parse and validate the response
            extracted_data = self._parse_response(response, section)
            
            # Additional validation for basic_info completeness
            if section == "basic_info":
                extracted_data = self._validate_basic_info_completeness(extracted_data)
                extracted_data = self._normalize_weight(extracted_data)

            return extracted_data
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON response: {str(e)}"
            logger.error(error_msg)
            return self._create_error_response(section, error_msg)
        except DataExtractionError as e:
            error_msg = f"Data extraction failed: {str(e)}"
            logger.error(error_msg)
            return self._create_error_response(section, error_msg)
        except Exception as e:
            error_msg = f"Unexpected error during extraction: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return self._create_error_response(section, error_msg)

    def _get_chatbot_response(self, prompt: str, section: str) -> str:
        """Handle chatbot communication with error handling"""
        try:
            system_message = {
                "role": "system",
                "content": (
                    "You are a medical information extraction assistant. Respond only with valid JSON. "
                    "Important rules:\n"
                    "1. Mark 'is_complete' true ONLY when sufficient information is provided\n"
                    "2. For weight, always convert to kg and return as number\n"
                    "3. Be strict about required fields for each section\n"
                    f"Current section: {section}"
                )
            }

            response = self.chatbot.get_completion(
                messages=[system_message, {"role": "user", "content": prompt}],
                temperature=0.1,
                max_retries=3
            )
            
            if not response:
                raise DataExtractionError("Empty response from chatbot")
                
            return response
        except Exception as e:
            raise DataExtractionError(f"Chatbot communication failed: {str(e)}")

    def _parse_response(self, response: str, section: str) -> Dict[str, Any]:
        """Parse and validate the chatbot response"""
        try:
            extracted_data = json.loads(response)
            logger.info(f"Successfully parsed JSON for {section}")
            
            if not isinstance(extracted_data, dict):
                raise DataExtractionError("Response is not a JSON object")
                
            if 'extracted' not in extracted_data:
                raise DataExtractionError("Missing 'extracted' field in response")
                
            return validate_and_normalize_extracted_data(extracted_data, section)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response for {section}: {response}")
            raise
        except Exception as e:
            raise DataExtractionError(f"Response validation failed: {str(e)}")

    def _normalize_weight(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure weight is in kg and properly formatted"""
        if not data.get('extracted'):
            return data
            
        extracted = data['extracted']
        weight = extracted.get('weight')
        
        if weight is None:
            return data
            
        try:
            # Handle string inputs
            if isinstance(weight, str):
                weight = weight.lower().strip()
                
                # Extract numeric value
                num_match = re.search(r'(\d+\.?\d*)', weight)
                if not num_match:
                    raise ValueError("No numeric weight value found")
                    
                numeric_value = float(num_match.group(1))
                
                # Convert units if needed
                if 'lb' in weight or 'pound' in weight:
                    numeric_value *= 0.453592  # Convert lbs to kg
                
                weight = numeric_value
            elif isinstance(weight, (int, float)):
                weight = float(weight)
            else:
                raise TypeError("Invalid weight type")
                
            extracted['weight'] = round(weight, 2)
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Weight normalization failed: {str(e)}")
            extracted['weight'] = None
            data['needs_clarification'] = True
            if 'clarification_message' not in data:
                data['clarification_message'] = "Please provide weight in kg or lbs (e.g., '70 kg' or '150 lbs')"
                    
        return data

    def _validate_basic_info_completeness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure basic info has required fields before marking complete"""
        if not data.get('extracted'):
            return data
            
        extracted = data['extracted']
        
        # Check required fields
        is_complete = all(
            extracted.get(field) not in [None, ""] 
            for field in self.required_basic_fields
        )
        
        # Update completeness flags
        data['is_complete'] = is_complete
        if not is_complete:
            data['needs_clarification'] = True
            missing_fields = [
                f for f in self.required_basic_fields 
                if not extracted.get(f)
            ]
            data['clarification_message'] = (
                f"Please provide: {', '.join(missing_fields)}. "
                "For weight, specify units (kg or lbs)."
            )
        
        return data

    def _create_error_response(self, section: str, error_msg: Optional[str] = None) -> Dict[str, Any]:
        """Create a standardized error response with clarification guidance"""
        response = {
            "extracted": {"items": [] if section != "basic_info" else {
                "name": None,
                "age": None,
                "gender": None,
                "height": None,
                "weight": None
            }},
            "is_complete": False,
            "needs_clarification": True,
            "error": error_msg,
            "success": False
        }
        
        if section == "basic_info":
            response["clarification_message"] = (
                f"Please provide your name and age to continue. {error_msg or ''}"
                "For weight, please specify kg or lbs (e.g., '70 kg' or '150 lbs')."
            )
        
        return response

    def _get_extraction_prompt(self, section: str, message: str, context_str: str) -> str:
        """
        Generate the extraction prompt with detailed section-specific instructions.
        Maintains all original specialized prompts while adding weight handling.
        """
        if section == "basic_info":
            return f"""
            Based on the patient's response: "{message}"
            And considering this context: "{context_str}"
            Extract relevant basic medical information with these requirements:
            1. REQUIRED fields: name and age (must have both to mark complete)
            2. OPTIONAL fields: gender, height, weight
            3. For weight: Convert to kilograms if needed and return as number
            4. For height: Keep original format (e.g., '170 cm')
            
            Return JSON with this exact structure:
            {{
                "extracted": {{
                    "name": "string or null",
                    "age": number or null,
                    "gender": "string or null",
                    "height": "string or null",
                    "weight": number or null  // MUST be in kg
                }},
                "is_complete": boolean,  // true ONLY if name AND age are provided
                "needs_clarification": boolean
            }}
            """
        elif section == "medications":
            return f"""
            Based on the patient's response: "{message}"
            And considering this context: "{context_str}"
            Extract medication information with these requirements:
            1. For each medication, capture: name, dosage, frequency
            2. Mark complete if at least one complete medication is found
            3. Mark needs_clarification if any information is unclear
            
            Return JSON with this exact structure:
            {{
                "extracted": {{
                    "items": [
                        {{
                            "name": "string",
                            "dosage": "string",
                            "frequency": "string"
                        }}
                    ]
                }},
                "is_complete": boolean,
                "needs_clarification": boolean
            }}
            """
        elif section == "allergies":
            return f"""
            Based on the patient's response: "{message}"
            And considering this context: "{context_str}"
            Extract allergy information with these requirements:
            1. For each allergy, capture: type, name, severity, reaction
            2. Type should be one of: food, medication, environmental, other
            3. Mark complete if at least one complete allergy is found
            
            Return JSON with this exact structure:
            {{
                "extracted": {{
                    "items": [
                        {{
                            "type": "string",
                            "name": "string",
                            "severity": "string",
                            "reaction": "string"
                        }}
                    ]
                }},
                "is_complete": boolean,
                "needs_clarification": boolean
            }}
            """
        elif section == "chronic_conditions":
            return f"""
            Based on the patient's response: "{message}"
            And considering this context: "{context_str}"
            Extract chronic condition information with these requirements:
            1. For each condition, capture: name, diagnosis_date, status, treatments
            2. Diagnosis date can be approximate (e.g., "2015", "3 years ago")
            3. Mark complete if at least one complete condition is found
            
            Return JSON with this exact structure:
            {{
                "extracted": {{
                    "items": [
                        {{
                            "name": "string",
                            "diagnosis_date": "string",
                            "status": "string",
                            "treatments": "string"
                        }}
                    ]
                }},
                "is_complete": boolean,
                "needs_clarification": boolean
            }}
            """
        elif section == "surgeries":
            return f"""
            Based on the patient's response: "{message}"
            And considering this context: "{context_str}"
            Extract surgery information with these requirements:
            1. For each surgery, capture: type, date, complications
            2. Date can be approximate (e.g., "2018", "last year")
            3. Mark complete if at least one complete surgery is found
            
            Return JSON with this exact structure:
            {{
                "extracted": {{
                    "items": [
                        {{
                            "type": "string",
                            "date": "string",
                            "complications": "string"
                        }}
                    ]
                }},
                "is_complete": boolean,
                "needs_clarification": boolean
            }}
            """
        elif section == "family_history":
            return f"""
            Based on the patient's response: "{message}"
            And considering this context: "{context_str}"
            Extract family history information with these requirements:
            1. For each entry, capture: relation, condition, age_of_onset
            2. Relation should be family member (e.g., "mother", "grandfather")
            3. Mark complete if at least one complete entry is found
            
            Return JSON with this exact structure:
            {{
                "extracted": {{
                    "items": [
                        {{
                            "relation": "string",
                            "condition": "string",
                            "age_of_onset": "string"
                        }}
                    ]
                }},
                "is_complete": boolean,
                "needs_clarification": boolean
            }}
            """
        else:
            return f"""
            Based on the patient's response: "{message}"
            And considering this context: "{context_str}"
            Extract relevant medical information for the {section} section.
            
            Return JSON with this exact structure:
            {{
                "extracted": {{
                    "items": []
                }},
                "is_complete": boolean,
                "needs_clarification": boolean
            }}
            """