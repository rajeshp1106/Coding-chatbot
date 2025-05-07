import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai

# Load environment variables from .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Set up Gemini
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

# Code formatter
def format_code_response(text):
    if '```' not in text:
        text = f"```\n{text.strip()}\n```"
    return text

# Streamlit App
def main():
    st.set_page_config(page_title="Gemini Coding Assistant", layout="centered")
    st.title("💡 Gemini Coding Assistant")
    st.markdown("Ask questions about Python, Java, C++, Algorithms, or Debugging.")

    # Initialize session state
    if "chat" not in st.session_state:
        st.session_state.chat = setup_gemini().start_chat(history=[])
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # User input
    user_input = st.chat_input("Ask a coding question...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # System prompt
        system_prompt = """You are an expert coding assistant. Follow these rules:
        1. Respond ONLY with:
           - Complete code solutions in ```language``` blocks
           - Concise explanations (1-2 sentences)
           - Debugging fixes with before/after examples
        2. Include all necessary imports and helper functions
        3. For algorithms, include time/space complexity
        4. Decline non-coding questions politely"""

        try:
            response = st.session_state.chat.send_message(
                f"{system_prompt}\n\nQuestion: {user_input}"
            )
            formatted_response = format_code_response(response.text)
            st.session_state.messages.append({"role": "assistant", "content": formatted_response})
            with st.chat_message("assistant"):
                st.markdown(formatted_response)
        except Exception as e:
            st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
