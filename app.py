import streamlit as st
import openai
from docx import Document
from datetime import date
import io

# ------------------------------------------------------------
# SETUP
# ------------------------------------------------------------
st.set_page_config(page_title="Boost Mobile BRD Generator", layout="wide")

if "openai_api_key" not in st.secrets:
    st.error("🚨 Missing OpenAI API Key. Please add it in Streamlit → Settings → Secrets.")
    st.stop()

openai.api_key = st.secrets["openai_api_key"]


# ------------------------------------------------------------
# Dynamic Table Helper
# ------------------------------------------------------------
def dynamic_table(label, columns, session_key):
    st.subheader(label)

    # Initialize session state table
    if session_key not in st.session_state:
        st.session_state[session_key] = [dict.fromkeys(columns, "")]

    rows = st.session_state[session_key]

    # Display existing rows
    for idx, row in enumerate(rows):
        st.markdown(f"**Row {idx + 1}**")
        cols_ui = st.columns(len(columns))

        for i, col_name in enumerate(columns):
            row[col_name] = cols_ui[i].text_input(
                f"{col_name} (Row {idx+1})",
                value=row[col_name],
                key=f"{session_key}_{col_name}_{idx}"
            )

        st.divider()

    # Add row button
    if st.button(f"➕ Add Row to {label}"):
        rows.append(dict.fromkeys(columns, ""))


# ------------------------------------------------------------
# Word Document Creator
# ------------------------------------------------------------
def create_brd_docx(form_inputs):
    doc = Document()

    # Header
    doc.add_heading("Business Requirements Document (Dashboard Request)", level=1)

    doc.add_paragraph(f"Project / Dashboard Name: {form_inputs['project_name']}")
    doc.add_paragraph(f"Date Created: {form_inputs['date_created']}")
    doc.add_paragraph(f"Requested By (Business Team): {form_inputs['requested_by']}")
    doc.add_paragraph(f"Prepared By (Analyst): {form_inputs['prepared_by']}")
    doc.add_paragraph(f"Version: {form_inputs['version']}")
    doc.add_paragraph("")

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
    # TABLES (Stakeholders, Data Inputs, etc.)
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

    add_table("2️⃣ Key Stakeholders",
              ["Role", "Name", "Department / Notes"],
              form_inputs["stakeholders"])

    add_table("3️⃣ Data Inputs",
              ["Source System/Table", "Description", "Frequency", "Owner"],
              form_inputs["data_inputs"])

    add_table("4️⃣ Dashboard Requirements",
              ["Dashboard Section", "Description / Purpose", "Key Metrics / Fields", "Filters Required", "Drilldown Needed?"],
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

    # 8️⃣ Notes
    doc.add_heading("8️⃣ Notes / Attachments", level=2)
    doc.add_paragraph(form_inputs["notes"])

    add_table("9️⃣ Control Data & Validation Sources",
              ["Control Report / Source", "Description / Purpose", "Business Owner", "Validation Method", "Frequency"],
              form_inputs["control_data"])

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


# ------------------------------------------------------------
# STREAMLIT UI
# ------------------------------------------------------------
st.title("📊 Boost Mobile BRD Generator")
st.markdown("Generate a BRD identical to your team's official template.")

# BASIC INFO
project_name = st.text_input("Project Name")
requested_by = st.text_input("Requested By (Business Team)")
prepared_by = st.text_input("Prepared By (Analyst)")
version = st.text_input("Version", value="1.0")
date_created = st.date_input("Date Created", value=date.today())

# 1️⃣ Business Overview
st.subheader("1️⃣ Business Overview")
business_problem = st.text_area("Business Problem")
business_goal = st.text_area("Business Goal")
in_scope = st.text_area("In Scope")
out_of_scope = st.text_area("Out of Scope")
frequency = st.selectbox("Expected Frequency", ["Daily", "Weekly", "Monthly", "Ad hoc"])

# ------------------------------------------------------------
# Dynamic Tables
# ------------------------------------------------------------
dynamic_table("2️⃣ Key Stakeholders",
              ["Role", "Name", "Department / Notes"],
              "stakeholders")

dynamic_table("3️⃣ Data Inputs",
              ["Source System/Table", "Description", "Frequency", "Owner"],
              "data_inputs")

dynamic_table("4️⃣ Dashboard Requirements",
              ["Dashboard Section", "Description / Purpose", "Key Metrics / Fields", "Filters Required", "Drilldown Needed?"],
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

dynamic_table("9️⃣ Control Data & Validation Sources",
              ["Control Report / Source", "Description / Purpose", "Business Owner", "Validation Method", "Frequency"],
              "control_data")

notes = st.text_area("8️⃣ Notes / Attachments")

# ------------------------------------------------------------
# Generate BRD Button
# ------------------------------------------------------------
if st.button("Generate BRD (.docx)"):
    with st.spinner("Creating BRD Document…"):
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
        }

        buffer = create_brd_docx(form_inputs)

        st.success("🎉 BRD Created Successfully!")
        st.download_button(
            label="📥 Download BRD Document",
            data=buffer,
            file_name="BRD.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        # Auto-reset form
        st.session_state.clear()
        st.experimental_rerun()
