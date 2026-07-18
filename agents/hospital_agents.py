"""
Hospital Agents
Four specialised agents that coordinate to handle user queries and bookings.
"""
import json
import random
import pandas as pd
from datetime import datetime, timedelta
from utils import data_loader, llm_client


# ──────────────────────────────────────────────────
# 1. HOSPITAL RETRIEVAL AGENT
# ──────────────────────────────────────────────────
class HospitalRetrieverAgent:
    """Finds hospitals matching user requirements."""

    SYSTEM = """You are a hospital retrieval assistant for Bengaluru.
Given a user query and a JSON list of hospitals, return the top 3 most relevant hospitals.
Respond ONLY with a JSON array of hospital_ids, e.g.: ["HOSP001","HOSP003","HOSP007"]
Consider: speciality needed, location preference, rating, type of hospital."""

    def retrieve(self, query: str, filters: dict = None) -> list[dict]:
        df = data_loader.get("hospitals")
        if df.empty:
            return []

        # Apply hard filters
        if filters:
            if filters.get("min_rating"):
                df = df[df["rating"] >= float(filters["min_rating"])]
            if filters.get("hospital_type") and filters["hospital_type"] != "Any":
                df = df[df["type"].str.contains(filters["hospital_type"], case=False, na=False)]

        sample = df.head(30).to_dict(orient="records")
        prompt = f"User query: {query}\n\nHospitals:\n{json.dumps(sample, default=str)}"
        response = llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            system=self.SYSTEM,
            temperature=0.2,
        )
        try:
            ids = json.loads(response)
            results = df[df["hospital_id"].isin(ids)].to_dict(orient="records")
            if not results:
                results = df.head(3).to_dict(orient="records")
        except Exception:
            results = df.head(3).to_dict(orient="records")
        return results


# ──────────────────────────────────────────────────
# 2. DOCTOR FINDER AGENT
# ──────────────────────────────────────────────────
class DoctorFinderAgent:
    """Finds the right doctor for a given symptom/speciality."""

    SYSTEM = """You are a doctor-matching assistant.
Given a patient query and a list of doctors (JSON), return the top 3 doctor_ids best suited.
Respond ONLY with a JSON array: ["DOC00001","DOC00002","DOC00003"]
Consider: specialization match, experience, availability, rating, consultation fee."""

    def find(self, query: str, hospital_ids: list = None, dept_filter: str = None) -> list[dict]:
        df = data_loader.get("doctors")
        if df.empty:
            return []

        if hospital_ids:
            df = df[df["hospital_id"].isin(hospital_ids)]
        if dept_filter and dept_filter != "Any":
            df = df[df["department_name"].str.contains(dept_filter, case=False, na=False)]

        df_avail = df[df["is_available"] == True]
        sample = df_avail.head(40).to_dict(orient="records")

        prompt = f"Patient query: {query}\n\nDoctors:\n{json.dumps(sample, default=str)}"
        response = llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            system=self.SYSTEM,
            temperature=0.2,
        )
        try:
            ids = json.loads(response)
            results = df[df["doctor_id"].isin(ids)].to_dict(orient="records")
            if not results:
                results = df_avail.head(3).to_dict(orient="records")
        except Exception:
            results = df_avail.head(3).to_dict(orient="records")
        return results

    def get_slots(self, doctor_id: str, date: str) -> list[str]:
        df = data_loader.get("doctors")
        doc = df[df["doctor_id"] == doctor_id]
        if doc.empty:
            return []
        slots_str = doc.iloc[0].get("available_slots", "9:00 AM,10:00 AM,11:00 AM,2:00 PM,3:00 PM")
        all_slots = [s.strip() for s in slots_str.split(",")]
        # Randomly mark some as booked
        available = [s for s in all_slots if random.random() > 0.3]
        return available if available else all_slots[:2]


# ──────────────────────────────────────────────────
# 3. BOOKING AGENT
# ──────────────────────────────────────────────────
class BookingAgent:
    """Handles the appointment booking pipeline end-to-end."""

    SYSTEM = """You are a hospital appointment booking assistant.
Your job is to confirm appointment details and generate a friendly confirmation message.
Include: patient name, doctor name, hospital, department, date, time, fee, and a booking reference.
Be warm, professional, and concise."""

    def __init__(self):
        self.appointments = []  # In-memory store (replace with DB in production)

    def book(self, booking_data: dict) -> dict:
        """Create an appointment record and return confirmation."""
        ref = f"APT{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(10,99)}"
        appointment = {
            "booking_ref": ref,
            "status": "Confirmed",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            **booking_data,
        }
        self.appointments.append(appointment)

        # Generate LLM confirmation message
        prompt = f"Generate a confirmation for this appointment:\n{json.dumps(appointment, default=str)}"
        message = llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            system=self.SYSTEM,
            temperature=0.5,
        )
        appointment["confirmation_message"] = message
        return appointment

    def cancel(self, ref: str) -> bool:
        for appt in self.appointments:
            if appt["booking_ref"] == ref:
                appt["status"] = "Cancelled"
                return True
        return False

    def list_appointments(self, patient_name: str = None) -> list[dict]:
        if patient_name:
            return [a for a in self.appointments if patient_name.lower() in a.get("patient_name","").lower()]
        return self.appointments


# ──────────────────────────────────────────────────
# 4. LEAD SCORER AGENT
# ──────────────────────────────────────────────────
class LeadScorerAgent:
    """Scores inbound leads and prioritises follow-ups."""

    SYSTEM = """You are a healthcare CRM lead scoring assistant.
Given a lead profile (JSON), return a JSON object with:
{
  "score": <integer 0-100>,
  "priority": "<High|Medium|Low>",
  "recommended_action": "<short action string>",
  "reasoning": "<1-2 sentences>"
}
Respond ONLY with the JSON object, no markdown."""

    def score(self, lead_data: dict) -> dict:
        prompt = f"Score this lead:\n{json.dumps(lead_data, default=str)}"
        response = llm_client.chat(
            messages=[{"role": "user", "content": prompt}],
            system=self.SYSTEM,
            temperature=0.2,
        )
        try:
            clean = response.strip().strip("```json").strip("```").strip()
            return json.loads(clean)
        except Exception:
            return {
                "score": random.randint(40, 80),
                "priority": "Medium",
                "recommended_action": "Follow up within 24 hours",
                "reasoning": "Score estimated due to parsing error.",
            }

    def top_leads(self, n: int = 10) -> pd.DataFrame:
        df = data_loader.get("lead_scores")
        if df.empty:
            return df
        return df.nlargest(n, "lead_score")


# ──────────────────────────────────────────────────
# 5. GENERAL QA AGENT (RAG-lite over CSV data)
# ──────────────────────────────────────────────────
class QAAgent:
    """Answers general hospital/health queries using CSV context."""

    SYSTEM = """You are a helpful hospital information assistant for Bengaluru.
Use the provided context (hospital/doctor/service data) to answer user questions accurately.
If information isn't in the context, say so honestly.
Be concise, friendly, and helpful. Format lists clearly."""

    def answer(self, question: str, context_tables: list[str] = None) -> str:
        context_tables = context_tables or ["hospitals", "doctors", "services"]
        context_parts = []
        for table in context_tables:
            df = data_loader.get(table)
            if not df.empty:
                sample = df.head(20).to_dict(orient="records")
                context_parts.append(f"### {table.upper()}:\n{json.dumps(sample, default=str)}")

        context_str = "\n\n".join(context_parts)
        messages = [
            {"role": "user", "content": f"Context:\n{context_str[:6000]}\n\nQuestion: {question}"}
        ]
        return llm_client.chat(messages=messages, system=self.SYSTEM, temperature=0.4)
