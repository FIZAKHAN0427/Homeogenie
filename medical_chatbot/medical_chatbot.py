# medical_chatbot.py
import os
import json
import logging
from typing import List, Dict, Any, Optional, Union
from dotenv import load_dotenv
from .models import PatientHistory
from .document_store import DocumentStore
import groq
from datetime import datetime
from .data_extraction import DataExtractor
from .history_manager import HistoryManager
from .utils import validate_and_normalize_extracted_data

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class MedicalChatbot:
    def __init__(self):
        self.model_name = os.getenv("MODEL_NAME", "mixtral-8x7b-32768")
        self.max_retries = int(os.getenv("RETRY_ATTEMPTS", 3))
        self.retry_delay = int(os.getenv("RETRY_DELAY", 1))
        self.doc_store = DocumentStore()
        self.sections = [
            "basic_info",
            "medications",
            "allergies",
            "chronic_conditions",
            "surgeries",
            "family_history"
        ]
        self.history_manager = HistoryManager(self.sections)
        self.data_extractor = DataExtractor(self)
        self.init_models()

    def init_models(self):
        try:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable not set")
            self.client = groq.Client(api_key=api_key)
            test_response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": "test"}],
                model=self.model_name,
                max_tokens=10
            )
            logger.info("Groq client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            raise RuntimeError(f"Failed to initialize chatbot: {str(e)}")

    def get_system_prompt(self, section: str, history: PatientHistory) -> str:
        base_prompt = """You are a medical intake chatbot conducting a patient interview. Be professional, concise, and friendly. 
        Extract relevant medical information from patient responses and maintain a natural conversation flow.
        If the patient provides unclear or incomplete information, ask for clarification.
        Do not ask repeated questions.
        Current patient information:
        """
        patient_info = f"""
        Name: {history.name if history.name else 'Not Provided'}
        Age: {history.age if history.age else 'Not provided'}
        Gender: {history.gender if history.gender else 'Not provided'}
        Height: {history.height if history.height else 'Not provided'}
        Weight: {history.weight if history.weight else 'Not provided'}
        Medications: {', '.join(history.medications) if history.medications else 'None recorded'}
        Allergies: {', '.join(history.allergies) if history.allergies else 'None recorded'}
        Chronic Conditions: {', '.join(history.chronic_conditions) if history.chronic_conditions else 'None recorded'}
        Surgeries: {', '.join(history.surgeries) if history.surgeries else 'None recorded'}
        Family History: {', '.join(history.family_history) if history.family_history else 'None recorded'}
        """
        section_prompts = {
            "basic_info": """
            For this section, collect the patient's name, age, gender, height, and weight.
            Ensure responses are in standard formats:
            - Name: text
            - Age: numerical value
            - Gender: male, female, or other
            - Height: feet and inches (e.g., 5'10")
            - Weight: pounds or kilograms
            """,
            "medications": """
            Collect information about current medications, including:
            - Medication names
            - Dosages
            - Frequency of use
            Ask follow-up questions if information is incomplete.
            """,
            "allergies": """
            Gather information about:
            - Medication allergies
            - Food allergies
            - Environmental allergies
            For each allergy, try to get severity and reaction type.
            """,
            "chronic_conditions": """
            Collect information about ongoing medical conditions:
            - Condition names
            - When diagnosed
            - Current status
            - Any treatments
            """,
            "surgeries": """
            Gather surgical history:
            - Types of surgeries
            - Dates or approximate timeframes
            - Any complications
            """,
            "family_history": """
            Collect information about:
            - Medical conditions in immediate family
            - Which relatives were affected
            - Age of onset if known
            """
        }
        return base_prompt + patient_info + section_prompts.get(section, "")

    def get_completion(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        try:
            for attempt in range(self.max_retries):
                try:
                    completion = self.client.chat.completions.create(
                        messages=messages,
                        model=self.model_name,
                        temperature=temperature,
                        max_tokens=1000
                    )
                    return completion.choices[0].message.content
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"Retry {attempt+1}/{self.max_retries} after error: {e}")
                        continue
                    else:
                        raise
            raise RuntimeError(f"Failed after {self.max_retries} attempts")
        except Exception as e:
            logger.error(f"Error in API call: {e}")
            raise

    def generate_response(self, message: str, history: PatientHistory, conversation_id: str) -> Dict[str, Any]:
        try:
            # Clean up any duplicate data first
            history = self.history_manager.clean_patient_history(history)
            
            if history.current_section is None:
                return {
                    "response": "Thank you for completing your medical history. Is there anything else you'd like to share?",
                    "next_question": None,
                    "data_updated": False
                }

            relevant_context = self.doc_store.get_relevant_context(
                message,
                history.patient_id
            )

            system_prompt = self.get_system_prompt(history.current_section, history)
            system_prompt += "\nRelevant conversation history:\n" + "\n".join(relevant_context)

            extracted_info = self.data_extractor.extract_information(message, history, relevant_context)
            data_updated = self.history_manager.update_history(history, extracted_info)

            if data_updated:
                self.doc_store.add_patient_data(
                    history.patient_id,
                    extracted_info["extracted"],
                    history.current_section
                )

            response_prompt = f"""
            {system_prompt}
            Patient's last message: "{message}"
            
            Generate an appropriate response that:
            1. Acknowledges the information provided
            2. Asks for clarification if needed
            3. Moves to the next relevant question
            
            Keep the response concise and natural. Your response should ONLY include what you would say directly to the patient.
            Do not include any instructions, explanations of your approach, or meta-commentary about how you're responding.
            Do not include JSON or raw data in the response.
            """

            response = self.get_completion(
                messages=[
                    {"role": "system", "content": "You are a professional medical intake chatbot. Respond ONLY with the exact text you would say to the patient."},
                    {"role": "user", "content": response_prompt}
                ],
                temperature=0.7
            )

            # Check for and remove any system messages or instructions that might have leaked
            response_lines = response.split('\n')
            clean_response_lines = []
            for line in response_lines:
                if not any(marker in line.lower() for marker in [
                    "while waiting for", "ensure that you", "this will establish", 
                    "by following these guidelines", "if the patient provides", 
                    "ask for clarification by saying", "you can maintain"
                ]):
                    clean_response_lines.append(line)
                    
            clean_response = '\n'.join(clean_response_lines).strip()
            
            self.doc_store.add_conversation(
                conversation_id,
                message,
                clean_response,
                {
                    "patient_id": history.patient_id,
                    "section": history.current_section,
                    "timestamp": datetime.now().isoformat()
                }
            )

            return {
                "response": clean_response,
                "next_question": None,
                "data_updated": data_updated
            }
        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            raise