import streamlit as st
from dotenv import load_dotenv
from utils import prd_template, prd_fields_and_questions, fill_prd_template
from openai import OpenAI, RateLimitError, APIError
import os, time, json
from io import BytesIO
from docx import Document
from fpdf import FPDF

# ── ENV / CLIENT ────────────────────────────────────────────────────────────────
load_dotenv()
MODEL_NAME   = os.getenv("MODEL_NAME", "gpt-4o-mini")     # or gpt-4o
APP_PASSWORD = os.getenv("APP_PASSWORD", "secret123")
client       = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── PAGE & STATE ────────────────────────────────────────────────────────────────
st.set_page_config("PRD Chatbot", layout="centered")

state = st.session_state
state.setdefault("authenticated",   False)
state.setdefault("answers",         {})      # field → text
state.setdefault("chat_history",    [])      # list[(role,msg)]
state.setdefault("pending_question", None)   # last question asked

# ── PASSWORD GATE ───────────────────────────────────────────────────────────────
def password_modal():
    st.markdown("""
        <style>
        .stApp{backdrop-filter:blur(6px);}
        .pwd{background:#fff;padding:2rem;border-radius:8px;
             max-width:350px;margin:10% auto;box-shadow:0 0 12px rgba(0,0,0,.15);}
        </style>""", unsafe_allow_html=True)
    st.markdown('<div class="pwd">', unsafe_allow_html=True)
    st.markdown("### 🔐 Enter Password")
    pw = st.text_input("Password", type="password")
    if st.button("Unlock"):
        if pw == APP_PASSWORD:
            state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.markdown("</div>", unsafe_allow_html=True)

if not state.authenticated:
    password_modal()
    st.stop()

# ── LLM HELPER ─────────────────────────────────────────────────────────────────
FIELD_NAMES = [f[0] for f in prd_fields_and_questions]

def llm_extract_and_ask(user_text:str, answers:dict):
    """
    Returns dict(extracted_fields:dict, next_question:str|None)
    """
    sys = (
        "You are an expert product‑requirements interviewer. "
        "You have the PRD field list below. "
        "1️⃣ Extract ANY fields you see in the user's reply. If the user's reply is a question, answer it first.\n"
        "2️⃣ If some fields remain blank, ask ONE concise follow‑up question "
        "that will most efficiently obtain missing info. "
        "3️⃣ Return ONLY valid JSON with keys extracted_fields and next_question.\n\n"
        f"PRD fields: {', '.join(FIELD_NAMES)}\n"
    )
    user = (
        f"Current filled fields JSON:\n{json.dumps(answers, indent=2)}\n\n"
        f"User reply:\n{user_text}"
    )
    try:
        resp = client.chat.completions.create(
            model     = MODEL_NAME,
            temperature=0.3,
            messages=[{"role":"system","content":sys},
                      {"role":"user",  "content":user}]
        )
        content = resp.choices[0].message.content.strip()
        data    = json.loads(content)        # raises if not valid JSON
        return data.get("extracted_fields",{}), data.get("next_question")
    except RateLimitError:
        st.warning("⚠️ Rate limit hit, retrying …"); time.sleep(5); return {}, None
    except (APIError, json.JSONDecodeError) as e:
        st.error(f"OpenAI/API error: {e}"); return {}, None
    except Exception as e:
        st.error(f"Unexpected error: {e}"); return {}, None

# ── CHAT UI ────────────────────────────────────────────────────────────────────
st.title("📄 PRD Chatbot Assistant")

for role,msg in state.chat_history:
    with st.chat_message(role): st.markdown(msg)

# ── PROCESS USER INPUT ────────────────────────────────────────────────────────
user_input = st.chat_input("Type here…")

if user_input:
    state.chat_history.append(("user", user_input))

    # ① Call LLM to extract + get next question
    extracted, nxt_q = llm_extract_and_ask(user_input, state.answers)
    state.answers.update(extracted)

    # ② Store next question (if any) & reply
    if nxt_q:
        state.pending_question = nxt_q
        state.chat_history.append(("assistant", f"**{nxt_q}**"))
    else:
        state.pending_question = None
        state.chat_history.append(
            ("assistant", "🎉 Thank you! All fields are filled. "
                          "You can preview or export your PRD below.")
        )
    st.rerun()

# ── FIRST TURN (no pending question yet) ───────────────────────────────────────
if not state.chat_history and not state.pending_question:
    first_q = "Great! Let’s start – what is the **Title** of this product or feature?"
    state.pending_question = first_q
    state.chat_history.append(("assistant", f"**{first_q}**"))
    st.rerun()

# ── RENDER LAST ASSISTANT QUESTION (if page loaded after rerun) ────────────────
if state.pending_question and (not state.chat_history or state.chat_history[-1][0] != "assistant"):
    with st.chat_message("assistant"): st.markdown(f"**{state.pending_question}**")

# ── FILLED PRD + PREVIEW + EXPORT ─────────────────────────────────────────────
all_filled = len(state.answers) == len(FIELD_NAMES)

filled_prd = fill_prd_template(prd_template, state.answers)

st.divider()
st.subheader("📦 Export")
fmt = st.selectbox("Format", ["txt","md","docx","pdf"])
def export(content, fmt):
    if fmt == "txt":
        st.download_button("Download TXT", content, "PRD.txt")

    elif fmt == "md":
        st.download_button("Download Markdown", content, "PRD.md")

    elif fmt == "docx":
        doc = Document()
        for p in content.split("\n"):
            doc.add_paragraph(p)
        buf = BytesIO()
        doc.save(buf)
        st.download_button("Download DOCX", buf.getvalue(), "PRD.docx")

    elif fmt == "pdf":
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in content.split("\n"):
            pdf.multi_cell(0, 8, line)

        pdf_bytes = pdf.output(dest="S").encode("latin-1")
        st.download_button(
            "Download PDF",
            pdf_bytes,
            file_name="PRD.pdf",
            mime="application/pdf"
        )

export(filled_prd, fmt)

with st.expander("📄 Live PRD Preview", expanded=True):
    st.markdown(f"```markdown\n{filled_prd}\n```")
