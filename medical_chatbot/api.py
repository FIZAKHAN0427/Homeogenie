# api.py
from fastapi import FastAPI, HTTPException
from uuid import uuid4
from datetime import datetime
from typing import Dict, List, Any
import logging
import os
from .models import ChatMessage, ChatResponse, PatientHistory
from .medical_chatbot import MedicalChatbot

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create a logger
logger = logging.getLogger(__name__)

app = FastAPI()
chatbot = MedicalChatbot()

patient_histories: Dict[str, PatientHistory] = {}
chat_histories: Dict[str, List[Dict[str, Any]]] = {}

@app.post("/chat/history/", response_model=ChatResponse)
async def chat_history_endpoint(message: ChatMessage):
    try:
        conversation_id = message.conversation_id or str(uuid4())
        
        if message.patient_id not in patient_histories:
            patient_histories[message.patient_id] = PatientHistory(patient_id=message.patient_id)
        
        history = patient_histories[message.patient_id]
        
        try:
            response_data = chatbot.generate_response(message.message, history, conversation_id)
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return ChatResponse(
                response="I apologize, but I'm having trouble processing your response. Could you please try again?",
                conversation_id=conversation_id,
                speaker="bot",
                error=str(e),
                completion_status=history.completion_status
            )
        
        if conversation_id not in chat_histories:
            chat_histories[conversation_id] = []
        
        chat_histories[conversation_id].extend([
            {
                "type": "history",
                "message": message.message,
                "speaker": "patient",
                "timestamp": datetime.now().isoformat()
            },
            {
                "type": "history",
                "message": response_data["response"],
                "speaker": "bot",
                "timestamp": datetime.now().isoformat()
            }
        ])
        
        return ChatResponse(
            response=response_data["response"],
            next_question=response_data["next_question"],
            conversation_id=conversation_id,
            speaker="bot",
            data_updated=response_data["data_updated"],
            completion_status=history.completion_status
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patient/history/{patient_id}")
async def get_patient_history(patient_id: str):
    try:
        if patient_id not in patient_histories:
            raise HTTPException(status_code=404, detail="Patient history not found")
        return patient_histories[patient_id]
    except Exception as e:
        logger.error(f"Error retrieving patient history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/history/{conversation_id}")
async def get_chat_history(conversation_id: str):
    try:
        if conversation_id not in chat_histories:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return chat_histories[conversation_id]
    except Exception as e:
        logger.error(f"Error retrieving chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))