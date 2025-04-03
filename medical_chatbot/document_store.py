# document_store.py
import chromadb
from uuid import uuid4
import json
from typing import Dict, List, Any
from sentence_transformers import SentenceTransformer
from datetime import datetime

class DocumentStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.conversation_history = self.client.get_or_create_collection("conversation_history")
        self.patient_data = self.client.get_or_create_collection("patient_data")

    def add_conversation(self, conversation_id: str, message: str, response: str, metadata: Dict):
        context = f"User: {message}\nBot: {response}"
        embedding = self.encoder.encode(context).tolist()
        self.conversation_history.add(
            documents=[context],
            embeddings=[embedding],
            metadatas=[metadata],
            ids=[str(uuid4())]
        )

    def add_patient_data(self, patient_id: str, data: Dict, section: str):
        context = json.dumps(data)
        embedding = self.encoder.encode(context).tolist()
        self.patient_data.add(
            documents=[context],
            embeddings=[embedding],
            metadatas=[{"patient_id": patient_id, "section": section}],
            ids=[str(uuid4())]
        )

    def get_relevant_context(self, query: str, patient_id: str, k: int = 5) -> List[str]:
        query_embedding = self.encoder.encode(query).tolist()
        conv_results = self.conversation_history.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where={"patient_id": patient_id}
        )
        data_results = self.patient_data.query(
            query_embeddings=[query_embedding],
            n_results=k,
            where={"patient_id": patient_id}
        )
        context = []
        if conv_results and conv_results['documents']:
            context.extend(conv_results['documents'][0])
        if data_results and data_results['documents']:
            context.extend(data_results['documents'][0])
        return context