Here's the complete, properly formatted README.md in a single file:

```markdown
# Homeogenie  
🏥 Medical Chatbot API  

A FastAPI-powered AI chatbot that assists healthcare professionals by collecting and managing structured patient medical histories through conversational interaction. It uses the Groq API for intelligent response generation and ChromaDB for document storage.  

---

## 🚀 Features  
- 💬 **Conversational Interface** – Interacts with patients to gather medical history  
- 🧠 **Smart NLP** – Uses Groq API for natural language processing and response generation  
- 📋 **Structured Data Extraction** – Converts chat input into structured health information  
- 🏥 **Patient Record Management** – Retrieves and updates patient records  
- 🗂️ **Conversation History Storage** – Manages persistent history with ChromaDB  
- 🔌 **RESTful API** – Seamless integration with other healthcare tools or systems  

---

## 🧰 Tech Stack  
- **Backend Framework**: FastAPI  
- **NLP & Chat Generation**: Groq API  
- **Database**: ChromaDB (Vector DB)  
- **Language**: Python 3.8+  

---

## ✅ Prerequisites  
- Python 3.8 or higher installed  
- [Groq API key](https://groq.com/)  
- ChromaDB installed locally (in-memory or persistent mode)  

---

## 📦 Installation  

### 1. Clone the repository  
```bash
git clone https://github.com/FIZAKHAN0427/Homeogenie.git
```

### 2. Set up virtual environment  
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Python dependencies  
```bash
pip install -r requirements.txt
```

---

## 🔐 Configuration  
1. Create `.env` file in the root directory:  
```ini
GROQ_API_KEY=your_groq_api_key_here
```  
Replace `your_groq_api_key_here` with your actual API key.  

---

## ▶️ Running the Application  
Start the FastAPI server:  
```bash
python -m main
```  

The API will be available at:  
`http://localhost:8000`  

Interactive Swagger UI:  
`http://localhost:8000/docs`  

---

## 🔌 API Endpoints  

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/chat/history/` | Send patient message and get chatbot response |
| GET    | `/patient/history/{patient_id}` | Retrieve a specific patient's medical history |
| GET    | `/chat/history/{conversation_id}` | Get chat history of a specific conversation |

---

## 🗂️ Project Structure  
```
Groq/
├── .env
├── chroma_db/
│   └── chroma.sqlite3
├── medical_chatbot/
│   ├── api.py
│   ├── data_extraction.py
│   ├── document_store.py
│   ├── history_manager.py
│   ├── main.py
│   ├── medical_chatbot.py
│   ├── models.py
│   ├── utils.py
│   ├── __init__.py
│   └── __pycache__/
├── README.md
├── requirements.txt
└── run.py
```


