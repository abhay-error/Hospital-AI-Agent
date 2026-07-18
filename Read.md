# 🏥 Hospital AI Agent

An AI-powered Hospital Discovery and Appointment Assistant built using **Python**, **Streamlit**, and **OpenRouter LLMs**.

The application helps users search hospitals, discover doctors, schedule appointments, perform intelligent hospital retrieval, and visualize healthcare analytics through an interactive dashboard.

---

## Features

- AI Hospital Search
- Doctor Recommendation
- Appointment Booking
- Hospital Lead Scoring
- Analytics Dashboard
- AI Chat Assistant
- Hospital Data Scraper
- CSV-based Local Storage
- Streamlit Web Interface

---

## Project Structure

```
Hospital-AI-Agent
│
├── agents/
│   ├── hospital_agents.py
│
├── Scrapers/
│   ├── hospital_scraper.py
│
├── utils/
│   ├── data_loader.py
│   ├── llm_client.py
│
├── data/
│   ├── hospitals.csv
│   ├── doctors.csv
│   ├── departments.csv
│   ├── contacts.csv
│   ├── documents.csv
│
├── app.py
├── requirements.txt
├── README.md
└── .env
```

---

## Technologies Used

- Python 3.13+
- Streamlit
- OpenRouter API
- Pandas
- BeautifulSoup
- Requests
- Plotly
- NumPy

---

## Installation

Clone the repository

```bash
git clone https://github.com/yourusername/Hospital-AI-Agent.git
```

Move into the project

```bash
cd Hospital-AI-Agent
```

Create a virtual environment

```bash
python -m venv .venv
```

Activate it

Windows

```bash
.venv\Scripts\activate
```

Linux/macOS

```bash
source .venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the project root.

```
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_MODEL=mistralai/mistral-7b-instruct
```

---

## Run the Application

```bash
streamlit run app.py
```

The application will be available at

```
http://localhost:8501
```

---

## Project Modules

### Agents

- Hospital Retrieval Agent
- Doctor Finder Agent
- Booking Agent
- Lead Scoring Agent
- Question Answering Agent

### Scraper

Collects hospital information from public sources and generates structured datasets.

### Analytics

Provides visual insights into hospitals, doctors, appointments, and leads.

---

## Future Improvements

- PostgreSQL Integration
- Authentication
- Multi-city Hospital Support
- Email Notifications
- Calendar Integration
- Docker Deployment
- CI/CD Pipeline
- Cloud Deployment

---

## Author

1.Abhay Varun S 
Bachelor of Engineering (Artificial Intelligence & Machine Learning)
University of Mysore
2.Bopanna. K. N
Bachelor of Engineering (Artificial Intelligence & Data science)
University of Mysore

---

## License

This project is intended for educational and research purposes.