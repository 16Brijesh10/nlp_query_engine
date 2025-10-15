# 🧠 Hybrid NL-to-SQL Engine

A schema-agnostic Natural Language Query System built using FastAPI (backend) and React (frontend).  
It dynamically connects to any PostgreSQL database, analyzes its schema, and allows natural language queries to be executed as SQL or hybrid Doc+SQL reasoning.

---

## 🚀 Features
- Dynamic schema discovery (no hardcoded tables/columns)
- Natural language → SQL translation using LLM reasoning
- Document ingestion & vector search (Chroma)
- Hybrid querying (structured + unstructured)
- Modular FastAPI backend + React frontend
- Dockerized deployment

---

## 🧩 Tech Stack
**Backend:** FastAPI, SQLAlchemy, psycopg2, Chroma  
**Frontend:** React (Vite), TailwindCSS  
**Database:** PostgreSQL  
**LLM:** Gemini / OpenAI API  
**Containerization:** Docker + Docker Compose

---

## ⚙️ Setup Instructions 

### 1️⃣ Clone and Install
git clone https://github.com/16Brijesh10/nlp_query_engine
cd hybrid-nl2sql-engine/backend
pip install -r requirements.txt

### 2️⃣ Start Database

docker-compose up -d postgres

### 3️⃣ Run Backend

uvicorn app.main:app --reload --port 8000

### 4️⃣ Run Frontend

cd ../frontend
npm install
npm run dev

Then open http://localhost:5173
