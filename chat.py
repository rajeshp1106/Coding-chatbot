import streamlit as st
from dotenv import load_dotenv
import os
import uuid
import google.generativeai as genai
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Load env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
db_url = os.getenv("DATABASE_URL")

# Initialize DB
def init_db():
    try:
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # Create chat sessions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id UUID PRIMARY KEY,
                title VARCHAR(255),
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create chat messages table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id SERIAL PRIMARY KEY,
                session_id UUID REFERENCES chat_sessions(session_id),
                role TEXT,
                content TEXT,
                timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Database init failed: {e}")

# Gemini setup
def setup_gemini():
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config={
            "temperature": 0.5,
            "top_p": 0.95,
            "top_k": 32,
            "max_output_tokens": 2048,
        },
        safety_settings={
            "HARM_CATEGORY_HARASSMENT": "BLOCK_ONLY_HIGH",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_ONLY_HIGH",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_ONLY_HIGH",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_ONLY_HIGH",
        }
    )

# Format code
def format_code_response(text):
    if '<code>' in text or '```' in text:
        return text
    return f"```\n{text.strip()}\n```"

# Create new session
def create_new_session(session_id, first_message=None):
    try:
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        title = "New Chat" if not first_message else f"Chat: {first_message[:50]}"
        cur.execute(
            "INSERT INTO chat_sessions (session_id, title) VALUES (%s, %s)",
            (session_id, title)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"Session creation error: {e}")

# Delete session
def delete_session(session_id):
    try:
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # Delete messages first (due to foreign key constraint)
        cur.execute(
            "DELETE FROM chat_messages WHERE session_id = %s",
            (session_id,)
        )
        
        # Then delete the session
        cur.execute(
            "DELETE FROM chat_sessions WHERE session_id = %s",
            (session_id,)
        )
        
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Session deletion error: {e}")
        return False

# Save message
def store_message(session_id, role, content):
    try:
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # First check if session exists
        cur.execute("SELECT 1 FROM chat_sessions WHERE session_id = %s", (session_id,))
        if not cur.fetchone():
            create_new_session(session_id)
        
        # Store the message
        cur.execute(
            "INSERT INTO chat_messages (session_id, role, content) VALUES (%s, %s, %s)",
            (session_id, role, content)
        )
        
        # Update session title if it's the first assistant message
        if role == "assistant":
            cur.execute(
                "SELECT title FROM chat_sessions WHERE session_id = %s",
                (session_id,)
            )
            session = cur.fetchone()
            if session and session["title"] == "New Chat":
                new_title = f"Chat: {content[:50]}"
                cur.execute(
                    "UPDATE chat_sessions SET title = %s, updated_at = CURRENT_TIMESTAMP WHERE session_id = %s",
                    (new_title, session_id)
                )
        
        # Update session timestamp
        cur.execute(
            "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = %s",
            (session_id,)
        )
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        st.error(f"DB write error: {e}")

# Load session history
def load_session_messages(session_id):
    try:
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        cur.execute(
            "SELECT role, content FROM chat_messages WHERE session_id = %s ORDER BY id ASC",
            (str(session_id),))
        messages = cur.fetchall()
        cur.close()
        conn.close()
        return messages
    except Exception as e:
        st.error(f"Load history error: {e}")
        return []

# Load past sessions
def get_all_sessions():
    try:
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        cur.execute("""
            SELECT s.session_id, s.title, s.updated_at 
            FROM chat_sessions s
            ORDER BY s.updated_at DESC
            LIMIT 20
        """)
        sessions = cur.fetchall()
        cur.close()
        conn.close()
        return sessions
    except Exception as e:
        st.error(f"Session fetch error: {e}")
        return []

# Streamlit main app
def main():
    st.set_page_config(page_title="Alice - Coding Assistant", layout="centered")
    st.title("💡 Alice - Coding Assistant")
    st.markdown("Ask about Python, Java, C++, DSA, Debugging.")

    init_db()

    # Initialize session ID
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        create_new_session(st.session_state.session_id)

    # Initialize Gemini
    if "gemini_model" not in st.session_state:
        st.session_state.gemini_model = setup_gemini()
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Load any existing messages from DB
        db_messages = load_session_messages(st.session_state.session_id)
        for msg in db_messages:
            st.session_state.messages.append({"role": msg["role"], "content": msg["content"]})

    # Sidebar - Sessions
    with st.sidebar:
        st.subheader("🗂️ Chat Sessions")
        
        # Button for new chat
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.session_id = str(uuid.uuid4())
            create_new_session(st.session_state.session_id)
            st.session_state.messages = []
            st.rerun()
        
        st.divider()
        
        # List of past sessions
        past_sessions = get_all_sessions()
        for sess in past_sessions:
            sid = sess["session_id"]
            title = f"{sess['title']}"
            
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                if st.button(
                    title,
                    key=f"btn_{sid}",
                    help=f"Switch to this session",
                    use_container_width=True
                ):
                    st.session_state.session_id = str(sid)
                    st.session_state.messages = []
                    # Load messages for this session
                    db_messages = load_session_messages(st.session_state.session_id)
                    for msg in db_messages:
                        st.session_state.messages.append({"role": msg["role"], "content": msg["content"]})
                    st.rerun()
            
            with col2:
                if st.button(
                    "🗑️",
                    key=f"del_{sid}",
                    help="Delete this session"
                ):
                    if delete_session(sid):
                        if st.session_state.session_id == str(sid):
                            # If deleting current session, create a new one
                            st.session_state.session_id = str(uuid.uuid4())
                            create_new_session(st.session_state.session_id)
                            st.session_state.messages = []
                        st.rerun()

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask a coding question..."):
        # Display user message
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        store_message(st.session_state.session_id, "user", prompt)

        # System prompt
        system_prompt = """You are an expert coding assistant. Follow these rules:
        1. Respond with complete code solutions in code blocks
        2. Include concise explanations (1-2 sentences)
        3. For algorithms, give time/space complexity
        4. Decline non-coding questions politely"""

        try:
            # Get Gemini response
            with st.spinner("Thinking..."):
                chat = st.session_state.gemini_model.start_chat(history=[])
                response = chat.send_message(f"{system_prompt}\n\nQuestion: {prompt}")
                formatted_response = format_code_response(response.text)
            
            # Display assistant message
            with st.chat_message("assistant"):
                st.markdown(formatted_response)
            
            # Store in session state and DB
            st.session_state.messages.append({"role": "assistant", "content": formatted_response})
            store_message(st.session_state.session_id, "assistant", formatted_response)
            
        except Exception as e:
            st.error(f"Gemini error: {e}")

if __name__ == "__main__":
    main()