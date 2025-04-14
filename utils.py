# utils.py
import fitz  # PyMuPDF
import docx

prd_template = """
# 1. Document Overview
- **Title:** {Title}
- **Document Version and Date:** TBD
- **Author(s) and Stakeholders:** TBD
- **Approval Signatures:** TBD

# 2. Executive Summary
- **Purpose:** {Purpose}
- **Target Audience:** {Target Audience}
- **Business Objectives:** TBD

# 3. Product Description and Background
- **Problem Statement:** TBD
- **Product Vision:** TBD
- **Market and User Research:** TBD

# 4. Scope of the Product
- **In Scope:** TBD
- **Out of Scope:** TBD
- **Assumptions and Dependencies:** TBD

# 5. User Requirements
- **User Personas:** {User Personas}
- **User Stories and Use Cases:** TBD
- **User Journey / Workflows:** TBD

# 6. Functional Requirements
- **Feature Descriptions:** TBD
- **User Interface (UI) Requirements:** TBD
- **Business Rules:** TBD
- **Error Handling and Notifications:** TBD

# 7. Non-Functional Requirements
- **Performance Requirements:** TBD
- **Security Requirements:** TBD
- **Reliability and Availability:** TBD
- **Usability and Accessibility:** TBD
- **Compliance and Regulatory:** TBD

# 8. Technical and System Requirements
- **Architecture Overview:** TBD
- **Platform and Technical Environment:** TBD
- **Data Models and Schema:** TBD
- **Performance Metrics and KPIs:** TBD

# 9. Roadmap and Milestones
- **Release Plan:** TBD
- **Backlog and Future Enhancements:** TBD
- **Risk Management:** TBD

# 10. Appendix
- **Glossary:** TBD
- **References:** TBD
- **Change Log:** TBD
"""

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
        from collections import defaultdict
        import re
        field_map = defaultdict(lambda: "TBD")
        for match in re.findall(r"(?m)^([A-Za-z ]+):\s*(.+)$", answers):
            key, val = match
            field_map[key.strip()] = val.strip()
        answers = field_map
    return template.format_map(defaultdict(lambda: "TBD", answers))
