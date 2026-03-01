import numpy as np

def analyze_skills(data):
    subjects = list(data.keys())
    scores = np.array(list(map(int, data.values())))

    weak = [subjects[i] for i, s in enumerate(scores) if s < 50]
    skill_percent = int(scores.mean())

    if skill_percent > 75:
        career = "AI / Data Science"
    elif skill_percent > 60:
        career = "Web Development"
    else:
        career = "Fundamentals & Internships"

    return {
        "Weak Areas": weak,
        "Skill Percentage": skill_percent,
        "Career Recommendation": career
    }
