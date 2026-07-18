"""
🏥 Hospital AI Agent — Main Streamlit App
Multi-page application with:
  • Data Scraper
  • Hospital & Doctor Search
  • Appointment Booking
  • AI Chat Assistant
  • Lead Scoring Dashboard
  • Analytics
"""

import sys
import os
from datetime import date, timedelta
import pandas as pd
import streamlit as st

# ─────────────────────────────────────────────
# FIX MODULE PATH — points to project root
# ─────────────────────────────────────────────
# Get the directory where this script is located
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Add the project directory to sys.path so we can import modules
PROJECT_ROOT = CURRENT_DIR
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ─────────────────────────────────────────────
# LOAD ENVIRONMENT VARIABLES
# ─────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# ─────────────────────────────────────────────
# IMPORT PROJECT MODULES
# ─────────────────────────────────────────────
try:
    from utils import data_loader, llm_client
    from agents.hospital_agents import (
        HospitalRetrieverAgent,
        DoctorFinderAgent,
        BookingAgent,
        LeadScorerAgent,
        QAAgent
    )
    from Scrapers.hospital_scraper import run_scraper
except ImportError as e:
    st.error(f"""
    ❌ **Import Error**
    
    Could not import required modules. Please check:
    1. You are running this from the correct directory
    2. All modules exist in the project structure
    
    **Error details:** {str(e)}
    
    **Current directory:** {os.getcwd()}
    **Project root:** {PROJECT_ROOT}
    **sys.path:** {sys.path}
    """)
    st.stop()

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="🏥 Hospital AI Agent",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
  .main-header {
    background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%);
    color: white; padding: 20px 24px; border-radius: 12px;
    margin-bottom: 24px;
  }
  .main-header h1 { margin: 0; font-size: 2rem; }
  .main-header p  { margin: 4px 0 0; opacity: .85; font-size: .95rem; }
  .metric-card {
    background: #f8faff; border: 1px solid #dbe8ff;
    border-radius: 10px; padding: 16px; text-align: center;
  }
  .metric-card h2 { color: #1a73e8; margin: 0; font-size: 2rem; }
  .metric-card p  { color: #555; margin: 4px 0 0; font-size: .85rem; }
  .doc-card {
    background: white; border: 1px solid #e0e0e0;
    border-radius: 10px; padding: 16px; margin-bottom: 12px;
    border-left: 4px solid #1a73e8;
  }
  .appt-card {
    background: #e8f5e9; border: 1px solid #a5d6a7;
    border-radius: 10px; padding: 16px; margin-bottom: 12px;
  }
  .badge-high   { background:#ffebee; color:#c62828; padding:2px 10px; border-radius:20px; font-size:.8rem; }
  .badge-medium { background:#fff8e1; color:#f57f17; padding:2px 10px; border-radius:20px; font-size:.8rem; }
  .badge-low    { background:#e8f5e9; color:#2e7d32; padding:2px 10px; border-radius:20px; font-size:.8rem; }
  .stButton>button { border-radius: 8px; font-weight: 500; }
  .st-emotion-cache-16idsys p { font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE INITIALIZATION
# ─────────────────────────────────────────────
if "booking_agent" not in st.session_state:
    st.session_state.booking_agent = BookingAgent()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "selected_doctor" not in st.session_state:
    st.session_state.selected_doctor = None
if "selected_hospital" not in st.session_state:
    st.session_state.selected_hospital = None
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False
if "page" not in st.session_state:
    st.session_state.page = "🏠 Dashboard"

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏥 Hospital AI Agent")
    st.markdown("---")

    # API Key
    api_key = st.text_input(
        "🔑 OpenRouter API Key",
        type="password",
        value=os.getenv("OPENROUTER_API_KEY", ""),
        help="Get your key at openrouter.ai"
    )
    if api_key:
        os.environ["OPENROUTER_API_KEY"] = api_key

    # Model selection
    try:
        available_models = llm_client.available_models()
    except Exception:
        available_models = ["mistralai/mistral-7b-instruct"]
    
    model = st.selectbox(
        "🤖 LLM Model",
        available_models,
        index=0
    )
    os.environ["OPENROUTER_MODEL"] = model

    st.markdown("---")
    
    # Navigation
    page = st.radio(
        "📌 Navigation",
        [
            "🏠 Dashboard",
            "🔍 Scrape Data",
            "🏨 Find Hospital",
            "👨‍⚕️ Find Doctor",
            "📅 Book Appointment",
            "💬 AI Chat",
            "📊 Lead Scoring",
            "📈 Analytics",
        ],
        index=0
    )
    st.session_state.page = page
    
    st.markdown("---")

    # Data status
    try:
        summary = data_loader.summary()
        if any(v > 0 for v in summary.values()):
            st.success("✅ Data loaded")
            for k, v in summary.items():
                if v > 0:
                    st.caption(f"  • {k}: {v:,}")
        else:
            st.warning("⚠️ No data yet — run Scrape Data")
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")

# ─────────────────────────────────────────────
# PAGE ROUTING
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# PAGE: DASHBOARD
# ─────────────────────────────────────────────
if page == "🏠 Dashboard":
    st.markdown("""
    <div class="main-header">
      <h1>🏥 Hospital AI Agent</h1>
      <p>Agentic AI for hospital discovery, doctor matching & appointment automation · Bengaluru</p>
    </div>
    """, unsafe_allow_html=True)

    try:
        s = data_loader.summary()
        cols = st.columns(4)
        metrics = [
            ("🏨", "Hospitals", s.get("hospitals", 0)),
            ("🏬", "Departments", s.get("departments", 0)),
            ("👨‍⚕️", "Doctors", s.get("doctors", 0)),
            ("🩺", "Services", s.get("services", 0)),
        ]
        for col, (icon, label, val) in zip(cols, metrics):
            with col:
                st.markdown(f"""
                <div class="metric-card">
                  <h2>{icon} {val:,}</h2><p>{label}</p>
                </div>""", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Unable to load metrics: {str(e)}")

    st.markdown("### 🤖 Agent Pipeline")
    agents_info = [
        ("🔎 Retrieval Agent", "Searches hospitals by location, specialty & rating using LLM ranking"),
        ("👨‍⚕️ Doctor Finder Agent", "Matches patient symptoms/needs to the best available doctor"),
        ("📅 Booking Agent", "Automates the full appointment workflow with LLM-generated confirmations"),
        ("📊 Lead Scorer Agent", "Scores inbound patient leads and recommends follow-up actions"),
        ("💬 QA Agent", "Answers any hospital/health queries grounded in real CSV data (RAG-lite)"),
    ]
    for title, desc in agents_info:
        with st.expander(title):
            st.write(desc)

    st.markdown("### 🚀 Quick Start")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("**Step 1** → Run 🔍 Scrape Data to populate the hospital database")
    with c2:
        st.info("**Step 2** → Add your OpenRouter API key in the sidebar")
    with c3:
        st.info("**Step 3** → Use 📅 Book Appointment or 💬 AI Chat")


# ─────────────────────────────────────────────
# PAGE: SCRAPE DATA
# ─────────────────────────────────────────────
elif page == "🔍 Scrape Data":
    st.header("🔍 Hospital Data Scraper")
    st.markdown("""
    Scrapes live hospital data from public sources (Practo, NHA, etc.) and falls back
    to realistic synthetic data. Produces 9 structured CSV files used to train the agents.
    """)

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("#### CSVs that will be generated:")
        try:
            for t in data_loader.TABLES:
                st.markdown(f"  - `data/{t}.csv`")
        except Exception:
            st.markdown("  - `data/hospitals.csv`")
            st.markdown("  - `data/doctors.csv`")
            st.markdown("  - `data/services.csv`")

    with col2:
        st.markdown("#### Current status:")
        try:
            s = data_loader.summary()
            for k, v in s.items():
                icon = "✅" if v > 0 else "❌"
                st.caption(f"{icon} {k}: {v} rows")
        except Exception:
            st.caption("❌ No data loaded")

    st.markdown("---")
    if st.button("▶️ Run Scraper Now", type="primary", width="stretch"):
        with st.spinner("Scraping & generating hospital data …"):
            progress = st.progress(0)
            log_area = st.empty()
            logs = []

            try:
                import io
                import contextlib
                
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    dfs = run_scraper()
                logs = buf.getvalue().split("\n")
                progress.progress(100)

                log_area.code("\n".join(logs) if logs else "Scraper completed successfully!")
                data_loader.load_all()
                st.success(f"✅ Done! Generated {sum(len(v) for v in dfs.values()):,} records across {len(dfs)} tables.")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"❌ Scraper failed: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

    # Preview tabs
    try:
        s = data_loader.summary()
        if any(v > 0 for v in s.values()):
            st.markdown("---")
            st.subheader("📋 Data Preview")
            tab_names = [t for t in data_loader.TABLES if not data_loader.get(t).empty]
            if tab_names:
                tabs = st.tabs(tab_names)
                for tab, tname in zip(tabs, tab_names):
                    with tab:
                        df = data_loader.get(tname)
                        st.dataframe(df.head(20), width="stretch")
                        st.caption(f"{len(df):,} rows × {len(df.columns)} columns")
    except Exception as e:
        st.caption(f"No data to preview: {str(e)}")


# ─────────────────────────────────────────────
# PAGE: FIND HOSPITAL
# ─────────────────────────────────────────────
elif page == "🏨 Find Hospital":
    st.header("🏨 Find a Hospital")
    
    try:
        agent = HospitalRetrieverAgent()
    except Exception as e:
        st.error(f"Failed to initialize HospitalRetrieverAgent: {str(e)}")
        agent = None

    with st.form("hosp_search"):
        query = st.text_input(
            "🔍 What are you looking for?",
            placeholder="e.g. best cardiology hospital near Whitefield"
        )
        c1, c2 = st.columns(2)
        with c1:
            min_rating = st.slider("Minimum Rating", 3.0, 5.0, 4.0, 0.1)
        with c2:
            hosp_type = st.selectbox("Hospital Type", ["Any", "Multi-Specialty", "Super-Specialty", "General", "Maternity"])
        submitted = st.form_submit_button("🔍 Search", type="primary", width="stretch")

    if submitted and query:
        if agent is None:
            st.error("Agent not initialized. Please check your setup.")
        else:
            with st.spinner("Finding best hospitals with AI …"):
                try:
                    filters = {"min_rating": min_rating, "hospital_type": hosp_type}
                    results = agent.retrieve(query, filters)

                    if results:
                        st.success(f"Found {len(results)} hospitals")
                        for h in results:
                            with st.expander(f"🏨 {h.get('name', 'Unknown')}  ⭐ {h.get('rating', 'N/A')}", expanded=True):
                                c1, c2, c3 = st.columns(3)
                                with c1:
                                    st.markdown(f"**📍** {h.get('address', '')}, {h.get('city', '')}")
                                    st.markdown(f"**📞** {h.get('phone', '')}")
                                    st.markdown(f"**📧** {h.get('email', '')}")
                                with c2:
                                    st.markdown(f"**Type:** {h.get('type', '')}")
                                    st.markdown(f"**Beds:** {h.get('beds', '')}")
                                    st.markdown(f"**Est.:** {h.get('established', '')}")
                                with c3:
                                    st.markdown(f"**Accreditation:** {h.get('accreditation', '')}")
                                    st.markdown(f"**Rating:** {h.get('rating', '')} ⭐ ({h.get('reviews_count', '')} reviews)")

                                if st.button(f"Select this hospital", key=f"sel_{h.get('hospital_id', 'unknown')}"):
                                    st.session_state.selected_hospital = h
                                    st.success(f"✅ Selected {h.get('name', '')}. Go to Find Doctor or Book Appointment.")
                    else:
                        st.warning("No results found. Try a different query or run the scraper first.")
                except Exception as e:
                    st.error(f"Search failed: {str(e)}")


# ─────────────────────────────────────────────
# PAGE: FIND DOCTOR
# ─────────────────────────────────────────────
elif page == "👨‍⚕️ Find Doctor":
    st.header("👨‍⚕️ Find a Doctor")
    
    try:
        finder = DoctorFinderAgent()
    except Exception as e:
        st.error(f"Failed to initialize DoctorFinderAgent: {str(e)}")
        finder = None

    with st.form("doc_search"):
        query = st.text_input(
            "🩺 Describe your symptoms or the specialist you need",
            placeholder="e.g. chest pain, I need a cardiologist"
        )
        c1, c2 = st.columns(2)
        with c1:
            dept_filter = st.selectbox("Department (optional)", [
                "Any", "Cardiology", "Neurology", "Orthopedics", "Oncology",
                "Gynecology", "Pediatrics", "Dermatology", "Psychiatry",
                "Gastroenterology", "Urology", "Ophthalmology", "ENT", "Pulmonology",
            ])
        with c2:
            hosp_id = None
            if st.session_state.selected_hospital:
                st.info(f"🏨 Searching in: {st.session_state.selected_hospital.get('name', '')}")
                hosp_id = [st.session_state.selected_hospital.get("hospital_id")]
            else:
                st.caption("No hospital selected — searching all hospitals")
        submitted = st.form_submit_button("🔍 Find Doctor", type="primary", width="stretch")

    if submitted and query:
        if finder is None:
            st.error("Finder not initialized. Please check your setup.")
        else:
            with st.spinner("Matching you with the best doctors …"):
                try:
                    results = finder.find(query, hospital_ids=hosp_id, dept_filter=dept_filter)

                    if results:
                        st.success(f"Found {len(results)} doctors")
                        for doc in results:
                            with st.expander(f"👨‍⚕️ {doc.get('name', 'Unknown')} — {doc.get('specialization', '')}", expanded=True):
                                c1, c2, c3 = st.columns(3)
                                with c1:
                                    st.markdown(f"**Dept:** {doc.get('department_name', '')}")
                                    st.markdown(f"**Qualification:** {doc.get('qualification', '')}")
                                    st.markdown(f"**Experience:** {doc.get('experience_years', '')} years")
                                with c2:
                                    st.markdown(f"**Fee:** ₹{doc.get('consultation_fee', '')}")
                                    st.markdown(f"**Languages:** {doc.get('languages', '')}")
                                    st.markdown(f"**Available:** {doc.get('available_days', '')}")
                                with c3:
                                    st.markdown(f"**Rating:** {doc.get('rating', '')} ⭐")
                                    status = "🟢 Available" if doc.get("is_available") else "🔴 Unavailable"
                                    st.markdown(f"**Status:** {status}")

                                if doc.get("is_available") and st.button(f"📅 Book with {doc.get('name', '')}", key=f"book_{doc.get('doctor_id', 'unknown')}"):
                                    st.session_state.selected_doctor = doc
                                    st.success(f"✅ Selected {doc.get('name', '')}. Go to Book Appointment.")
                    else:
                        st.warning("No doctors found. Try adjusting your query or run the scraper.")
                except Exception as e:
                    st.error(f"Search failed: {str(e)}")


# ─────────────────────────────────────────────
# PAGE: BOOK APPOINTMENT
# ─────────────────────────────────────────────
elif page == "📅 Book Appointment":
    st.header("📅 Book an Appointment")
    
    try:
        booking_agent = st.session_state.booking_agent
    except Exception as e:
        st.error(f"Failed to initialize BookingAgent: {str(e)}")
        booking_agent = None

    # Show existing appointments
    if booking_agent:
        try:
            existing = booking_agent.list_appointments()
            if existing:
                with st.expander(f"📋 My Appointments ({len(existing)})", expanded=False):
                    for appt in reversed(existing):
                        colour = "#e8f5e9" if appt.get("status") == "Confirmed" else "#ffebee"
                        st.markdown(f"""
                        <div style="background:{colour};border-radius:8px;padding:12px;margin-bottom:8px;">
                          <strong>🎫 {appt.get('booking_ref', '')}</strong> &nbsp;|&nbsp; {appt.get('status', '')}<br>
                          <strong>{appt.get('doctor_name', '')}</strong> @ {appt.get('hospital_name', '')}<br>
                          🗓️ {appt.get('appointment_date', '')} &nbsp; ⏰ {appt.get('appointment_time', '')}<br>
                          👤 {appt.get('patient_name', '')}
                        </div>""", unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"Could not load appointments: {str(e)}")

    st.markdown("---")
    st.subheader("New Appointment")

    # Pre-fill from session
    pre_doc = st.session_state.selected_doctor
    pre_hosp = st.session_state.selected_hospital

    with st.form("booking_form"):
        st.markdown("#### 👤 Patient Details")
        c1, c2 = st.columns(2)
        with c1:
            patient_name = st.text_input("Full Name *")
            patient_phone = st.text_input("Phone *", placeholder="+91-XXXXXXXXXX")
        with c2:
            patient_email = st.text_input("Email")
            patient_age = st.number_input("Age", 1, 110, 30)

        patient_gender = st.selectbox("Gender", ["Male", "Female", "Other"])

        st.markdown("#### 🏥 Appointment Details")
        # Hospital selector
        try:
            hosp_df = data_loader.get("hospitals")
            if not hosp_df.empty:
                hosp_options = hosp_df["name"].tolist()
                default_hosp = 0
                if pre_hosp and pre_hosp.get("name") in hosp_options:
                    default_hosp = hosp_options.index(pre_hosp["name"])
                selected_hosp_name = st.selectbox("🏨 Hospital", hosp_options, index=default_hosp)
            else:
                selected_hosp_name = st.text_input("🏨 Hospital", value=pre_hosp.get("name", "") if pre_hosp else "")
        except Exception:
            selected_hosp_name = st.text_input("🏨 Hospital", value=pre_hosp.get("name", "") if pre_hosp else "")

        # Department & Doctor
        try:
            dept_df = data_loader.get("departments")
            hosp_df = data_loader.get("hospitals")
            selected_hosp_row = hosp_df[hosp_df["name"] == selected_hosp_name] if not hosp_df.empty else pd.DataFrame()
            hosp_id_sel = selected_hosp_row.iloc[0]["hospital_id"] if not selected_hosp_row.empty else None

            dept_options = ["Any"]
            if not dept_df.empty and hosp_id_sel:
                dept_options += dept_df[dept_df["hospital_id"] == hosp_id_sel]["department_name"].unique().tolist()
            department = st.selectbox("🏬 Department", dept_options)

            doc_df = data_loader.get("doctors")
            doc_filter = doc_df.copy() if not doc_df.empty else pd.DataFrame()
            if not doc_filter.empty and hosp_id_sel:
                doc_filter = doc_filter[doc_filter["hospital_id"] == hosp_id_sel]
            if not doc_filter.empty and department != "Any":
                doc_filter = doc_filter[doc_filter["department_name"] == department]

            doc_options = doc_filter["name"].tolist() if not doc_filter.empty else ["No doctors found"]
            default_doc = 0
            if pre_doc and pre_doc.get("name") in doc_options:
                default_doc = doc_options.index(pre_doc["name"])
            selected_doc_name = st.selectbox("👨‍⚕️ Doctor", doc_options, index=min(default_doc, len(doc_options)-1))
        except Exception:
            selected_doc_name = st.text_input("👨‍⚕️ Doctor", value=pre_doc.get("name", "") if pre_doc else "")

        c1, c2 = st.columns(2)
        with c1:
            appt_date = st.date_input("📅 Date", min_value=date.today(), value=date.today() + timedelta(days=1))
        with c2:
            appt_time = st.selectbox("⏰ Time Slot", ["9:00 AM", "10:00 AM", "11:00 AM", "12:00 PM", "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM"])

        reason = st.text_area("📝 Reason for Visit", placeholder="Briefly describe your symptoms or purpose of visit …")
        insurance = st.text_input("🛡️ Insurance Provider (optional)")

        submitted = st.form_submit_button("📅 Confirm Booking", type="primary", width="stretch")

    if submitted:
        if not patient_name or not patient_phone:
            st.error("Please fill in Name and Phone.")
        elif booking_agent is None:
            st.error("Booking agent not initialized. Please check your setup.")
        else:
            with st.spinner("Booking your appointment …"):
                try:
                    # Get selected doctor details
                    doc_row = doc_filter[doc_filter["name"] == selected_doc_name] if 'doc_filter' in locals() and not doc_filter.empty else pd.DataFrame()
                    fee = int(doc_row.iloc[0]["consultation_fee"]) if not doc_row.empty else 500

                    booking_data = {
                        "patient_name": patient_name,
                        "patient_phone": patient_phone,
                        "patient_email": patient_email,
                        "patient_age": patient_age,
                        "patient_gender": patient_gender,
                        "hospital_name": selected_hosp_name,
                        "department": department if 'department' in locals() else "",
                        "doctor_name": selected_doc_name,
                        "appointment_date": str(appt_date),
                        "appointment_time": appt_time,
                        "reason": reason,
                        "insurance": insurance,
                        "consultation_fee": fee,
                    }
                    result = booking_agent.book(booking_data)

                    st.balloons()
                    st.markdown(f"""
                    <div class="appt-card">
                      <h3>✅ Appointment Confirmed!</h3>
                      <p><strong>Booking Reference:</strong> {result.get('booking_ref', '')}</p>
                      <p><strong>Doctor:</strong> {result.get('doctor_name', '')}</p>
                      <p><strong>Hospital:</strong> {result.get('hospital_name', '')}</p>
                      <p><strong>Date & Time:</strong> {result.get('appointment_date', '')} at {result.get('appointment_time', '')}</p>
                      <p><strong>Fee:</strong> ₹{result.get('consultation_fee', '')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("#### 💬 Confirmation Message from AI")
                    st.info(result.get("confirmation_message", "Your appointment has been booked successfully."))
                except Exception as e:
                    st.error(f"Booking failed: {str(e)}")


# ─────────────────────────────────────────────
# PAGE: AI CHAT
# ─────────────────────────────────────────────
elif page == "💬 AI Chat":
    st.header("💬 Hospital AI Assistant")
    st.caption("Ask anything about hospitals, doctors, services, costs, or booking.")

    try:
        qa_agent = QAAgent()
    except Exception as e:
        st.error(f"Failed to initialize QAAgent: {str(e)}")
        qa_agent = None

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg.get("role", "user")):
            st.markdown(msg.get("content", ""))

    if prompt := st.chat_input("Ask me anything about hospitals in Bengaluru …"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if qa_agent is None:
                response = "I'm sorry, the QA agent is not available. Please check your setup."
            else:
                with st.spinner("Thinking …"):
                    try:
                        response = qa_agent.answer(prompt)
                    except Exception as e:
                        response = f"I encountered an error: {str(e)}"
            st.markdown(response)
        st.session_state.chat_history.append({"role": "assistant", "content": response})

    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

    # Suggested questions
    st.markdown("#### 💡 Try asking:")
    suggestions = [
        "Which hospitals have the best cardiology departments?",
        "What is the average consultation fee for an orthopedic surgeon?",
        "List all services available at Manipal Hospital",
        "Which doctors speak Tamil and Kannada?",
        "What's the cost of an MRI scan in Bengaluru?",
    ]
    cols = st.columns(2)
    for i, s in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(s, key=f"sug_{i}"):
                st.session_state.chat_history.append({"role": "user", "content": s})
                if qa_agent is not None:
                    with st.spinner("Thinking …"):
                        try:
                            resp = qa_agent.answer(s)
                        except Exception as e:
                            resp = f"I encountered an error: {str(e)}"
                else:
                    resp = "QA agent not available."
                st.session_state.chat_history.append({"role": "assistant", "content": resp})
                st.rerun()


# ─────────────────────────────────────────────
# PAGE: LEAD SCORING
# ─────────────────────────────────────────────
elif page == "📊 Lead Scoring":
    st.header("📊 Lead Scoring Dashboard")
    
    try:
        scorer = LeadScorerAgent()
    except Exception as e:
        st.error(f"Failed to initialize LeadScorerAgent: {str(e)}")
        scorer = None

    try:
        top_leads = scorer.top_leads(20) if scorer else pd.DataFrame()
        if top_leads.empty:
            st.warning("No lead data found. Run the scraper first.")
        else:
            # KPIs
            c1, c2, c3, c4 = st.columns(4)
            df_leads = data_loader.get("lead_scores")
            with c1:
                st.metric("Total Leads", len(df_leads) if not df_leads.empty else 0)
            with c2:
                high_count = len(df_leads[df_leads["priority"]=="High"]) if not df_leads.empty else 0
                st.metric("High Priority", high_count)
            with c3:
                converted_count = len(df_leads[df_leads["status"]=="Converted"]) if not df_leads.empty else 0
                st.metric("Converted", converted_count)
            with c4:
                avg_score = df_leads["lead_score"].mean() if not df_leads.empty else 0
                st.metric("Avg Score", f"{avg_score:.1f}")

            st.markdown("---")
            st.subheader("🏆 Top 20 Leads")
            display_cols = ["lead_id", "patient_name", "intent", "channel", "lead_score", "priority", "status", "created_at"]
            available_cols = [c for c in display_cols if c in top_leads.columns]
            st.dataframe(top_leads[available_cols], width="stretch")

            st.markdown("---")
            st.subheader("🤖 Score a New Lead with AI")
            with st.form("lead_form"):
                c1, c2 = st.columns(2)
                with c1:
                    lead_name = st.text_input("Patient Name")
                    lead_phone = st.text_input("Phone")
                    lead_intent = st.selectbox("Intent", ["Book Appointment", "Get Information", "Emergency", "Follow-up", "Insurance Query"])
                with c2:
                    lead_channel = st.selectbox("Channel", ["Web Chat", "WhatsApp", "Phone", "Walk-in", "App"])
                    lead_dept = st.text_input("Department of Interest")
                    lead_notes = st.text_area("Notes", height=80)
                score_btn = st.form_submit_button("🎯 Score Lead", type="primary")

            if score_btn and lead_name and scorer:
                lead_data = {
                    "name": lead_name,
                    "phone": lead_phone,
                    "intent": lead_intent,
                    "channel": lead_channel,
                    "department": lead_dept,
                    "notes": lead_notes,
                }
                with st.spinner("Scoring with AI …"):
                    try:
                        result = scorer.score(lead_data)

                        col1, col2 = st.columns(2)
                        with col1:
                            score = result.get("score", 0)
                            st.metric("Lead Score", f"{score}/100")
                            priority = result.get("priority", "Medium")
                            badge_class = f"badge-{priority.lower()}"
                            st.markdown(f'<span class="{badge_class}">{priority} Priority</span>', unsafe_allow_html=True)
                        with col2:
                            st.info(f"**Recommended Action:** {result.get('recommended_action', '')}")
                            st.caption(result.get("reasoning", ""))
                    except Exception as e:
                        st.error(f"Scoring failed: {str(e)}")
    except Exception as e:
        st.error(f"Error loading lead scoring data: {str(e)}")


# ─────────────────────────────────────────────
# PAGE: ANALYTICS
elif page == "📈 Analytics":
    st.header("📈 Analytics")

    try:
        import plotly.express as px
        PLOTLY = True
    except ImportError:
        PLOTLY = False
        st.warning("Plotly not installed — showing tables instead.")

    try:
        df_hosp = data_loader.get("hospitals")
        df_doc = data_loader.get("doctors")
        df_svc = data_loader.get("services")
        df_leads = data_loader.get("lead_scores")
        df_search = data_loader.get("search_history")

        if df_hosp.empty:
            st.warning("No data. Run the scraper first.")
        else:
            tab1, tab2, tab3 = st.tabs(["Hospitals & Doctors", "Services", "Search & Leads"])

            with tab1:
                c1, c2 = st.columns(2)
                with c1:
                    if PLOTLY and not df_hosp.empty:
                        fig = px.histogram(df_hosp, x="type", title="Hospital Types", color="type")
                        st.plotly_chart(fig, width="stretch")
                    else:
                        st.dataframe(df_hosp["type"].value_counts().reset_index(), width="stretch")
                with c2:
                    if PLOTLY and not df_doc.empty:
                        top_depts = df_doc["department_name"].value_counts().head(10).reset_index()
                        top_depts.columns = ["Department", "Count"]
                        fig = px.bar(top_depts, x="Count", y="Department", orientation="h", title="Doctors by Department")
                        st.plotly_chart(fig, width="stretch")
                    elif not df_doc.empty:
                        st.dataframe(df_doc["department_name"].value_counts().head(10).reset_index(), width="stretch")

                if PLOTLY and not df_doc.empty:
                    fig = px.histogram(df_doc, x="consultation_fee", nbins=20, title="Consultation Fee Distribution (₹)")
                    st.plotly_chart(fig, width="stretch")

            with tab2:
                if not df_svc.empty and PLOTLY:
                    svc_cat = df_svc["category"].value_counts().reset_index()
                    svc_cat.columns = ["Category", "Count"]
                    fig = px.pie(svc_cat, names="Category", values="Count", title="Services by Category")
                    st.plotly_chart(fig, width="stretch")

                    # FIXED THIS LINE - added all parameters and closed the parentheses
                    fig2 = px.box(df_svc[df_svc["price"] > 0], x="category", y="price", title="Price Range by Service Category (₹)")
                    st.plotly_chart(fig2, width="stretch")

            with tab3:
                if not df_leads.empty and PLOTLY:
                    c1, c2 = st.columns(2)
                    with c1:
                        fig = px.histogram(df_leads, x="lead_score", nbins=20, title="Lead Score Distribution")
                        st.plotly_chart(fig, width="stretch")
                    with c2:
                        status_counts = df_leads["status"].value_counts().reset_index()
                        status_counts.columns = ["Status", "Count"]
                        fig = px.pie(status_counts, names="Status", values="Count", title="Lead Status Breakdown")
                        st.plotly_chart(fig, width="stretch")

                if not df_search.empty and PLOTLY:
                    loc_counts = df_search["user_location"].value_counts().reset_index()
                    loc_counts.columns = ["Location", "Count"]
                    fig = px.bar(loc_counts, x="Location", y="Count", title="Searches by Location")
                    st.plotly_chart(fig, width="stretch")
    except Exception as e:
        st.error(f"Error loading analytics: {str(e)}")
