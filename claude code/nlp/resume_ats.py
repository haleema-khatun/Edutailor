import re

REQUIRED_KEYWORDS = [
    "python", "machine learning", "data analysis",
    "sql", "flask", "project", "teamwork",
    "communication", "problem solving"
]

ACTION_VERBS = [
    "developed", "implemented", "designed",
    "built", "optimized", "analyzed", "created"
]

def analyze_resume(text):
    text_lower = text.lower()

    matched = []
    missing = []

    for keyword in REQUIRED_KEYWORDS:
        if keyword in text_lower:
            matched.append(keyword)
        else:
            missing.append(keyword)

    ats_score = int((len(matched) / len(REQUIRED_KEYWORDS)) * 100)

    improvements = []

    # Specific improvement suggestions
    for word in missing:
        if word == "flask":
            improvements.append("Add backend framework experience such as Flask or Django.")
        elif word == "teamwork":
            improvements.append("Include examples of teamwork or collaboration in projects.")
        elif word == "problem solving":
            improvements.append("Mention problem-solving achievements with measurable impact.")
        elif word == "data analysis":
            improvements.append("Add data analysis tools like Pandas, NumPy, or visualization tools.")
        else:
            improvements.append(f"Include experience related to '{word}'.")

    # Check for action verbs
    if not any(verb in text_lower for verb in ACTION_VERBS):
        improvements.append("Use strong action verbs like 'Developed', 'Built', 'Implemented'.")

    # Check for measurable results (numbers, %, etc.)
    if not re.search(r"\d+%|\d+\s?(users|projects|clients)", text_lower):
        improvements.append("Add measurable achievements (e.g., improved accuracy by 20%).")

    # Length check
    word_count = len(text.split())
    if word_count < 300:
        improvements.append("Resume is too short. Add more project details and technical skills.")
    elif word_count > 800:
        improvements.append("Resume is too long. Keep it concise (1-2 pages).")

    return {
        "ATS Score": ats_score,
        "Matched Keywords": matched,
        "Missing Keywords": missing,
        "Improvements": improvements
    }
