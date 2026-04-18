import os
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from groq import Groq
from dotenv import load_dotenv
from app.db.database import cursor, conn

# ===============================
# LOAD ENV
# ===============================
from dotenv import load_dotenv
load_dotenv()  # safe for both local + render

print("ENV PATH:", ENV_PATH)
print("FILE EXISTS:", os.path.exists(ENV_PATH))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
print("KEY:", GROQ_API_KEY)

if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY not found in .env")

client = Groq(api_key=GROQ_API_KEY)

# ===============================
# MEMORY
# ===============================
chat_memory = {}

# ===============================
# PATH
# ===============================
DATA_PATH = "app/data/docs"

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"❌ Folder not found: {DATA_PATH}")

# ===============================
# EMBEDDING MODEL
# ===============================
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# ===============================
# LOAD PDFs
# ===============================
def load_pdfs():
    texts = []

    for file in os.listdir(DATA_PATH):
        if file.endswith(".pdf"):
            pdf_path = os.path.join(DATA_PATH, file)

            try:
                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        texts.append(text)
            except Exception as e:
                print(f"⚠️ Error reading {file}: {e}")

    if not texts:
        print("⚠️ No PDF content found")
        return []

    return texts

# ===============================
# CHUNK TEXT
# ===============================
def chunk_text(texts, chunk_size=500):
    chunks = []

    for text in texts:
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i:i + chunk_size])

    return chunks

# ===============================
# CREATE VECTOR STORE
# ===============================
def create_vector_store():
    print("📄 Loading PDFs...")
    texts = load_pdfs()

    if not texts:
        return None, []

    print("✂️ Chunking...")
    chunks = chunk_text(texts)

    print("🧠 Creating embeddings...")
    embeddings = embedding_model.encode(chunks)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))

    print("✅ Vector store ready")
    return index, chunks

# ===============================
# INIT VECTOR STORE
# ===============================
try:
    index, chunks = create_vector_store()
except Exception as e:
    print(f"⚠️ Init failed: {e}")
    index, chunks = None, []

# ===============================
# SEARCH
# ===============================
def search(query, top_k=2):
    if index is None or len(chunks) == 0:
        return ["No data available in PDF"]

    query_embedding = embedding_model.encode([query])
    distances, indices = index.search(np.array(query_embedding), top_k)

    return [chunks[i] for i in indices[0]]

# ===============================
# SAVE CHAT TO DB
# ===============================
def save_message(session_id, role, message):
    cursor.execute(
        "INSERT INTO chats (session_id, role, message) VALUES (?, ?, ?)",
        (session_id, role, message)
    )
    conn.commit()

# ===============================
# MAIN RAG FUNCTION
# ===============================
def ask_rag(query: str, session_id: str = "default"):
    try:
        relevant_chunks = search(query, top_k=2)

        # 🚫 No data fallback
        if not relevant_chunks or relevant_chunks == ["No data available in PDF"]:
            return "⚠️ Please upload a PDF first."

        context = "\n".join(relevant_chunks)

        prompt = f"""
You are a solar energy assistant.

Answer ONLY from the context below.
Keep the answer short (max 3-4 lines).
Be clear and helpful.

If answer not found, say "I don't know".

Context:
{context}

Question:
{query}
"""

        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful solar assistant."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
        )

        # 🛑 Safe response handling
        if not response or not response.choices:
            return "⚠️ No response from AI"

        answer = response.choices[0].message.content or "⚠️ Empty response"

        # 💾 Memory
        chat_memory.setdefault(session_id, []).append(("user", query))
        chat_memory.setdefault(session_id, []).append(("bot", answer))

        # 💾 Database
        save_message(session_id, "user", query)
        save_message(session_id, "bot", answer)

        return answer

    except Exception as e:
        import traceback
        print("🔥 FULL ERROR:")
        traceback.print_exc()

        return f"❌ Error: {str(e)}"

# ===============================
# STREAM RESPONSE
# ===============================
def ask_rag_stream(query: str, session_id: str = "default"):
    response_text = ask_rag(query, session_id)

    for char in response_text:
        yield char