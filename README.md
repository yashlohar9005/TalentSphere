# TalentSphere Elevate 🚀

![TalentSphere Elevate](https://img.shields.io/badge/Status-Active-success)
![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B)
![Database](https://img.shields.io/badge/Database-SQLAlchemy-green)
![AI Powered](https://img.shields.io/badge/AI-Google_Generative_AI-orange)

# TalentSphere Elevate (V2 Full-Stack Architecture)

An AI-powered career growth and recruitment platform serving High School Students, College Students, and Working Professionals.

## Architecture Migration
The project is currently migrating from a monolithic Streamlit/SQLite setup to a production-ready **FastAPI + PostgreSQL** backend with a decoupled Streamlit frontend.

The new backend code is located in the `app/` directory.
The legacy Streamlit code remains at the root level until the migration is complete.

## How to run the new Backend API (FastAPI)

1. Ensure PostgreSQL is installed and running on your local machine.
2. Create a database named `talentsphere`.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```
4. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```
5. View the interactive API docs at `http://localhost:8000/docs`.

## How to run the Legacy Frontend (Streamlit)

1. Start the Streamlit server:
   ```bash
   streamlit run app.py
   ```

## 🌟 Key Features

The platform offers distinct dashboards tailored to different user profiles:

### 🎓 High School Students
- **Career Exploration:** Discover potential career paths based on interests and skills.
- **Skill Building:** Early-stage skill development and recommendations.
- **AI Guidance:** Ask questions and get personalized advice for college prep and career planning.

### 🏫 College Students
- **Resume Building:** Create and refine professional resumes.
- **Interview Preparation:** AI-driven mock interviews and question generation.
- **Internship/Job Strategies:** Tailored advice for landing the first job.
- **Progress Tracking:** Monitor academic and extracurricular milestones.

### 💼 Working Professionals
- **Career Growth Planning:** Chart out long-term career trajectories and milestones.
- **Skill Upgradation:** Identify skill gaps and get targeted learning recommendations.
- **Performance Analysis:** Tools for self-assessment and goal setting.

### 🛡️ Admin
- **User Management:** Manage users, monitor activity, and oversee system health.
- **Analytics Dashboard:** Visualize platform usage, demographics, and engagement metrics.

## 🛠️ Technology Stack

- **Frontend:** Streamlit, Plotly (for interactive charts)
- **Backend & Database:** Python, SQLAlchemy, SQLite (`talentsphere.db`)
- **Authentication:** bcrypt (secure password hashing)
- **AI Engine:** Google Generative AI (Gemini) integration for dynamic content generation
- **Data Analysis & Processing:** Pandas, NumPy, scikit-learn
- **Reporting:** ReportLab (for PDF generation)

## ⚙️ Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.8 or higher
- `pip` (Python package manager)

## 🚀 Installation & Setup

1. **Clone the repository (if applicable) or navigate to the project directory:**
   ```bash
   cd "e:\infosys springborad internship\Project"
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   You will need to set up your Google Generative AI API Key for the AI Engine to function correctly. Ensure your environment variables are configured appropriately.

## 🏃‍♂️ Running the Application

To launch TalentSphere Elevate, run the following command from the project root directory:

```bash
streamlit run app.py
```

The application will start a local server and open in your default web browser (typically at `http://localhost:8501`).

## 📁 Project Structure

```text
Project/
├── app.py                     # Main application entry point
├── database.py                # Database setup, models, and session management
├── ai/                        # AI Engine integration (Google Generative AI)
├── modules/                   # Core functionality divided by user roles
│   ├── high_school/           # Dashboard for High School Students
│   ├── college/               # Dashboard for College Students
│   └── professional/          # Dashboard for Working Professionals
├── admin/                     # Admin dashboard and analytics
├── reports/                   # PDF generation and report engine
├── resume/                    # Resume building features
├── notifications/             # Notification system
├── assets/                    # Static assets (images, CSS, etc.)
└── requirements.txt           # Python package dependencies
```

## 🤝 Contributing

Contributions are welcome! Please follow the standard fork-and-pull request workflow.

## 📄 License

This project is part of the Infosys Springboard Internship program. All rights reserved.
