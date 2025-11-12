import streamlit as st
import openai
from docx import Document
from datetime import date
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders


# ------------------------------------------------------------
# SETUP
# ------------------------------------------------------------
st.set_page_config(page_title="Boost Mobile BRD Generator", layout="wide")

# Validate OpenAI key
if "openai_api_key" not in st.secrets:
    st.error("🚨 Missing OpenAI API Key. Add it in Streamlit → Settings → Secrets.")
    st.stop()

openai.api_key = st.secrets["openai_api_key"]


# ------------------------------------------------------------
# SMTP EMAIL SENDER
# ------------------------------------------------------------
def send_email(subject, body, attachments):
    smtp_server = st.secrets["smtp_server"]
    smtp_port = int(st.secrets["smtp_port"])
    sender_email = st.secrets["sender_email"]
    sender_password = st.secrets["sender_password"]
    receiver_email = st.secrets["receiver_email"]

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    # Add attachments
    for file in attachments:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(file["data"])
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {file['filename']}",
        )
        msg.attach(part)

    # Send email
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(sender_email, sender_password)
    server.sendmail(sender_email, receiver_email, msg.as_string())
    server.quit()


# ------------------------------------------------------------
# Dynamic Row Table Builder
# ------------------------------------------------------------
def dynamic_table(label, columns, session_key):
    st.subheader(label)

    if session_key not in st.session_state:
        st.session_state[session_key] = [dict.fromkeys(columns, "")]

    rows = st.session_state[session_key]

    for idx, row in enumerate(rows):
        st.markdown(f"**Entry {idx + 1}**")
        cols_ui = st.columns(len(columns))

        for i, col_name in enumerate(columns):
            row[col_name] = cols_ui[i].text_input(
                f"{col_name}",
                value=row[col_name],
                key=f"{session_key}_{col_name}_{idx}"
            )

        st.divider()

    if st.button(f"➕ Add Row to {label}"):
        rows.append(dict.fromkeys(columns, ""))


# ------------------------------------------------------------
# Create Word BRD Document
# ------------------------------------------------------------
def create_brd_docx(form_inputs):
    doc = Document()

    doc.add_heading("Business Requirements Document (Dashboard Request)", level=1)

    doc.add_paragraph(f"Project / Dashboard Name: {form_inputs['project_name']}")
    doc.add_paragraph(f"Date Created: {form_inputs['date_created']}")
    doc.add_paragraph(f"Requested By (Business Team): {form_inputs['requested_by']}")
    doc.add_paragraph(f"Prepared By (Analyst): {form_inputs['prepared_by']}")
    doc.add_paragraph(f"Version: {form_inputs['version']}\n")

    # 1️⃣ Business Overview
    doc.add_heading("1️⃣ Business Overview", level=2)
    doc.add_paragraph("Business Problem / Need:")
    doc.add_paragraph(form_inputs["business_problem"])

    doc.add_paragraph("\nBusiness Goal / Outcome:")
    doc.add_paragraph(form_inputs["business_goal"])

    doc.add_paragraph("\nScope (In-Scope):")
    doc.add_paragraph(form_inputs["in_scope"])

    doc.add_paragraph("\nOut of Scope:")
    doc.add_paragraph(form_inputs["out_of_scope"])

    doc.add_paragraph("\nExpected Frequency:")
    doc.add_paragraph(form_inputs["frequency"])

    # ------------------------------------------------------------
    # Helper to add tables
    # ------------------------------------------------------------
    def add_table(title, columns, rows):
        doc.add_heading(title, level=2)
        table = doc.add_table(rows=1, cols=len(columns))
        hdr = table.rows[0].cells
        for i, col in enumerate(columns):
            hdr[i].text = col

        for row in rows:
            cells = table.add_row().cells
            for i, col in enumerate(columns):
                cells[i].text = row[col] if row[col] else ""

    # 2-7 tables
    add_table("2️⃣ Key Stakeholders",
              ["Role", "Name", "Department / Notes"],
              form_inputs["stakeholders"])

    add_table("3️⃣ Data Inputs",
              ["Source System/Table", "Description", "Frequency", "Owner"],
              form_inputs["data_inputs"])

    add_table("4️⃣ Dashboard Requirements",
              ["Dashboard Section", "Description / Purpose", "Key Metrics / Fields",
               "Filters Required", "Drilldown Needed?"],
              form_inputs["dash_reqs"])

    add_table("5️⃣ Business Rules / Calculations",
              ["Metric", "Definition / Formula", "Notes"],
              form_inputs["business_rules"])

    add_table("6️⃣ Expected Outputs",
              ["Deliverable", "Format / Platform", "Frequency", "Audience"],
              form_inputs["expected_outputs"])

    add_table("7️⃣ Validation & Sign-off",
              ["Step", "Responsible", "Criteria", "Status"],
              form_inputs["validation"])

    # 8️⃣ Notes & Attachments
    doc.add_heading("8️⃣ Notes & Attachments", level=2)
    doc.add_paragraph(form_inputs["notes"])

    # Add images inline if any
    for file in form_inputs["attachments"]:
        if file.type.startswith("image/"):
            doc.add_picture(file, width=None)

    # 9️⃣ Control Data
    add_table("9️⃣ Control Data & Validation Sources",
              ["Control Report / Source", "Description / Purpose",
               "Business Owner", "Validation Method", "Frequency"],
              form_inputs["control_data"])

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer



# ------------------------------------------------------------
# STREAMLIT UI
# ------------------------------------------------------------
st.title("📊 Boost Mobile BRD Generator")

# BASIC INFO
project_name = st.text_input("Project Name")
requested_by = st.text_input("Requested By (Business Team)")
prepared_by = st.text_input("Prepared By (Analyst)")
version = st.text_input("Version", "1.0")
date_created = st.date_input("Date Created", date.today())

# 1️⃣ Business Overview
st.subheader("1️⃣ Business Overview")
business_problem = st.text_area("Business Problem")
business_goal = st.text_area("Business Goal")
in_scope = st.text_area("In Scope")
out_of_scope = st.text_area("Out of Scope")
frequency = st.selectbox("Expected Frequency", ["Daily", "Weekly", "Monthly", "Ad hoc"])

# Tables
dynamic_table("2️⃣ Key Stakeholders",
              ["Role", "Name", "Department / Notes"],
              "stakeholders")

dynamic_table("3️⃣ Data Inputs",
              ["Source System/Table", "Description", "Frequency", "Owner"],
              "data_inputs")

dynamic_table("4️⃣ Dashboard Requirements",
              ["Dashboard Section", "Description / Purpose",
               "Key Metrics / Fields", "Filters Required", "Drilldown Needed?"],
              "dash_reqs")

dynamic_table("5️⃣ Business Rules / Calculations",
              ["Metric", "Definition / Formula", "Notes"],
              "business_rules")

dynamic_table("6️⃣ Expected Outputs",
              ["Deliverable", "Format / Platform", "Frequency", "Audience"],
              "expected_outputs")

dynamic_table("7️⃣ Validation & Sign-off",
              ["Step", "Responsible", "Criteria", "Status"],
              "validation")

# 8️⃣ Notes & Attachments
st.subheader("8️⃣ Notes & Attachments")
notes = st.text_area("Notes")
attachments = st.file_uploader(
    "Upload attachments (any file type)",
    accept_multiple_files=True,
    type=None
)

# 9️⃣ Control Data
dynamic_table("9️⃣ Control Data & Validation Sources",
              ["Control Report / Source", "Description / Purpose",
               "Business Owner", "Validation Method", "Frequency"],
              "control_data")


# ------------------------------------------------------------
# Submit → Generate BRD & Email It
# ------------------------------------------------------------
if st.button("📤 Submit & Email BRD"):
    with st.spinner("Generating BRD and sending email…"):
        
        # Create clean filename
        safe_project_name = project_name.replace(" ", "_").replace("/", "_")
        brd_filename = f"{safe_project_name}_BRD.docx"
        
        form_inputs = {
            "project_name": project_name,
            "requested_by": requested_by,
            "prepared_by": prepared_by,
            "version": version,
            "date_created": date_created,
            "business_problem": business_problem,
            "business_goal": business_goal,
            "in_scope": in_scope,
            "out_of_scope": out_of_scope,
            "frequency": frequency,
            "stakeholders": st.session_state["stakeholders"],
            "data_inputs": st.session_state["data_inputs"],
            "dash_reqs": st.session_state["dash_reqs"],
            "business_rules": st.session_state["business_rules"],
            "expected_outputs": st.session_state["expected_outputs"],
            "validation": st.session_state["validation"],
            "control_data": st.session_state["control_data"],
            "notes": notes,
            "attachments": attachments or [],
        }

        # Generate BRD Docx
        brd_docx = create_brd_docx(form_inputs)

        # Build attachments array for email
        email_attachments = [
            {"filename": brd_filename, "data": brd_docx.getvalue()}
        ]

        # Include user-uploaded files
        for f in attachments or []:
            email_attachments.append({"filename": f.name, "data": f.getvalue()})

        # Send email
        send_email(
            subject=f"New BRD Submission: {project_name}",
            body=f"A new BRD has been submitted.\n\nProject: {project_name}",
            attachments=email_attachments
        )

        # SUCCESS MESSAGE FOR THE USER
        st.success("✅ BRD Submitted – Reach out to himanshu.jadaun@dish.com for any questions")

        # Reset everything
        st.session_state.clear()
        st.rerun()
