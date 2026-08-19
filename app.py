from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from openai import OpenAI
from pymongo import MongoClient
import os
import fitz
import re
from datetime import datetime

# =======================================
# BASIC SETUP
# =======================================

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "change-this-secret-key"
)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =======================================
# GROQ AI CLIENT
# =======================================

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)


# =======================================
# MONGODB
# =======================================

mongo_client = MongoClient(
    os.getenv("MONGO_URI")
)

db = mongo_client["AIResumeAnalyzer"]

users_collection = db["users"]
resumes_collection = db["resumes"]
job_matches_collection = db["job_matches"]
career_chats_collection = db["career_chats"]


# =======================================
# FILE VALIDATION
# =======================================

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# =======================================
# PDF TEXT EXTRACTION
# =======================================

def extract_text_from_pdf(filepath):

    document = fitz.open(filepath)

    text = ""

    for page in document:
        text += page.get_text()

    document.close()

    return text


# =======================================
# ATS SCORE
# =======================================

def calculate_ats_score(resume_text):

    text = resume_text.lower()

    contact = 0

    if re.search(
        r"\b[\w.-]+@[\w.-]+\.\w+\b",
        text
    ):
        contact += 5

    if re.search(
        r"\b(?:\+91[-\s]?)?[6-9]\d{9}\b",
        text
    ):
        contact += 5


    education_words = [
        "education",
        "b.tech",
        "btech",
        "bachelor",
        "degree",
        "university",
        "college",
        "cgpa"
    ]

    education = min(
        10,
        sum(
            word in text
            for word in education_words
        ) * 2
    )


    skills = [
        "python",
        "java",
        "javascript",
        "html",
        "css",
        "sql",
        "mongodb",
        "mysql",
        "flask",
        "django",
        "react",
        "node.js",
        "git",
        "github",
        "c++",
        "c",
        "machine learning",
        "deep learning",
        "artificial intelligence",
        "aws",
        "docker"
    ]

    matched_skills = [
        skill
        for skill in skills
        if skill in text
    ]

    technical_skills = min(
        20,
        len(matched_skills) * 2
    )


    project_words = [
        "project",
        "projects",
        "developed",
        "built",
        "implemented",
        "application"
    ]

    project_hits = sum(
        word in text
        for word in project_words
    )

    projects = min(
        15,
        project_hits * 3
    )


    experience_words = [
        "experience",
        "internship",
        "intern",
        "employment",
        "developer",
        "worked"
    ]

    experience_hits = sum(
        word in text
        for word in experience_words
    )

    experience = min(
        15,
        experience_hits * 3
    )


    certification_words = [
        "certification",
        "certifications",
        "certificate",
        "certified"
    ]

    certifications = 5 if any(
        word in text
        for word in certification_words
    ) else 0


    achievement_words = [
        "achievement",
        "achievements",
        "award",
        "hackathon",
        "competition"
    ]

    achievements = 5 if any(
        word in text
        for word in achievement_words
    ) else 0


    sections = [
        "summary",
        "objective",
        "skills",
        "education",
        "projects",
        "experience",
        "certifications"
    ]

    section_count = sum(
        section in text
        for section in sections
    )

    structure = min(
        10,
        section_count + 3
    )


    word_count = len(text.split())

    if word_count >= 700:
        content = 10
    elif word_count >= 500:
        content = 8
    elif word_count >= 300:
        content = 6
    elif word_count >= 150:
        content = 4
    else:
        content = 2


    total_score = (
        contact
        + education
        + technical_skills
        + projects
        + experience
        + certifications
        + achievements
        + structure
        + content
    )


    details = {
        "Contact Information": contact,
        "Education": education,
        "Technical Skills": technical_skills,
        "Projects": projects,
        "Experience": experience,
        "Certifications": certifications,
        "Achievements": achievements,
        "Resume Structure": structure,
        "Content Quality": content
    }

    return min(total_score, 100), details


# =======================================
# AI RESUME ANALYSIS
# =======================================

def analyze_resume(resume_text, ats_score):

    prompt = f"""
You are an expert resume reviewer.

The resume has already received a fixed ATS score
of {ats_score}/100.

Do NOT calculate another score.

Analyze the resume and provide:

1. Resume Summary
2. Technical Skills
3. Soft Skills
4. Strengths
5. Weaknesses
6. Missing Skills
7. Resume Improvement Suggestions

Be specific and useful.

Resume:

{resume_text}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": "You are an expert resume reviewer."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content


# =======================================
# JOB MATCH SCORE
# =======================================

def calculate_job_match(resume_text, job_description):

    resume = resume_text.lower()
    job = job_description.lower()

    skills = [
        "python",
        "java",
        "c++",
        "c",
        "javascript",
        "html",
        "css",
        "sql",
        "mysql",
        "mongodb",
        "flask",
        "django",
        "react",
        "node.js",
        "git",
        "github",
        "docker",
        "aws",
        "machine learning",
        "deep learning",
        "artificial intelligence",
        "data structures",
        "algorithms",
        "rest api",
        "fastapi",
        "pandas",
        "numpy",
        "tensorflow",
        "pytorch"
    ]

    required_skills = [
        skill
        for skill in skills
        if skill in job
    ]

    matched_skills = [
        skill
        for skill in required_skills
        if skill in resume
    ]

    missing_skills = [
        skill
        for skill in required_skills
        if skill not in resume
    ]

    if required_skills:

        skill_score = round(
            (
                len(matched_skills)
                / len(required_skills)
            ) * 70
        )

    else:

        skill_score = 0


    relevant_sections = [
        "education",
        "project",
        "experience",
        "certification"
    ]

    section_count = sum(
        section in resume
        for section in relevant_sections
    )

    section_score = min(
        20,
        section_count * 5
    )


    role_keywords = [
        "developer",
        "engineer",
        "software",
        "programming",
        "technology"
    ]

    keyword_matches = sum(
        word in job and word in resume
        for word in role_keywords
    )

    keyword_score = min(
        10,
        keyword_matches * 2
    )


    match_score = min(
        100,
        skill_score
        + section_score
        + keyword_score
    )

    return (
        match_score,
        matched_skills,
        missing_skills
    )


# =======================================
# AI JOB ANALYSIS
# =======================================

def analyze_job_match(resume_text, job_description):

    prompt = f"""
You are an expert career assistant.

Compare the resume with the job description.

Do NOT generate a match score.

Provide:

1. Matched Skills
2. Missing Skills
3. Matching Strengths
4. Skill Gap
5. Application Recommendation

Be specific and practical.

Resume:

{resume_text}

Job Description:

{job_description}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": "You are an expert career assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content


# =======================================
# AI CAREER ASSISTANT
# =======================================

def career_assistant(resume_text, question):

    prompt = f"""
You are an expert AI Career Assistant.

Use the candidate's resume to answer the question.

Give practical, honest and personalized advice.

Do not invent information that is not present
in the resume.

Candidate Resume:

{resume_text}

User Question:

{question}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": "You are an expert career advisor."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content


# =======================================
# HOME
# =======================================

@app.route("/")
def home():

    return render_template("index.html")


# =======================================
# SIGNUP
# =======================================

@app.route("/signup")
def signup_page():

    return render_template("signup.html")


@app.route("/signup", methods=["POST"])
def signup():

    name = request.form.get(
        "name",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    password = request.form.get(
        "password",
        ""
    )


    if not name or not email or not password:

        return render_template(
            "signup.html",
            error="Please fill in all fields."
        )


    existing_user = users_collection.find_one(
        {"email": email}
    )


    if existing_user:

        return render_template(
            "signup.html",
            error="An account with this email already exists."
        )


    hashed_password = generate_password_hash(
        password
    )


    user = {
        "name": name,
        "email": email,
        "password": hashed_password,
        "created_at": datetime.utcnow()
    }


    result = users_collection.insert_one(
        user
    )


    session["user_id"] = str(
        result.inserted_id
    )

    session["user_name"] = name
    session["user_email"] = email


    return redirect(
        url_for("dashboard")
    )


# =======================================
# LOGIN
# =======================================

@app.route("/login")
def login_page():

    return render_template(
        "login.html"
    )


@app.route("/login", methods=["POST"])
def login():

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    password = request.form.get(
        "password",
        ""
    )


    user = users_collection.find_one(
        {"email": email}
    )


    if not user:

        return render_template(
            "login.html",
            error="Invalid email or password."
        )


    if not check_password_hash(
        user["password"],
        password
    ):

        return render_template(
            "login.html",
            error="Invalid email or password."
        )


    session["user_id"] = str(
        user["_id"]
    )

    session["user_name"] = user["name"]
    session["user_email"] = user["email"]


    return redirect(
        url_for("dashboard")
    )


# =======================================
# LOGOUT
# =======================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# =======================================
# DASHBOARD
# =======================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login_page")
        )


    user_id = session["user_id"]


    user_resumes = list(
        resumes_collection.find(
            {"user_id": user_id}
        ).sort(
            "created_at",
            -1
        ).limit(5)
    )


    user_job_matches = list(
        job_matches_collection.find(
            {"user_id": user_id}
        ).sort(
            "created_at",
            -1
        ).limit(5)
    )


    user_career_chats = list(
        career_chats_collection.find(
            {"user_id": user_id}
        ).sort(
            "created_at",
            -1
        ).limit(5)
    )


    latest_score = None

    if user_resumes:

        latest_score = user_resumes[0].get(
            "ats_score"
        )


    return render_template(

        "dashboard.html",

        user_name=session.get(
            "user_name"
        ),

        latest_score=latest_score,

        resume_count=len(
            user_resumes
        ),

        job_match_count=len(
            user_job_matches
        ),

        career_chat_count=len(
            user_career_chats
        ),

        resume_history=user_resumes,

        job_history=user_job_matches,

        career_history=user_career_chats

    )


# =======================================
# RESUME UPLOAD
# =======================================

@app.route(
    "/upload",
    methods=["POST"]
)
def upload_resume():

    if "user_id" not in session:

        return redirect(
            url_for("login_page")
        )


    if "resume" not in request.files:

        return "No resume selected"


    file = request.files["resume"]


    if file.filename == "":

        return "No resume selected"


    if not allowed_file(
        file.filename
    ):

        return "Only PDF files are allowed"


    filename = secure_filename(
        file.filename
    )


    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )


    file.save(filepath)


    resume_text = extract_text_from_pdf(
        filepath
    )


    ats_score, score_details = calculate_ats_score(
        resume_text
    )


    try:

        analysis = analyze_resume(
            resume_text,
            ats_score
        )


        resume_record = {

            "user_id": session["user_id"],

            "filename": filename,

            "ats_score": ats_score,

            "score_details": score_details,

            "analysis": analysis,

            "created_at": datetime.utcnow()

        }


        resumes_collection.insert_one(
            resume_record
        )


        return render_template(

            "analysis.html",

            analysis=analysis,

            score=ats_score,

            score_details=score_details

        )


    except Exception as e:

        print(
            "AI ERROR:",
            e
        )


        return render_template(

            "analysis.html",

            analysis=
            "AI explanation could not be generated.",

            score=ats_score,

            score_details=score_details

        )


# =======================================
# JOB MATCH PAGE
# =======================================

@app.route("/job-match")
def job_match():

    if "user_id" not in session:

        return redirect(
            url_for("login_page")
        )


    return render_template(
        "job_match.html"
    )


# =======================================
# PROCESS JOB MATCH
# =======================================

@app.route(
    "/job-match",
    methods=["POST"]
)
def process_job_match():

    if "user_id" not in session:

        return redirect(
            url_for("login_page")
        )


    job_description = request.form.get(
        "job_description"
    )


    if not job_description:

        return (
            "Please enter a job description."
        )


    pdf_files = [

        file

        for file in os.listdir(
            UPLOAD_FOLDER
        )

        if file.lower().endswith(".pdf")

    ]


    if not pdf_files:

        return (
            "Please upload your resume first."
        )


    latest_resume = max(

        pdf_files,

        key=lambda file:

        os.path.getmtime(

            os.path.join(
                UPLOAD_FOLDER,
                file
            )

        )

    )


    filepath = os.path.join(

        UPLOAD_FOLDER,

        latest_resume

    )


    resume_text = extract_text_from_pdf(
        filepath
    )


    (
        match_score,
        matched_skills,
        missing_skills

    ) = calculate_job_match(

        resume_text,

        job_description

    )


    try:

        result = analyze_job_match(

            resume_text,

            job_description

        )


        job_match_record = {

            "user_id": session["user_id"],

            "resume_filename": latest_resume,

            "job_description": job_description,

            "match_score": match_score,

            "matched_skills": matched_skills,

            "missing_skills": missing_skills,

            "analysis": result,

            "created_at": datetime.utcnow()

        }


        job_matches_collection.insert_one(
            job_match_record
        )


        return render_template(

            "job_result.html",

            result=result,

            match_score=match_score,

            matched_skills=matched_skills,

            missing_skills=missing_skills

        )


    except Exception as e:

        return (
            f"Job matching failed: {str(e)}"
        )


# =======================================
# CAREER ASSISTANT PAGE
# =======================================

@app.route(
    "/career-assistant"
)
def career_assistant_page():

    if "user_id" not in session:

        return redirect(
            url_for("login_page")
        )


    return render_template(
        "career_assistant.html"
    )


# =======================================
# PROCESS CAREER ASSISTANT
# =======================================

@app.route(
    "/career-assistant",
    methods=["POST"]
)
def process_career_assistant():

    if "user_id" not in session:

        return redirect(
            url_for("login_page")
        )


    question = request.form.get(
        "question"
    )


    if not question:

        return "Please enter a question."


    pdf_files = [

        file

        for file in os.listdir(
            UPLOAD_FOLDER
        )

        if file.lower().endswith(".pdf")

    ]


    if not pdf_files:

        return (
            "Please upload your resume first."
        )


    latest_resume = max(

        pdf_files,

        key=lambda file:

        os.path.getmtime(

            os.path.join(
                UPLOAD_FOLDER,
                file
            )

        )

    )


    filepath = os.path.join(

        UPLOAD_FOLDER,

        latest_resume

    )


    resume_text = extract_text_from_pdf(
        filepath
    )


    try:

        answer = career_assistant(

            resume_text,

            question

        )


        career_record = {

            "user_id": session["user_id"],

            "resume_filename": latest_resume,

            "question": question,

            "answer": answer,

            "created_at": datetime.utcnow()

        }


        career_chats_collection.insert_one(
            career_record
        )


        return render_template(

            "career_assistant.html",

            answer=answer

        )


    except Exception as e:

        return (
            f"Career Assistant failed: {str(e)}"
        )


# =======================================
# START APPLICATION
# =======================================

if __name__ == "__main__":

    try:

        mongo_client.admin.command(
            "ping"
        )

        print(
            "MongoDB connected successfully!"
        )

    except Exception as e:

        print(
            "MongoDB connection failed:"
        )

        print(e)


    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )