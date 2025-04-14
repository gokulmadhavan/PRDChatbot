# utils.py
import fitz  # PyMuPDF
import docx
from collections import defaultdict
import re


prd_template = """
# 1. Document Overview
- **Title:** {Title}
- **Document Version and Date:** {Document Version and Date}
- **Author(s) and Stakeholders:** {Author(s) and Stakeholders}
- **Approval Signatures:** {Approval Signatures}

# 2. Executive Summary
- **Purpose:** {Purpose}
- **Target Audience:** {Target Audience}
- **Business Objectives:** {Business Objectives}

# 3. Product Description and Background
- **Problem Statement:** {Problem Statement}
- **Product Vision:** {Product Vision}
- **Market and User Research:** {Market and User Research}

# 4. Scope of the Product
- **In Scope:** {In Scope}
- **Out of Scope:** {Out of Scope}
- **Assumptions and Dependencies:** {Assumptions and Dependencies}

# 5. User Requirements
- **User Personas:** {User Personas}
- **User Stories and Use Cases:** {User Stories and Use Cases}
- **User Journey / Workflows:** {User Journey / Workflows}

# 6. Functional Requirements
- **Feature Descriptions:** {Feature Descriptions}
- **User Interface (UI) Requirements:** {User Interface (UI) Requirements}
- **Business Rules:** {Business Rules}
- **Error Handling and Notifications:** {Error Handling and Notifications}

# 7. Non-Functional Requirements
- **Performance Requirements:** {Performance Requirements}
- **Security Requirements:** {Security Requirements}
- **Reliability and Availability:** {Reliability and Availability}
- **Usability and Accessibility:** {Usability and Accessibility}
- **Compliance and Regulatory:** {Compliance and Regulatory}

# 8. Technical and System Requirements
- **Architecture Overview:** {Architecture Overview}
- **Platform and Technical Environment:** {Platform and Technical Environment}
- **Data Models and Schema:** {Data Models and Schema}
- **Performance Metrics and KPIs:** {Performance Metrics and KPIs}

# 9. Roadmap and Milestones
- **Release Plan:** {Release Plan}
- **Backlog and Future Enhancements:** {Backlog and Future Enhancements}
- **Risk Management:** {Risk Management}

# 10. Appendix
- **Glossary:** {Glossary}
- **References:** {References}
- **Change Log:** {Change Log}
"""

prd_fields_and_questions = [
    ("Title", "What is the title of the product or feature?"),
    ("Document Version and Date", "What is the current version and update date for this document?"),
    ("Author(s) and Stakeholders", "Who are the main authors and stakeholders involved?"),
    ("Approval Signatures", "Are there any required approval signatures?"),

    ("Purpose", "Why does this product or feature exist? What is its purpose?"),
    ("Target Audience", "Who is the primary audience or user group for this?"),
    ("Business Objectives", "What business objectives or goals does this support?"),

    ("Problem Statement", "What core problems or pain points does this product address?"),
    ("Product Vision", "What is the long-term vision for this product or feature?"),
    ("Market and User Research", "Have you conducted any market or user research? What did you find?"),

    ("In Scope", "What features or areas are in scope for this release?"),
    ("Out of Scope", "What is explicitly out of scope for this version?"),
    ("Assumptions and Dependencies", "Are there any assumptions or dependencies that impact delivery?"),

    ("User Personas", "Who are the key user personas?"),
    ("User Stories and Use Cases", "Can you provide any key user stories or use cases?"),
    ("User Journey / Workflows", "Can you describe the user journey or expected workflows?"),

    ("Feature Descriptions", "Please describe the key features of the product."),
    ("User Interface (UI) Requirements", "What UI requirements or interactions should be supported?"),
    ("Business Rules", "Are there any business rules or logic to document?"),
    ("Error Handling and Notifications", "How should the system handle errors and notify users?"),

    ("Performance Requirements", "What performance expectations exist (e.g., load time)?"),
    ("Security Requirements", "What security or compliance needs must be met?"),
    ("Reliability and Availability", "What are the reliability and availability expectations?"),
    ("Usability and Accessibility", "What usability or accessibility standards must be met?"),
    ("Compliance and Regulatory", "What regulatory or compliance guidelines apply?"),

    ("Architecture Overview", "What does the high-level system architecture look like?"),
    ("Platform and Technical Environment", "What platforms or technologies are in use?"),
    ("Data Models and Schema", "Can you describe the data model or schema?"),
    ("Performance Metrics and KPIs", "What performance metrics or KPIs will be tracked?"),

    ("Release Plan", "What is the release plan or timeline for this product?"),
    ("Backlog and Future Enhancements", "What’s in the backlog or being considered for the future?"),
    ("Risk Management", "What risks have been identified and how will they be mitigated?"),

    ("Glossary", "Would you like to define any specific terms used throughout this document?"),
    ("References", "Do you want to include any references, research, or notes?"),
    ("Change Log", "Would you like to maintain a change log for this document?")
]

def parse_prd_file(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        return _parse_pdf(uploaded_file)
    elif name.endswith(".docx"):
        return _parse_docx(uploaded_file)
    elif name.endswith(".md") or name.endswith(".txt"):
        return uploaded_file.read().decode("utf-8")
    else:
        raise ValueError("Unsupported file format")

def _parse_pdf(file):
    text = ""
    with fitz.open(stream=file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def _parse_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def fill_prd_template(template, answers):
    # answers can be either a dict or a string with field: value
    if isinstance(answers, str):
        field_map = defaultdict(lambda: "TBD")
        for match in re.findall(r"(?m)^([A-Za-z ()]+):\s*(.+)$", answers):
            key, val = match
            field_map[key.strip()] = val.strip()
        answers = field_map
    return template.format_map(defaultdict(lambda: "TBD", answers))
