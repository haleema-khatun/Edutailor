import random
from textblob import TextBlob

def analyze_sentiment(answer):
    blob = TextBlob(answer)
    polarity = blob.sentiment.polarity

    if polarity > 0:
        return "Positive"
    elif polarity < 0:
        return "Negative"
    else:
        return "Neutral"
def confidence_score(answer):
    weak_words = ["maybe", "i think", "not sure", "probably"]

    score = 100
    for word in weak_words:
        if word in answer.lower():
            score -= 10

    return score

QUESTIONS = [
    "Explain what is Machine Learning.",
    "What is the difference between list and tuple in Python?",
    "Explain overfitting in machine learning.",
    "What is REST API?",
    "Explain OOP concepts."
]

def get_random_question():
    return random.choice(QUESTIONS)


def analyze_interview(answer):
    score = 0
    feedback = []

    word_count = len(answer.split())

    # Length check
    if word_count > 50:
        score += 30
    else:
        feedback.append("Your answer is too short. Explain in more detail.")

    # Technical keyword check
    if "example" in answer.lower():
        score += 20
    else:
        feedback.append("Add examples to make your answer stronger.")

    if any(word in answer.lower() for word in ["because", "therefore", "used for"]):
        score += 20
    else:
        feedback.append("Explain reasoning clearly using terms like 'because'.")

    if word_count > 100:
        score += 20

    if score < 50:
        level = "Needs Improvement"
    elif score < 80:
        level = "Good"
    else:
        level = "Excellent"

    return {
        "Score": score,
        "Level": level,
        "Feedback": feedback
    }
