# Coding-chatbot
Chatbot that only assists in coding solutions
# 💡 Gemini-Powered Coding Assistant

A web-based coding assistant built with **Streamlit** and powered by **Google's Gemini 1.5 Flash** model. It helps you write code, debug, and learn programming concepts in languages like **Python**, **Java**, **C++**, and more.

---

## 🚀 Features

- 🤖 AI-powered chatbot for coding questions
- 💬 Chat interface using Streamlit
- 🔐 Secure API key using `.env` and `python-dotenv`
- ⚙️ Code formatting with syntax highlighting
- ⚡ Based on Gemini 1.5 Flash model (Google Generative AI)

---

## 📦 Tech Stack

- [Streamlit](https://streamlit.io/)
- [Google Generative AI Python SDK](https://github.com/google/generative-ai-python)
- [Python 3.8+](https://www.python.org/)
- [dotenv](https://pypi.org/project/python-dotenv/)

---

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/gemini-coding-chatbot.git
cd gemini-coding-chatbot
python -m venv venv
source venv/bin/activate     # Linux/macOS
venv\Scripts\activate        # Windows

GEMINI_API_KEY=your_api_key_here

🧪 Run the App
streamlit run chat.py

📝 File Structure

├── chat.py           # Main Streamlit app
├── .env              # Environment variables (not committed)
├── .gitignore        # Ignore .env and virtual environments
├── requirements.txt  # Python dependencies
└── README.md         # This file
