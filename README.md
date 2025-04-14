# PRDChatbot

A Streamlit chatbot that helps product managers and teams fill out Product Requirement Documents (PRDs) by guiding them through structured questions or parsing uploaded PRD drafts.

---

## 🚀 Features

- 🔐 Password-protected access (env + Streamlit secrets)
- 🧠 Assistant powered by OpenAI `gpt-4o` (o3-mini)
- 📤 Upload support for `.pdf`, `.docx`, `.md`, `.txt`
- 🤖 Conversational interface (polite secretary-style)
- ✅ Retry logic, rate limits, and error logging
- 📥 Downloadable filled PRD output
- ✅ Marks incomplete sections as `TBD`

---

## 📁 Folder Structure

```
PRDChatbot/
├── app.py
├── utils.py
├── requirements.txt
├── .env.example
├── test_data.txt
└── README.md
```

---

## 🛠️ Local Setup

```bash
# 1. Clone the repo
https://github.com/your-org/PRDChatbot.git
cd PRDChatbot

# 2. Set up environment
python -m venv venv
./venv/Scripts/activate.ps1  # On Windows
pip install -r requirements.txt

# 3. Create a .env file
copy .env.example .env
# Fill in your OpenAI key and app password

# 4. Run the app
streamlit run app.py
```

---

## ☁️ Deployment on Streamlit Cloud

1. Push this repo to GitHub.
2. Go to [https://share.streamlit.io](https://share.streamlit.io)
3. Set the main file to `app.py`
4. Add the following secrets:

```ini
OPENAI_API_KEY = your_openai_key
APP_PASSWORD = your_secure_password
```

---

## 🧪 Test File
Use `test_data.txt` as an example input document when uploading.

---

## 📄 License
MIT License
