# models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class PatientSymptom(BaseModel):
    name: str
    severity: Optional[str] = None
    duration: Optional[str] = None
    notes: Optional[str] = None

class PatientVitals(BaseModel):
    blood_pressure: Optional[str] = None
    heart_rate: Optional[int] = None
    temperature: Optional[float] = None
    oxygen_saturation: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class PatientHistory(BaseModel):
    patient_id: str
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    medications: List[str] = []
    allergies: List[str] = []
    chronic_conditions: List[str] = []
    surgeries: List[str] = []
    family_history: List[str] = []
    last_updated: datetime = Field(default_factory=datetime.now)
    current_section: str = "basic_info"
    completion_status: Dict[str, bool] = Field(default_factory=lambda: {
        "basic_info": False,
        "medications": False,
        "allergies": False,
        "chronic_conditions": False,
        "surgeries": False,
        "family_history": False
    })

class ChatMessage(BaseModel):
    message: str
    patient_id: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    next_question: Optional[str] = None
    conversation_id: str
    speaker: str
    data_updated: bool = False
    completion_status: Dict[str, bool] = {}
    error: Optional[str] = None