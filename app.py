# app.py
import os
import time
import logging
from functools import wraps
from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI, RateLimitError, APIError, Timeout
from utils import parse_prd_file, fill_prd_template, prd_template

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, filename="app.log", filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
PASSWORD = os.getenv("APP_PASSWORD")
API_KEY = os.getenv("OPENAI_API_KEY")
oai_client = OpenAI(api_key=API_KEY)

# Retry decorator with rate limits and fallback
RATE_LIMIT_SECONDS = 3

def retry_with_backoff(max_retries=3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = RATE_LIMIT_SECONDS
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (RateLimitError, Timeout) as e:
                    logging.warning(f"Rate limit or timeout error: {e}. Retrying in {delay} seconds...")
                    time.sleep(delay)
                    delay *= 2
                except APIError as e:
                    logging.error(f"API error: {e}")
                    break
                except Exception as e:
                    logging.error(f"Unexpected error: {e}")
                    break
            return "⚠️ Sorry, something went wrong. Please try again later."
        return wrapper
    return decorator

# Streamlit App
st.set_page_config(page_title="PRD Chatbot", layout="wide")
st.markdown("""
    <style>
    .centered-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        backdrop-filter: blur(8px);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
        background-color: rgba(255, 255, 255, 0.5);
    }
    .password-box {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 0 25px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Password Gate
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    with st.container():
        st.markdown('<div class="centered-container"><div class="password-box">', unsafe_allow_html=True)
        password_input = st.text_input("Enter Password", type="password")
        if password_input == PASSWORD:
            st.session_state.authenticated = True
            st.success("Access granted!")
            st.rerun()
        elif password_input:
            st.error("Incorrect password. Please try again.")
        st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop()

# ==== Main App Interface ====
st.title("📄 PRD Assistant Chatbot")

st.sidebar.header("Upload Existing PRD")
uploaded_file = st.sidebar.file_uploader("Choose a PRD file", type=["docx", "pdf", "md", "txt"])

context_from_file = ""
if uploaded_file:
    try:
        context_from_file = parse_prd_file(uploaded_file)
        st.sidebar.success("Document parsed successfully.")
    except Exception as e:
        logging.error(f"File parsing error: {e}")
        st.sidebar.error("Failed to parse file. Please try another format.")

st.write("👩‍💼 *Hello! I’m your PRD secretary. I’ll help you fill this out. Just answer my questions!*")

# Initialize chat history
if "chat" not in st.session_state:
    st.session_state.chat = []
    st.session_state.answers = {}

# Ask questions and collect answers
questions = [
    ("Title", "What is the title of the product or feature?"),
    ("Purpose", "Why does this product exist? What problem does it solve?"),
    ("Target Audience", "Who is the primary audience for this product?"),
    ("User Personas", "Can you describe the main user personas?")
    # More questions can be added as needed
]

for field, question in questions:
    if field not in st.session_state.answers:
        example = " (e.g., 'Productivity Dashboard for Analysts')" if field == "Title" else ""
        user_input = st.text_input(f"{question}{example}")
        if user_input:
            st.session_state.answers[field] = user_input
            st.rerun()

# Call OpenAI API with retry logic
@retry_with_backoff()
def generate_prd_response(context):
    response = oai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an experienced product assistant who helps fill out Product Requirement Documents thoroughly."},
            {"role": "user", "content": context}
        ],
        temperature=0.5
    )
    return response.choices[0].message.content

# Finalize
if st.button("📝 Generate PRD"):
    try:
        combined_input = context_from_file + "\n\n" + "\n".join([f"{k}: {v}" for k, v in st.session_state.answers.items()])
        prd_output = generate_prd_response(combined_input)
        completed_prd = fill_prd_template(prd_template, prd_output)
        st.session_state.final_prd = completed_prd
        st.success("PRD successfully generated!")
        st.download_button("📥 Download Now", completed_prd, file_name="Filled_PRD.txt")
    except Exception as e:
        logging.error(f"Final PRD generation error: {e}")
        st.error("Failed to generate the PRD. Please try again later.")
