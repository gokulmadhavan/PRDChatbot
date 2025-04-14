import streamlit as st
from dotenv import load_dotenv
from utils import prd_template, prd_fields_and_questions, fill_prd_template
import os
import openai
import time
from io import BytesIO
from docx import Document
from fpdf import FPDF

# --- Setup ---
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
APP_PASSWORD = os.getenv("APP_PASSWORD", "secret123")

st.set_page_config(page_title="PRD Chatbot", layout="centered")

# --- Session State ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_field" not in st.session_state:
    st.session_state.last_field = None
if "export_format" not in st.session_state:
    st.session_state.export_format = "txt"

# --- Password Modal ---
def show_password_modal():
    st.markdown("""
        <style>
        .stApp { backdrop-filter: blur(6px); }
        .password-box {
            background-color: white;
            padding: 2rem;
            border-radius: 10px;
            max-width: 400px;
            margin: 8% auto;
            box-shadow: 0 0 15px rgba(0,0,0,0.15);
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="password-box">', unsafe_allow_html=True)
        st.markdown("### 🔐 Enter Password")
        password_input = st.text_input("Password", type="password")
        if st.button("Unlock"):
            if password_input == APP_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password.")
        st.markdown("</div>", unsafe_allow_html=True)

if not st.session_state.authenticated:
    show_password_modal()
    st.stop()

# --- Inference Helper ---
def infer_fields_from_text(text, current_answers):
    prompt = "You're a helpful assistant filling out a Product Requirement Document (PRD). Extract as many fields as possible from this input and return them in the format:\n\nTitle: ...\nPurpose: ...\n...\n\nOnly include fields from this list:\n" + ", ".join([f[0] for f in prd_fields_and_questions]) + f"\n\nUser input:\n{text}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # or "gpt-4", replace as needed
            messages=[{"role": "system", "content": prompt}],
            temperature=0.3
        )
        content = response.choices[0].message.content
        updates = {}
        for line in content.strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                k, v = k.strip(), v.strip()
                if k in [f[0] for f in prd_fields_and_questions] and v:
                    updates[k] = v
        return updates
    except openai.error.RateLimitError:
        st.warning("⚠️ Rate limit hit. Please wait a moment.")
        time.sleep(5)
        return {}
    except Exception as e:
        st.error(f"❌ Error contacting OpenAI: {e}")
        return {}

# --- Chat Display ---
st.title("📄 PRD Chatbot Assistant")

for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(message)

# --- Next Field Logic ---
next_q = None
for field, question in prd_fields_and_questions:
    if field not in st.session_state.answers:
        next_q = (field, question)
        break

# --- Chat Interaction ---
if next_q:
    field, question = next_q
    with st.chat_message("assistant"):
        st.markdown(f"**{question}**")

    user_input = st.chat_input("Your response...")
    if user_input:
        st.session_state.chat_history.append(("user", user_input))
        inferred = infer_fields_from_text(user_input, st.session_state.answers)
        st.session_state.answers.update(inferred)
        if field not in inferred:
            st.session_state.answers[field] = user_input
        with st.chat_message("assistant"):
            st.markdown("✅ Got it. Updating the document...")
        st.rerun()
else:
    with st.chat_message("assistant"):
        st.markdown("🎉 All set! You can download your PRD below or preview it live.")

# --- Filled PRD ---
filled_prd = fill_prd_template(prd_template, st.session_state.answers)

# --- Export Options ---
st.subheader("📦 Export Options")
format = st.selectbox("Choose format", ["txt", "md", "docx", "pdf"])
st.session_state.export_format = format

def convert_and_download(format, content):
    if format == "txt":
        st.download_button("📥 Download TXT", content, file_name="PRD.txt")
    elif format == "md":
        st.download_button("📥 Download Markdown", content, file_name="PRD.md")
    elif format == "docx":
        doc = Document()
        for para in content.split("\n"):
            doc.add_paragraph(para)
        buffer = BytesIO()
        doc.save(buffer)
        st.download_button("📥 Download DOCX", buffer.getvalue(), file_name="PRD.docx")
    elif format == "pdf":
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in content.split("\n"):
            pdf.multi_cell(0, 8, txt=line)
        buffer = BytesIO()
        pdf.output(buffer)
        st.download_button("📥 Download PDF", buffer.getvalue(), file_name="PRD.pdf")

convert_and_download(format, filled_prd)

# --- Live Preview ---
with st.expander("📄 Live Preview of PRD", expanded=True):
    st.markdown("```markdown\n" + filled_prd + "\n```")
