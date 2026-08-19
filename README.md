# AI Resume Analyzer & Career Assistant

An AI-powered web application that analyzes resumes, calculates ATS scores, matches resumes with job descriptions, and provides personalized career guidance.

## 🚀 Features

- 📄 PDF Resume Upload
- 📊 ATS Resume Scoring
- 🤖 AI-Powered Resume Analysis
- 🎯 Job Description Matching
- 🔍 Matched & Missing Skills Detection
- 💬 AI Career Assistant
- 👤 User Signup & Login
- 🔐 Secure Password Hashing
- 📚 Resume & Job Match History
- 📈 Personalized Dashboard
- 🗄️ MongoDB Data Storage
- 📱 Responsive Web Interface

## 🛠️ Technologies Used

### Backend
- Python
- Flask

### AI
- Groq API
- Large Language Model

### Database
- MongoDB Atlas

### Frontend
- HTML
- CSS
- Jinja2

### Other Technologies
- PyMuPDF
- Git
- GitHub
- Python-dotenv

## 🏗️ Project Architecture

```text
User
 │
 ▼
Flask Web Application
 │
 ├── Resume Analyzer
 │      ├── PDF Extraction
 │      ├── ATS Scoring
 │      └── AI Analysis
 │
 ├── Job Match
 │      ├── Skill Matching
 │      ├── Missing Skills
 │      └── AI Analysis
 │
 ├── Career Assistant
 │      └── Resume-based AI Advice
 │
 └── User Dashboard
        ├── Resume History
        ├── Job Match History
        └── Career History
 │
 ▼
MongoDB Atlas
```
## 📁 Project Structure

```text
AI-Resume-Analyzer/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── static/
│   └── css/
│       └── style.css
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── dashboard.html
│   ├── analysis.html
│   ├── job_match.html
│   ├── job_result.html
│   └── career_assistant.html
│
└── uploads/

```
## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/SRIKANTHPULAPA/AI-Resume-Analyzer.git