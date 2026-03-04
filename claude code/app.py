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

import random

# -------------------- QUIZ QUESTION BANK (10 per subject) --------------------

QUIZ_BANK = {
    "Python": [
        {"q": "What is the output of print(type([]))?", "options": ["<class 'list'>", "<class 'tuple'>", "<class 'dict'>", "<class 'set'>"], "answer": 0},
        {"q": "Which keyword is used to define a function in Python?", "options": ["func", "define", "def", "function"], "answer": 2},
        {"q": "What does 'len()' function do?", "options": ["Returns data type", "Returns length", "Returns index", "Returns value"], "answer": 1},
        {"q": "Which of these is immutable in Python?", "options": ["List", "Dictionary", "Set", "Tuple"], "answer": 3},
        {"q": "What is the correct file extension for Python files?", "options": [".pyth", ".pt", ".py", ".pyt"], "answer": 2},
        {"q": "What does 'pip' stand for?", "options": ["Python Install Package", "Pip Installs Packages", "Package in Python", "Python Integrated Platform"], "answer": 1},
        {"q": "Which method adds an element to the end of a list?", "options": ["add()", "insert()", "append()", "push()"], "answer": 2},
        {"q": "What is a dictionary in Python?", "options": ["Ordered sequence", "Key-value pairs", "Immutable list", "Set of numbers"], "answer": 1},
        {"q": "How do you start a comment in Python?", "options": ["//", "/*", "#", "--"], "answer": 2},
        {"q": "What is the output of bool('')?", "options": ["True", "False", "None", "Error"], "answer": 1},
    ],
    "Java": [
        {"q": "Which method is the entry point of a Java program?", "options": ["start()", "main()", "run()", "init()"], "answer": 1},
        {"q": "Java is a ___-oriented programming language.", "options": ["Procedure", "Object", "Function", "Logic"], "answer": 1},
        {"q": "Which keyword is used to inherit a class in Java?", "options": ["implements", "extends", "inherits", "super"], "answer": 1},
        {"q": "What is the size of int in Java?", "options": ["2 bytes", "4 bytes", "8 bytes", "Depends on OS"], "answer": 1},
        {"q": "Which of these is not a Java feature?", "options": ["Object-oriented", "Portable", "Pointers", "Multithreaded"], "answer": 2},
        {"q": "What is JVM?", "options": ["Java Virtual Machine", "Java Version Manager", "Java Variable Method", "Java Verified Module"], "answer": 0},
        {"q": "Which collection allows duplicate elements?", "options": ["Set", "HashSet", "ArrayList", "TreeSet"], "answer": 2},
        {"q": "What is encapsulation?", "options": ["Hiding data within a class", "Inheriting properties", "Method overloading", "Creating objects"], "answer": 0},
        {"q": "Which keyword prevents a class from being inherited?", "options": ["static", "final", "abstract", "private"], "answer": 1},
        {"q": "What is the parent class of all Java classes?", "options": ["Main", "Object", "Class", "Super"], "answer": 1},
    ],
    "JavaScript": [
        {"q": "Which company developed JavaScript?", "options": ["Microsoft", "Netscape", "Google", "Apple"], "answer": 1},
        {"q": "What does 'typeof null' return in JavaScript?", "options": ["'null'", "'undefined'", "'object'", "'boolean'"], "answer": 2},
        {"q": "Which method converts JSON to a JavaScript object?", "options": ["JSON.stringify()", "JSON.parse()", "JSON.convert()", "JSON.toObject()"], "answer": 1},
        {"q": "What is '===' in JavaScript?", "options": ["Assignment", "Loose equality", "Strict equality", "Not equal"], "answer": 2},
        {"q": "Which keyword declares a block-scoped variable?", "options": ["var", "let", "both var and let", "none"], "answer": 1},
        {"q": "What is a closure in JavaScript?", "options": ["A loop structure", "A function with access to outer scope", "An error handler", "A class definition"], "answer": 1},
        {"q": "Which method removes the last element of an array?", "options": ["shift()", "pop()", "splice()", "delete()"], "answer": 1},
        {"q": "What is 'NaN' in JavaScript?", "options": ["Not a Number", "Null and None", "New Array Number", "No assigned Name"], "answer": 0},
        {"q": "What does 'async' keyword do?", "options": ["Makes function synchronous", "Makes function return a Promise", "Stops execution", "Creates a thread"], "answer": 1},
        {"q": "Which event fires when DOM is fully loaded?", "options": ["onload", "DOMContentLoaded", "ready", "onstart"], "answer": 1},
    ],
    "C++": [
        {"q": "Who developed C++?", "options": ["Dennis Ritchie", "Bjarne Stroustrup", "James Gosling", "Guido van Rossum"], "answer": 1},
        {"q": "Which symbol is used for single-line comments in C++?", "options": ["/* */", "//", "#", "--"], "answer": 1},
        {"q": "What is the correct syntax to output text in C++?", "options": ["print()", "console.log()", "cout <<", "System.out.println()"], "answer": 2},
        {"q": "Which of these is used for dynamic memory allocation in C++?", "options": ["malloc", "new", "alloc", "create"], "answer": 1},
        {"q": "C++ supports which programming paradigm?", "options": ["Only procedural", "Only OOP", "Multi-paradigm", "Only functional"], "answer": 2},
        {"q": "What is a virtual function?", "options": ["A function with no body", "A function that can be overridden", "A static function", "A private function"], "answer": 1},
        {"q": "What does STL stand for?", "options": ["Standard Template Library", "System Type Library", "Static Template Loader", "Structured Type Language"], "answer": 0},
        {"q": "Which operator is used for scope resolution?", "options": [".", "->", "::", ":"], "answer": 2},
        {"q": "What is a destructor?", "options": ["Creates an object", "Destroys an object", "Copies an object", "Moves an object"], "answer": 1},
        {"q": "What is polymorphism?", "options": ["Single form", "Many forms", "No form", "Static form"], "answer": 1},
    ],
    "Machine Learning": [
        {"q": "Which type of learning uses labeled data?", "options": ["Unsupervised", "Supervised", "Reinforcement", "Semi-supervised"], "answer": 1},
        {"q": "What does 'overfitting' mean?", "options": ["Model is too simple", "Model memorizes training data", "Model ignores data", "Model is perfect"], "answer": 1},
        {"q": "Which algorithm is used for classification?", "options": ["Linear Regression", "K-Means", "Decision Tree", "PCA"], "answer": 2},
        {"q": "What is a 'feature' in machine learning?", "options": ["Output variable", "Input variable", "Algorithm name", "Loss function"], "answer": 1},
        {"q": "Which metric is used for regression problems?", "options": ["Accuracy", "F1-Score", "Mean Squared Error", "Precision"], "answer": 2},
        {"q": "What is cross-validation?", "options": ["Training once", "Splitting data for train/test multiple times", "Increasing epochs", "Removing features"], "answer": 1},
        {"q": "What is the bias-variance tradeoff?", "options": ["Speed vs accuracy", "Underfitting vs overfitting balance", "Training vs test split", "CPU vs GPU usage"], "answer": 1},
        {"q": "Which is an ensemble method?", "options": ["Linear Regression", "Random Forest", "K-Nearest Neighbors", "Naive Bayes"], "answer": 1},
        {"q": "What is gradient descent?", "options": ["A data structure", "An optimization algorithm", "A loss function", "A regularization technique"], "answer": 1},
        {"q": "What does 'regularization' prevent?", "options": ["Underfitting", "Overfitting", "Data loss", "Slow training"], "answer": 1},
    ],
    "Deep Learning": [
        {"q": "What is the basic unit of a neural network?", "options": ["Layer", "Neuron", "Weight", "Bias"], "answer": 1},
        {"q": "Which activation function outputs values between 0 and 1?", "options": ["ReLU", "Tanh", "Sigmoid", "Softmax"], "answer": 2},
        {"q": "CNN stands for?", "options": ["Central Neural Network", "Convolutional Neural Network", "Connected Node Network", "Computed Neural Net"], "answer": 1},
        {"q": "Which framework was developed by Google for deep learning?", "options": ["PyTorch", "Keras", "TensorFlow", "Caffe"], "answer": 2},
        {"q": "What is 'backpropagation' used for?", "options": ["Data preprocessing", "Updating weights", "Feature extraction", "Data augmentation"], "answer": 1},
        {"q": "What is a 'dropout' layer?", "options": ["Adds neurons", "Randomly disables neurons during training", "Increases learning rate", "Normalizes data"], "answer": 1},
        {"q": "RNN stands for?", "options": ["Random Neural Network", "Recurrent Neural Network", "Recursive Node Network", "Reduced Neural Net"], "answer": 1},
        {"q": "What is transfer learning?", "options": ["Training from scratch", "Using pre-trained model for new task", "Moving data between servers", "Converting models"], "answer": 1},
        {"q": "What is an epoch?", "options": ["One batch of data", "One pass through entire dataset", "One neuron update", "One layer forward"], "answer": 1},
        {"q": "What is vanishing gradient problem?", "options": ["Gradients become too large", "Gradients become too small", "Gradients become zero", "Gradients oscillate"], "answer": 1},
    ],
    "NLP": [
        {"q": "NLP stands for?", "options": ["Neural Language Processing", "Natural Language Processing", "Network Language Protocol", "Natural Logic Programming"], "answer": 1},
        {"q": "What is 'tokenization' in NLP?", "options": ["Removing stop words", "Splitting text into tokens", "Stemming words", "Encoding text"], "answer": 1},
        {"q": "Which model introduced the 'Attention' mechanism?", "options": ["LSTM", "GRU", "Transformer", "RNN"], "answer": 2},
        {"q": "What is 'stemming'?", "options": ["Adding prefixes", "Reducing words to root form", "Translating text", "Parsing sentences"], "answer": 1},
        {"q": "BERT was developed by?", "options": ["Facebook", "OpenAI", "Google", "Microsoft"], "answer": 2},
        {"q": "What is TF-IDF?", "options": ["A neural network", "A term frequency measure", "A language model", "A tokenizer"], "answer": 1},
        {"q": "What is Named Entity Recognition?", "options": ["Finding sentiments", "Identifying entities like names and places", "Translating text", "Summarizing text"], "answer": 1},
        {"q": "What is Word2Vec?", "options": ["A tokenizer", "Word embedding technique", "Language model", "Text classifier"], "answer": 1},
        {"q": "What is sentiment analysis?", "options": ["Grammar checking", "Determining emotion/opinion in text", "Word counting", "Language detection"], "answer": 1},
        {"q": "GPT stands for?", "options": ["General Processing Tool", "Generative Pre-trained Transformer", "Global Pattern Tracker", "Gradient Path Technique"], "answer": 1},
    ],
    "DSA": [
        {"q": "What is the time complexity of binary search?", "options": ["O(n)", "O(log n)", "O(n\u00b2)", "O(1)"], "answer": 1},
        {"q": "Which data structure uses FIFO?", "options": ["Stack", "Queue", "Tree", "Graph"], "answer": 1},
        {"q": "What is the worst-case time complexity of quicksort?", "options": ["O(n log n)", "O(n\u00b2)", "O(n)", "O(log n)"], "answer": 1},
        {"q": "Which data structure is used for BFS?", "options": ["Stack", "Queue", "Heap", "Array"], "answer": 1},
        {"q": "A balanced BST has height of?", "options": ["O(n)", "O(log n)", "O(n\u00b2)", "O(1)"], "answer": 1},
        {"q": "What is a hash table's average lookup time?", "options": ["O(n)", "O(log n)", "O(1)", "O(n\u00b2)"], "answer": 2},
        {"q": "Which sorting algorithm is stable?", "options": ["Quick Sort", "Heap Sort", "Merge Sort", "Selection Sort"], "answer": 2},
        {"q": "What is dynamic programming?", "options": ["Random approach", "Breaking problem into overlapping subproblems", "Brute force", "Greedy approach"], "answer": 1},
        {"q": "Which data structure uses LIFO?", "options": ["Queue", "Stack", "Array", "Linked List"], "answer": 1},
        {"q": "What is the space complexity of merge sort?", "options": ["O(1)", "O(log n)", "O(n)", "O(n\u00b2)"], "answer": 2},
    ],
    "DBMS": [
        {"q": "SQL stands for?", "options": ["Structured Query Language", "Simple Query Language", "Standard Query Logic", "Sequential Query Language"], "answer": 0},
        {"q": "Which normal form removes partial dependencies?", "options": ["1NF", "2NF", "3NF", "BCNF"], "answer": 1},
        {"q": "What does ACID stand for in databases?", "options": ["Atomicity, Consistency, Isolation, Durability", "Access, Control, Integrity, Data", "Atomicity, Control, Isolation, Data", "Access, Consistency, Integrity, Durability"], "answer": 0},
        {"q": "Which command is used to retrieve data from a database?", "options": ["GET", "FETCH", "SELECT", "RETRIEVE"], "answer": 2},
        {"q": "A primary key must be?", "options": ["Null", "Duplicate", "Unique and not null", "Only numeric"], "answer": 2},
        {"q": "What is a foreign key?", "options": ["Unique identifier", "References primary key of another table", "Auto-increment field", "Index column"], "answer": 1},
        {"q": "What is a JOIN in SQL?", "options": ["Deletes tables", "Combines rows from multiple tables", "Creates a table", "Drops a column"], "answer": 1},
        {"q": "What is normalization?", "options": ["Adding redundancy", "Reducing data redundancy", "Encrypting data", "Backing up data"], "answer": 1},
        {"q": "Which SQL clause filters grouped results?", "options": ["WHERE", "HAVING", "GROUP BY", "ORDER BY"], "answer": 1},
        {"q": "What is an index in a database?", "options": ["A table type", "Speeds up data retrieval", "A constraint", "A relationship"], "answer": 1},
    ],
    "Operating Systems": [
        {"q": "Which scheduling algorithm is non-preemptive?", "options": ["Round Robin", "FCFS", "SRTF", "Priority (preemptive)"], "answer": 1},
        {"q": "What is a 'deadlock'?", "options": ["Fast execution", "Processes waiting for each other indefinitely", "Memory overflow", "CPU idle state"], "answer": 1},
        {"q": "What does 'virtual memory' do?", "options": ["Increases RAM physically", "Extends memory using disk", "Compresses files", "Speeds up CPU"], "answer": 1},
        {"q": "Which memory allocation strategy is 'best fit'?", "options": ["Allocates first available block", "Allocates smallest sufficient block", "Allocates largest block", "Random allocation"], "answer": 1},
        {"q": "What is a 'semaphore' used for?", "options": ["Memory management", "Process synchronization", "File management", "Disk scheduling"], "answer": 1},
        {"q": "What is paging?", "options": ["Memory management technique", "CPU scheduling", "Disk formatting", "Process creation"], "answer": 0},
        {"q": "What is a thread?", "options": ["A heavy process", "Lightweight process", "A file system", "A network protocol"], "answer": 1},
        {"q": "What is thrashing?", "options": ["Fast processing", "Excessive paging reducing performance", "Memory leak", "CPU overclocking"], "answer": 1},
        {"q": "What are the conditions for deadlock?", "options": ["Mutual exclusion only", "Mutual exclusion, hold and wait, no preemption, circular wait", "Only circular wait", "Only no preemption"], "answer": 1},
        {"q": "What is a context switch?", "options": ["Changing user", "Saving/restoring process state", "Installing OS", "Formatting disk"], "answer": 1},
    ],
    "Web Development": [
        {"q": "HTML stands for?", "options": ["Hyper Text Markup Language", "High Tech Modern Language", "Hyper Transfer Markup Language", "Home Tool Markup Language"], "answer": 0},
        {"q": "Which CSS property changes text color?", "options": ["font-color", "text-color", "color", "foreground"], "answer": 2},
        {"q": "What does API stand for?", "options": ["Application Programming Interface", "Applied Program Integration", "Application Process Interface", "Automated Programming Interface"], "answer": 0},
        {"q": "Which HTTP method is used to update a resource?", "options": ["GET", "POST", "PUT", "DELETE"], "answer": 2},
        {"q": "What is responsive design?", "options": ["Fast loading", "Adapting to screen sizes", "Using animations", "Server-side rendering"], "answer": 1},
        {"q": "What is the DOM?", "options": ["Database Object Model", "Document Object Model", "Digital Output Module", "Data Operation Manager"], "answer": 1},
        {"q": "What is CORS?", "options": ["Code Optimization Resource System", "Cross-Origin Resource Sharing", "Central Object Request Service", "Client-Oriented Response System"], "answer": 1},
        {"q": "What is a REST API?", "options": ["A database", "An architectural style for web services", "A frontend framework", "A testing tool"], "answer": 1},
        {"q": "What does CSS Box Model include?", "options": ["Only padding", "Content, padding, border, margin", "Only margin", "Only border"], "answer": 1},
        {"q": "What is a cookie in web development?", "options": ["A virus", "Small data stored in browser", "A server type", "A CSS property"], "answer": 1},
    ],
    "Git & DevOps": [
        {"q": "What command initializes a Git repository?", "options": ["git start", "git init", "git create", "git new"], "answer": 1},
        {"q": "What does 'git clone' do?", "options": ["Deletes a repo", "Creates a copy of a repo", "Merges branches", "Pushes changes"], "answer": 1},
        {"q": "Docker containers are based on?", "options": ["Virtual machines", "Images", "Snapshots", "Volumes"], "answer": 1},
        {"q": "What is CI/CD?", "options": ["Code Integration/Code Deployment", "Continuous Integration/Continuous Delivery", "Central Integration/Central Delivery", "Compiled Integration/Compiled Deployment"], "answer": 1},
        {"q": "Which command shows the commit history?", "options": ["git status", "git log", "git diff", "git show"], "answer": 1},
        {"q": "What does 'git merge' do?", "options": ["Deletes a branch", "Combines two branches", "Creates a branch", "Reverts changes"], "answer": 1},
        {"q": "What is a Dockerfile?", "options": ["A log file", "Instructions to build a Docker image", "A config for Git", "A database file"], "answer": 1},
        {"q": "What is Kubernetes used for?", "options": ["Version control", "Container orchestration", "Code compilation", "Database management"], "answer": 1},
        {"q": "What does 'git stash' do?", "options": ["Deletes changes", "Temporarily saves uncommitted changes", "Pushes to remote", "Creates a tag"], "answer": 1},
        {"q": "What is a Git branch?", "options": ["A copy of the server", "An independent line of development", "A backup file", "A commit message"], "answer": 1},
    ],
}

# -------------------- QUIZ --------------------

@app.route("/quiz", methods=["GET", "POST"])
@login_required
def quiz():
    if request.method == "POST":
        subject = request.form.get("subject", "")
        if subject not in QUIZ_BANK:
            flash("Invalid subject selected.", "error")
            return redirect(url_for("quiz"))

        questions = QUIZ_BANK[subject]
        correct = 0
        total = len(questions)
        results = []

        for i, q in enumerate(questions):
            user_ans = request.form.get(f"q{i}", "-1")
            try:
                user_ans = int(user_ans)
            except ValueError:
                user_ans = -1

            is_correct = user_ans == q["answer"]
            if is_correct:
                correct += 1

            results.append({
                "question": q["q"],
                "options": q["options"],
                "user_answer": user_ans,
                "correct_answer": q["answer"],
                "is_correct": is_correct,
            })

        score = round((correct / total) * 100)

        # Save quiz score to DB
        user_id = session.get("user_id")
        if user_id:
            save_progress(user_id, "quiz", subject, score)

        return render_template(
            "quiz.html",
            subjects=ALL_SUBJECTS,
            selected_subject=subject,
            questions=None,
            results=results,
            score=score,
            correct=correct,
            total=total,
            show_results=True,
        )

    # GET — check if subject param provided
    subject = request.args.get("subject", "")

    if subject and subject in QUIZ_BANK:
        questions = QUIZ_BANK[subject]
        return render_template(
            "quiz.html",
            subjects=ALL_SUBJECTS,
            selected_subject=subject,
            questions=questions,
            results=None,
            show_results=False,
        )

    return render_template(
        "quiz.html",
        subjects=ALL_SUBJECTS,
        selected_subject=None,
        questions=None,
        results=None,
        show_results=False,
    )


# -------------------- RUN APP --------------------

if __name__ == "__main__":
    app.run(debug=True)
