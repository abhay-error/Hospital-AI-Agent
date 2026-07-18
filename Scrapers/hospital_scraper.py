"""
Hospital Data Scraper
Scrapes hospital data from public sources and generates structured CSVs.
Falls back to realistic synthetic data when live scraping is unavailable.
"""
import pandas as pd
import requests
from bs4 import BeautifulSoup
import random
import time
import uuid
import os
from datetime import datetime, timedelta
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ─────────────────────────────────────────────
# SCRAPERS  (try real, fallback to synthetic)
# ─────────────────────────────────────────────

def scrape_or_generate_hospitals():
    """Try to scrape hospital listing; fall back to synthetic."""
    hospitals = []
    try:
        url = "https://www.practo.com/bangalore/hospitals"
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "lxml")
        cards = soup.select(".listing-container .info-section")
        for card in cards[:20]:
            name_tag = card.select_one("h2")
            addr_tag = card.select_one(".location-link")
            if name_tag:
                hospitals.append({
                    "hospital_id": str(uuid.uuid4())[:8].upper(),
                    "name": name_tag.get_text(strip=True),
                    "address": addr_tag.get_text(strip=True) if addr_tag else "Bengaluru, Karnataka",
                    "city": "Bengaluru",
                    "state": "Karnataka",
                    "pincode": random.choice(["560001","560002","560003","560068","560076"]),
                    "phone": f"+91-80-{random.randint(2000,9999)}{random.randint(1000,9999)}",
                    "email": "",
                    "website": "",
                    "beds": random.randint(50, 800),
                    "established": random.randint(1970, 2015),
                    "type": random.choice(["Multi-Specialty","Super-Specialty","General"]),
                    "accreditation": random.choice(["NABH","JCI","NABL","None"]),
                    "rating": round(random.uniform(3.5, 5.0), 1),
                    "reviews_count": random.randint(50, 5000),
                })
        print(f"[Scraper] Scraped {len(hospitals)} hospitals from Practo")
    except Exception as e:
        print(f"[Scraper] Live scrape failed ({e}), using synthetic data")

    if len(hospitals) < 5:
        hospitals = generate_synthetic_hospitals()
    return pd.DataFrame(hospitals)


def generate_synthetic_hospitals():
    names = [
        "Manipal Hospital", "Fortis Hospital", "Apollo Hospitals",
        "Narayana Health", "Columbia Asia Hospital", "BGS Gleneagles",
        "Sakra World Hospital", "Aster CMI Hospital", "St. John's Hospital",
        "NIMHANS", "Victoria Hospital", "Bowring & Lady Curzon Hospital",
        "Sparsh Hospital", "Cloudnine Hospital", "Motherhood Hospital",
    ]
    hospitals = []
    for i, name in enumerate(names):
        hospitals.append({
            "hospital_id": f"HOSP{str(i+1).zfill(3)}",
            "name": name,
            "address": f"{random.randint(1,99)}, {random.choice(['MG Road','Whitefield','Jayanagar','Indiranagar','Koramangala','Hebbal','Yeshwanthpur'])}",
            "city": "Bengaluru",
            "state": "Karnataka",
            "pincode": random.choice(["560001","560017","560034","560068","560076","560066"]),
            "phone": f"+91-80-{random.randint(2000,9999)}{random.randint(1000,9999)}",
            "email": f"info@{name.lower().replace(' ', '').replace(chr(39), '')}bengaluru.com",
            "website": f"https://www.{name.lower().replace(' ', '').replace(chr(39), '')}bengaluru.com",
            "beds": random.randint(50, 1500),
            "established": random.randint(1960, 2018),
            "type": random.choice(["Multi-Specialty","Super-Specialty","General","Maternity","Children"]),
            "accreditation": random.choice(["NABH","JCI","NABL,NABH","None"]),
            "rating": round(random.uniform(3.5, 5.0), 1),
            "reviews_count": random.randint(100, 8000),
        })
    return hospitals


def generate_departments(hospital_df):
    dept_catalog = [
        ("Cardiology", "Heart & cardiovascular care"),
        ("Neurology", "Brain & nervous system disorders"),
        ("Orthopedics", "Bone, joint & muscle care"),
        ("Oncology", "Cancer diagnosis & treatment"),
        ("Gynecology", "Women's health & maternity"),
        ("Pediatrics", "Child health & development"),
        ("Emergency Medicine", "24/7 emergency & trauma care"),
        ("Radiology", "Imaging & diagnostics"),
        ("Gastroenterology", "Digestive system disorders"),
        ("Urology", "Urinary tract & kidney care"),
        ("Pulmonology", "Lung & respiratory care"),
        ("Endocrinology", "Hormonal & metabolic disorders"),
        ("Dermatology", "Skin, hair & nail care"),
        ("Psychiatry", "Mental health & behavioral care"),
        ("Ophthalmology", "Eye care & surgery"),
        ("ENT", "Ear, nose & throat care"),
        ("Nephrology", "Kidney disease management"),
        ("Rheumatology", "Arthritis & autoimmune care"),
        ("Plastic Surgery", "Reconstructive & cosmetic surgery"),
        ("Anesthesiology", "Surgical anesthesia & pain management"),
    ]
    records = []
    dept_id = 1
    for _, hosp in hospital_df.iterrows():
        n_depts = random.randint(5, len(dept_catalog))
        chosen = random.sample(dept_catalog, n_depts)
        for dept_name, dept_desc in chosen:
            records.append({
                "dept_id": f"DEPT{str(dept_id).zfill(4)}",
                "hospital_id": hosp["hospital_id"],
                "hospital_name": hosp["name"],
                "department_name": dept_name,
                "description": dept_desc,
                "floor": random.randint(1, 6),
                "block": random.choice(["A","B","C","D"]),
                "head_doctor": f"Dr. {random.choice(['Arun','Priya','Ravi','Meena','Suresh','Kavita','Rajesh','Anita'])} {random.choice(['Kumar','Sharma','Nair','Reddy','Patel','Iyer','Singh','Rao'])}",
                "contact_ext": str(random.randint(100, 999)),
                "opd_timings": "Mon-Sat 9:00 AM – 5:00 PM",
                "beds_allocated": random.randint(10, 80),
                "is_active": True,
            })
            dept_id += 1
    return pd.DataFrame(records)


def generate_doctors(dept_df):
    first_names = ["Arun","Priya","Ravi","Meena","Suresh","Kavita","Rajesh","Anita","Vikram","Deepa","Arjun","Sunita","Kiran","Pooja","Rohit","Nisha"]
    last_names = ["Kumar","Sharma","Nair","Reddy","Patel","Iyer","Singh","Rao","Gupta","Menon","Pillai","Joshi","Verma","Das","Bhat","Hegde"]
    specializations = {
        "Cardiology": ["Interventional Cardiologist","Cardiac Electrophysiologist","Heart Failure Specialist"],
        "Neurology": ["Stroke Specialist","Epileptologist","Movement Disorder Specialist"],
        "Orthopedics": ["Joint Replacement Surgeon","Spine Surgeon","Sports Medicine Specialist"],
        "Oncology": ["Medical Oncologist","Surgical Oncologist","Radiation Oncologist"],
        "Gynecology": ["Obstetrician","Gynecologic Oncologist","Reproductive Endocrinologist"],
        "Pediatrics": ["Neonatologist","Pediatric Cardiologist","General Pediatrician"],
    }
    records = []
    doc_id = 1
    for _, dept in dept_df.iterrows():
        n_docs = random.randint(2, 6)
        for _ in range(n_docs):
            dept_name = dept["department_name"]
            specs = specializations.get(dept_name, [f"{dept_name} Specialist", f"Consultant {dept_name}"])
            fn = random.choice(first_names)
            ln = random.choice(last_names)
            records.append({
                "doctor_id": f"DOC{str(doc_id).zfill(5)}",
                "hospital_id": dept["hospital_id"],
                "dept_id": dept["dept_id"],
                "department_name": dept_name,
                "name": f"Dr. {fn} {ln}",
                "specialization": random.choice(specs),
                "qualification": random.choice(["MBBS, MD","MBBS, MS","MBBS, DM","MBBS, MCh","MBBS, DNB"]),
                "experience_years": random.randint(3, 30),
                "gender": random.choice(["Male","Female"]),
                "languages": random.choice(["English, Kannada","English, Hindi, Kannada","English, Tamil, Kannada"]),
                "consultation_fee": random.choice([300, 400, 500, 600, 700, 800, 1000, 1200, 1500]),
                "available_days": random.choice(["Mon,Wed,Fri","Tue,Thu,Sat","Mon-Fri","Mon-Sat"]),
                "available_slots": "9:00 AM,10:00 AM,11:00 AM,2:00 PM,3:00 PM,4:00 PM",
                "rating": round(random.uniform(3.8, 5.0), 1),
                "reviews_count": random.randint(10, 1000),
                "email": f"{fn.lower()}.{ln.lower()}@hospital.com",
                "phone": f"+91-9{random.randint(100000000,999999999)}",
                "is_available": random.choice([True, True, True, False]),
            })
            doc_id += 1
    return pd.DataFrame(records)


def generate_services(hospital_df):
    service_catalog = [
        ("OPD Consultation", "Outpatient consultation with specialist", 300, 1500, "Consultation"),
        ("ECG", "12-lead electrocardiogram", 200, 500, "Diagnostic"),
        ("MRI Scan", "Magnetic resonance imaging", 5000, 15000, "Imaging"),
        ("CT Scan", "Computed tomography scan", 3000, 10000, "Imaging"),
        ("X-Ray", "Digital radiography", 300, 800, "Imaging"),
        ("Blood Test - CBC", "Complete blood count", 200, 500, "Lab"),
        ("Blood Test - LFT", "Liver function test", 500, 1200, "Lab"),
        ("Blood Test - KFT", "Kidney function test", 500, 1200, "Lab"),
        ("Ultrasound", "Abdominal/pelvic ultrasound", 800, 2500, "Imaging"),
        ("2D Echo", "Echocardiography", 1500, 4000, "Cardiac"),
        ("Endoscopy", "Upper GI endoscopy", 3000, 8000, "Procedure"),
        ("Dialysis", "Hemodialysis session", 2000, 5000, "Procedure"),
        ("Physiotherapy", "Physical therapy session", 500, 1500, "Therapy"),
        ("ICU Care (per day)", "Intensive care unit admission", 10000, 30000, "Inpatient"),
        ("General Ward (per day)", "General ward admission", 2000, 6000, "Inpatient"),
        ("Emergency Services", "24/7 emergency care", 0, 0, "Emergency"),
        ("Vaccination", "Immunization services", 300, 2000, "Preventive"),
        ("Health Checkup - Basic", "Basic health screening package", 1500, 4000, "Package"),
        ("Health Checkup - Comprehensive", "Full body checkup", 5000, 15000, "Package"),
        ("Surgical Procedure", "Minor/major surgical intervention", 10000, 200000, "Surgery"),
    ]
    records = []
    svc_id = 1
    for _, hosp in hospital_df.iterrows():
        n_svcs = random.randint(8, len(service_catalog))
        chosen = random.sample(service_catalog, n_svcs)
        for name, desc, price_min, price_max, category in chosen:
            price = random.randint(price_min, max(price_min+100, price_max)) if price_min > 0 else 0
            records.append({
                "service_id": f"SVC{str(svc_id).zfill(5)}",
                "hospital_id": hosp["hospital_id"],
                "hospital_name": hosp["name"],
                "service_name": name,
                "description": desc,
                "category": category,
                "price": price,
                "duration_minutes": random.choice([15, 30, 45, 60, 90, 120]),
                "requires_appointment": random.choice([True, True, False]),
                "available_24x7": name == "Emergency Services",
                "insurance_covered": random.choice([True, False]),
            })
            svc_id += 1
    return pd.DataFrame(records)


def generate_contacts(hospital_df):
    records = []
    contact_id = 1
    contact_types = ["Emergency", "Appointment Desk", "Billing", "Blood Bank", "Pharmacy", "Ambulance", "Reception"]
    for _, hosp in hospital_df.iterrows():
        for ctype in random.sample(contact_types, random.randint(3, len(contact_types))):
            records.append({
                "contact_id": f"CON{str(contact_id).zfill(5)}",
                "hospital_id": hosp["hospital_id"],
                "hospital_name": hosp["name"],
                "contact_type": ctype,
                "name": ctype,
                "phone": f"+91-80-{random.randint(2000,9999)}{random.randint(1000,9999)}",
                "email": f"{ctype.lower().replace(' ','.')}@{hosp['name'].lower().replace(' ','')}.com",
                "available_hours": "24/7" if ctype in ["Emergency","Ambulance"] else "Mon-Sat 8AM-8PM",
                "is_primary": ctype == "Reception",
            })
            contact_id += 1
    return pd.DataFrame(records)


def generate_documents(hospital_df, doctor_df):
    doc_types = [
        ("Accreditation Certificate", "Certification"),
        ("NABH Certificate", "Certification"),
        ("Doctor Registration", "License"),
        ("Facility License", "License"),
        ("Insurance Empanelment", "Insurance"),
        ("Quality Policy", "Policy"),
        ("Patient Rights Charter", "Policy"),
        ("Price List", "Information"),
        ("Visiting Hours Policy", "Policy"),
    ]
    records = []
    doc_id = 1
    for _, hosp in hospital_df.iterrows():
        for dtype, dcat in random.sample(doc_types, random.randint(3, 6)):
            records.append({
                "document_id": f"DOCU{str(doc_id).zfill(5)}",
                "hospital_id": hosp["hospital_id"],
                "title": f"{hosp['name']} – {dtype}",
                "category": dcat,
                "file_type": random.choice(["PDF","PDF","PDF","DOCX"]),
                "file_size_kb": random.randint(50, 5000),
                "upload_date": (datetime.now() - timedelta(days=random.randint(10, 730))).strftime("%Y-%m-%d"),
                "expiry_date": (datetime.now() + timedelta(days=random.randint(30, 1095))).strftime("%Y-%m-%d"),
                "is_public": random.choice([True, False]),
                "description": f"Official {dtype.lower()} document for {hosp['name']}",
            })
            doc_id += 1
    return pd.DataFrame(records)


def generate_embeddings_metadata(hospital_df, doctor_df, service_df):
    records = []
    emb_id = 1
    for _, hosp in hospital_df.iterrows():
        text = f"{hosp['name']} located at {hosp['address']}, {hosp['city']}. {hosp['type']} hospital with {hosp['beds']} beds. Accreditation: {hosp['accreditation']}. Rating: {hosp['rating']}."
        records.append({
            "embedding_id": f"EMB{str(emb_id).zfill(6)}",
            "source_type": "hospital",
            "source_id": hosp["hospital_id"],
            "text_chunk": text,
            "chunk_index": 0,
            "token_count": len(text.split()),
            "model": "text-embedding-3-small",
            "vector_dim": 1536,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        emb_id += 1

    for _, doc in doctor_df.iterrows():
        text = f"Dr. {doc['name']}, {doc['specialization']} at {doc['department_name']}. Qualification: {doc['qualification']}. Experience: {doc['experience_years']} years. Consultation fee: ₹{doc['consultation_fee']}. Available: {doc['available_days']}."
        records.append({
            "embedding_id": f"EMB{str(emb_id).zfill(6)}",
            "source_type": "doctor",
            "source_id": doc["doctor_id"],
            "text_chunk": text,
            "chunk_index": 0,
            "token_count": len(text.split()),
            "model": "text-embedding-3-small",
            "vector_dim": 1536,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        emb_id += 1

    for _, svc in service_df.iterrows():
        text = f"{svc['service_name']}: {svc['description']}. Price: ₹{svc['price']}. Duration: {svc['duration_minutes']} min. Insurance covered: {svc['insurance_covered']}."
        records.append({
            "embedding_id": f"EMB{str(emb_id).zfill(6)}",
            "source_type": "service",
            "source_id": svc["service_id"],
            "text_chunk": text,
            "chunk_index": 0,
            "token_count": len(text.split()),
            "model": "text-embedding-3-small",
            "vector_dim": 1536,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        emb_id += 1
    return pd.DataFrame(records)


def generate_lead_scores(doctor_df):
    records = []
    lead_id = 1
    intents = ["Book Appointment", "Get Information", "Emergency", "Follow-up", "Insurance Query"]
    channels = ["Web Chat", "WhatsApp", "Phone", "Walk-in", "App"]
    for _, doc in doctor_df.sample(min(len(doctor_df), 200)).iterrows():
        score = random.randint(20, 100)
        records.append({
            "lead_id": f"LEAD{str(lead_id).zfill(6)}",
            "doctor_id": doc["doctor_id"],
            "hospital_id": doc["hospital_id"],
            "patient_name": f"{random.choice(['Rahul','Priya','Arun','Sneha','Vikram','Ananya'])} {random.choice(['Kumar','Sharma','Nair','Reddy'])}",
            "phone": f"+91-9{random.randint(100000000,999999999)}",
            "email": f"patient{lead_id}@email.com",
            "intent": random.choice(intents),
            "channel": random.choice(channels),
            "lead_score": score,
            "priority": "High" if score >= 75 else "Medium" if score >= 50 else "Low",
            "status": random.choice(["New","Contacted","Appointment Booked","Converted","Lost"]),
            "created_at": (datetime.now() - timedelta(days=random.randint(0,90))).strftime("%Y-%m-%d %H:%M:%S"),
            "last_interaction": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        lead_id += 1
    return pd.DataFrame(records)


def generate_search_history():
    queries = [
        "cardiologist near me Bengaluru",
        "best orthopedic surgeon Koramangala",
        "pediatrician appointment today",
        "24 hour emergency hospital Whitefield",
        "MRI scan cost Bengaluru",
        "gynecologist for pregnancy",
        "diabetes specialist endocrinologist",
        "physiotherapy session near Indiranagar",
        "blood test CBC cost",
        "neurology consultation Manipal",
        "cancer treatment hospital Bengaluru",
        "dialysis center Hebbal",
        "skin specialist dermatologist",
        "eye specialist ophthalmologist appointment",
        "mental health psychiatrist consultation",
    ]
    records = []
    for i in range(300):
        records.append({
            "search_id": f"SRCH{str(i+1).zfill(6)}",
            "session_id": str(uuid.uuid4())[:12],
            "query": random.choice(queries),
            "results_count": random.randint(1, 20),
            "clicked_result": random.choice([True, False]),
            "appointment_booked": random.choice([True, False, False, False]),
            "timestamp": (datetime.now() - timedelta(minutes=random.randint(0, 43200))).strftime("%Y-%m-%d %H:%M:%S"),
            "user_location": random.choice(["Koramangala","Whitefield","Indiranagar","Jayanagar","Hebbal","Yeshwanthpur"]),
            "device": random.choice(["Mobile","Desktop","Tablet"]),
        })
    return pd.DataFrame(records)


# ─────────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────────

def run_scraper():
    print("=" * 55)
    print("  Hospital Data Scraper — Starting")
    print("=" * 55)

    print("\n[1/8] Scraping/generating hospitals …")
    hospital_df = scrape_or_generate_hospitals()
    hospital_df.to_csv(f"{OUTPUT_DIR}/hospitals.csv", index=False)
    print(f"      ✓ {len(hospital_df)} hospitals saved")

    print("[2/8] Generating departments …")
    dept_df = generate_departments(hospital_df)
    dept_df.to_csv(f"{OUTPUT_DIR}/departments.csv", index=False)
    print(f"      ✓ {len(dept_df)} departments saved")

    print("[3/8] Generating doctors …")
    doctor_df = generate_doctors(dept_df)
    doctor_df.to_csv(f"{OUTPUT_DIR}/doctors.csv", index=False)
    print(f"      ✓ {len(doctor_df)} doctors saved")

    print("[4/8] Generating services …")
    service_df = generate_services(hospital_df)
    service_df.to_csv(f"{OUTPUT_DIR}/services.csv", index=False)
    print(f"      ✓ {len(service_df)} services saved")

    print("[5/8] Generating contacts …")
    contact_df = generate_contacts(hospital_df)
    contact_df.to_csv(f"{OUTPUT_DIR}/contacts.csv", index=False)
    print(f"      ✓ {len(contact_df)} contacts saved")

    print("[6/8] Generating documents …")
    doc_df = generate_documents(hospital_df, doctor_df)
    doc_df.to_csv(f"{OUTPUT_DIR}/documents.csv", index=False)
    print(f"      ✓ {len(doc_df)} documents saved")

    print("[7/8] Generating embeddings metadata …")
    emb_df = generate_embeddings_metadata(hospital_df, doctor_df, service_df)
    emb_df.to_csv(f"{OUTPUT_DIR}/embeddings_metadata.csv", index=False)
    print(f"      ✓ {len(emb_df)} embedding records saved")

    print("[8/8] Generating lead scores & search history …")
    lead_df = generate_lead_scores(doctor_df)
    lead_df.to_csv(f"{OUTPUT_DIR}/lead_scores.csv", index=False)
    search_df = generate_search_history()
    search_df.to_csv(f"{OUTPUT_DIR}/search_history.csv", index=False)
    print(f"      ✓ {len(lead_df)} leads, {len(search_df)} search records saved")

    print("\n" + "=" * 55)
    print("  All CSVs written to /data/")
    print("=" * 55)
    return {
        "hospitals": hospital_df,
        "departments": dept_df,
        "doctors": doctor_df,
        "services": service_df,
        "contacts": contact_df,
        "documents": doc_df,
        "embeddings_metadata": emb_df,
        "lead_scores": lead_df,
        "search_history": search_df,
    }


if __name__ == "__main__":
    run_scraper()
