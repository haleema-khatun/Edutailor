from utils.voice_interview import speak, listen
from nlp.interview_agent import generate_question, analyze_answer
import sqlite3
import os
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from docx import Document
from PyPDF2 import PdfReader

from nlp.resume_ats import analyze_resume
from nlp.interview_analyzer import analyze_interview
from models.skill_model import analyze_skills
from utils.pdf_report import generate_pdf
from utils.db import init_db, create_user, verify_user, save_progress, get_progress_summary

# -------------------- APP SETUP --------------------

app = Flask(__name__)
app.secret_key = "career_ai_secret_2025_upgraded"

# Upload folder setup
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Initialize database on startup
with app.app_context():
    init_db()

# -------------------- LOGIN REQUIRED DECORATOR --------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# -------------------- EXPANDED RESOURCE MAP (12 Subjects) --------------------

RESOURCE_MAP = {
    # Programming Languages
    "Python": [
        "https://docs.python.org/3/tutorial/",
        "https://www.w3schools.com/python/",
        "https://realpython.com/"
    ],
    "Java": [
        "https://docs.oracle.com/javase/tutorial/",
        "https://www.w3schools.com/java/",
        "https://www.javatpoint.com/java-tutorial"
    ],
    "JavaScript": [
        "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide",
        "https://javascript.info/",
        "https://www.w3schools.com/js/"
    ],
    "C++": [
        "https://www.learncpp.com/",
        "https://www.w3schools.com/cpp/",
        "https://cplusplus.com/doc/tutorial/"
    ],

    # AI & ML
    "Machine Learning": [
        "https://www.coursera.org/learn/machine-learning",
        "https://scikit-learn.org/stable/tutorial/",
        "https://www.kaggle.com/learn/intro-to-machine-learning"
    ],
    "Deep Learning": [
        "https://www.deeplearning.ai/",
        "https://pytorch.org/tutorials/",
        "https://www.tensorflow.org/tutorials"
    ],
    "NLP": [
        "https://www.coursera.org/specializations/natural-language-processing",
        "https://huggingface.co/course/",
        "https://spacy.io/usage/spacy-101"
    ],

    # CS Fundamentals
    "DSA": [
        "https://leetcode.com",
        "https://www.geeksforgeeks.org/data-structures/",
        "https://neetcode.io/"
    ],
    "DBMS": [
        "https://www.w3schools.com/sql/",
        "https://www.tutorialspoint.com/dbms/",
        "https://www.javatpoint.com/dbms-tutorial"
    ],
    "Operating Systems": [
        "https://www.geeksforgeeks.org/operating-systems/",
        "https://www.tutorialspoint.com/operating_system/",
        "https://pages.cs.wisc.edu/~remzi/OSTEP/"
    ],

    # Web & Tools
    "Web Development": [
        "https://developer.mozilla.org/en-US/docs/Learn",
        "https://www.freecodecamp.org/",
        "https://www.theodinproject.com/"
    ],
    "Git & DevOps": [
        "https://git-scm.com/doc",
        "https://www.atlassian.com/git/tutorials",
        "https://docs.docker.com/get-started/"
    ]
}

ALL_SUBJECTS = list(RESOURCE_MAP.keys())

# -------------------- HOME --------------------

@app.route("/")
def home():
    return render_template("index.html")

# -------------------- REGISTER --------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return redirect(url_for("register"))

        if password != confirm:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register"))

        success, msg = create_user(username, email, password)
        if success:
            flash(msg, "success")
            return redirect(url_for("login"))
        else:
            flash(msg, "error")
            return redirect(url_for("register"))

    return render_template("register.html")

# -------------------- LOGIN --------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please enter both username and password.", "error")
            return redirect(url_for("login"))

        success, result = verify_user(username, password)
        if success:
            session["user"] = result["username"]
            session["user_id"] = result["id"]
            flash(f"Welcome back, {result['username']}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash(result, "error")
            return redirect(url_for("login"))

    return render_template("login.html")

# -------------------- LOGOUT --------------------

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))

# -------------------- VOICE INTERVIEW --------------------

@app.route("/voice_interview")
@login_required
def voice_interview():
    if "chat" not in session:
        session["chat"] = []

    question = generate_question(session["chat"])
    session["chat"].append({"role": "interviewer", "content": question})
    speak(question)

    answer = listen()
    session["chat"].append({"role": "user", "content": answer})
    session.modified = True

    return redirect("/dashboard")

# -------------------- DASHBOARD --------------------

@app.route("/dashboard")
@login_required
def dashboard():
    stats = get_progress_summary(session.get("user_id"))
    return render_template("dashboard.html", stats=stats)

# -------------------- LEARNING ANALYZER --------------------

def analyze_weak_subjects(scores):
    weak = {}
    for subject, score in scores.items():
        if score < 60:
            weak[subject] = {
                "level": "Weak" if score < 30 else "Needs Improvement",
                "score": score,
                "timeline": "6 Week Intensive Plan" if score < 30 else "4 Weeks Improvement Plan",
                "resources": RESOURCE_MAP.get(subject, [])
            }
    return weak

@app.route("/learning", methods=["GET", "POST"])
@login_required
def learning():
    weak_subjects = {}

    if request.method == "POST":
        scores = {}
        for subject in ALL_SUBJECTS:
            val = request.form.get(subject, "50")
            try:
                scores[subject] = int(val)
            except ValueError:
                scores[subject] = 50

        weak_subjects = analyze_weak_subjects(scores)

        # Save progress for each subject
        user_id = session.get("user_id")
        if user_id:
            for subject, score in scores.items():
                save_progress(user_id, "learning", subject, score)

    return render_template("learning.html", weak_subjects=weak_subjects)

# -------------------- INTERVIEW ANALYZER --------------------

@app.route("/interview", methods=["GET", "POST"])
@login_required
def interview():
    if "chat" not in session:
        session["chat"] = []

        # First question on fresh session
        first_question = generate_question([])
        session["chat"].append({
            "role": "interviewer",
            "content": first_question
        })
        session.modified = True

    if request.method == "POST":
        user_answer = request.form.get("message", "")

        if user_answer.strip():
            # Analyze the answer
            analysis = analyze_answer(user_answer)

            session["chat"].append({
                "role": "user",
                "content": user_answer,
                "analysis": analysis
            })

            # Save interview score
            user_id = session.get("user_id")
            if user_id:
                save_progress(user_id, "interview", "Mock Interview", analysis.get("score", 0))

            # Generate next AI question
            ai_question = generate_question(session["chat"])
            session["chat"].append({
                "role": "interviewer",
                "content": ai_question
            })

            session.modified = True

    return render_template("interview.html", chat=session.get("chat", []))

# -------------------- END INTERVIEW --------------------

@app.route("/end_interview")
@login_required
def end_interview():
    session.pop("chat", None)
    flash("Interview session ended. Great practice!", "success")
    return redirect(url_for("dashboard"))

# -------------------- RESUME ATS CHECKER --------------------

@app.route("/resume", methods=["GET", "POST"])
@login_required
def resume():
    result = {}

    if request.method == "POST":
        file = request.files.get("resume")

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            text = ""

            if filename.endswith(".txt"):
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            elif filename.endswith(".docx"):
                doc = Document(filepath)
                for para in doc.paragraphs:
                    text += para.text + "\n"
            elif filename.endswith(".pdf"):
                reader = PdfReader(filepath)
                for page in reader.pages:
                    text += page.extract_text() or ""
            else:
                flash("Unsupported file format. Please upload PDF, DOCX, or TXT.", "error")
                return redirect(url_for("resume"))

            result = analyze_resume(text)

            # Save resume ATS score
            user_id = session.get("user_id")
            if user_id and result.get("ATS Score"):
                save_progress(user_id, "resume", "ATS Check", result["ATS Score"])

    return render_template("resume.html", result=result)

# -------------------- ANALYTICS --------------------

@app.route("/analytics")
@login_required
def analytics():
    user_id = session.get("user_id")
    summary = get_progress_summary(user_id) if user_id else {
        "total_assessments": 0,
        "avg_score": 0,
        "best_subject": None,
        "category_averages": {},
        "recent": [],
        "subject_scores": {}
    }
    return render_template("analytics.html", summary=summary)

# -------------------- PDF DOWNLOAD --------------------

@app.route("/download")
@login_required
def download():
    user_id = session.get("user_id")
    summary = get_progress_summary(user_id) if user_id else {}
    
    data = summary.get("subject_scores", {})
    if not data:
        data = {"No Data": 0}
    
    pdf = generate_pdf(data)
    return send_file(pdf, as_attachment=True)



# -------------------- RUN APP --------------------

if __name__ == "__main__":
    app.run(debug=True)
