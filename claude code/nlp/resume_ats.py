import re
from openai import OpenAI

# Use API key
client = OpenAI(api_key="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")

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
    """Analyze resume using OpenAI for real, contextual feedback."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert ATS (Applicant Tracking System) resume analyzer. 
Analyze the given resume text and provide:

1. ATS Score (0-100): Based on keyword optimization, formatting quality, action verbs usage, 
   quantifiable achievements, and overall structure.
2. Matched Keywords: List of relevant technical/professional keywords found in the resume.
3. Missing Keywords: Important keywords that should be added for a software developer role.
4. Improvements: 3-6 specific, actionable improvement suggestions.

Respond in this exact JSON format (no markdown, just raw JSON):
{
    "ATS Score": 72,
    "Matched Keywords": ["python", "sql", "project"],
    "Missing Keywords": ["machine learning", "teamwork"],
    "Improvements": [
        "Add measurable achievements with specific numbers",
        "Include more technical skills relevant to target role",
        "Use stronger action verbs at the start of bullet points"
    ]
}"""
                },
                {
                    "role": "user",
                    "content": f"Analyze this resume:\n\n{text}"
                }
            ],
            temperature=0.3
        )

        import json
        result_text = response.choices[0].message.content.strip()
        # Clean up any markdown formatting
        if result_text.startswith("```"):
            result_text = result_text.split("\n", 1)[1]
            result_text = result_text.rsplit("```", 1)[0]
        result = json.loads(result_text)

        return {
            "ATS Score": min(max(result.get("ATS Score", 50), 0), 100),
            "Matched Keywords": result.get("Matched Keywords", []),
            "Missing Keywords": result.get("Missing Keywords", []),
            "Improvements": result.get("Improvements", ["Consider adding more details to your resume."])
        }

    except Exception as e:
        # Fallback to local analysis if API fails
        return _local_analyze_resume(text)


def _local_analyze_resume(text):
    """Fallback local analysis if OpenAI API is unavailable."""
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
