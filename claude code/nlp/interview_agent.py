from openai import OpenAI
import random
import os

# Secure way: use environment variable
client = OpenAI(api_key="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")

# Backup local questions if API fails
FALLBACK_QUESTIONS = [
    "Tell me about yourself.",
    "What are your strengths and weaknesses?",
    "Explain one of your projects.",
    "What is machine learning?",
    "Explain OOP concepts in Python.",
    "What is SQL JOIN?",
    "How do you handle failure?",
    "Where do you see yourself in 5 years?"
]


def generate_question(chat_history):

    try:
        messages = [
            {
                "role": "system",
                "content": """You are a professional technical interviewer.
Ask one interview question at a time.
Focus on software developer roles.
Be realistic and professional."""
            }
        ]

        # Add previous chat
        for msg in chat_history:
            if msg["role"] == "interviewer":
                messages.append({
                    "role": "assistant",
                    "content": msg["content"]
                })
            else:
                messages.append({
                    "role": "user",
                    "content": msg["content"]
                })

        # Generate AI question
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )

        return response.choices[0].message.content

    except Exception as e:

        # fallback if API fails
        asked = [msg["content"] for msg in chat_history if msg["role"] == "interviewer"]

        remaining = [q for q in FALLBACK_QUESTIONS if q not in asked]

        if remaining:
            return random.choice(remaining)
        else:
            return "Interview completed. Good job!"

import re
from textblob import TextBlob

def analyze_answer(answer):

    score = 0
    feedback = []

    word_count = len(answer.split())

    # Length score
    if word_count > 80:
        score += 30
    elif word_count > 40:
        score += 20
    else:
        feedback.append("Answer is too short. Add more details.")

    # Confidence words
    confident_words = [
        "implemented", "developed", "built",
        "created", "designed", "improved",
        "optimized", "achieved"
    ]

    confidence_score = sum(
        1 for word in confident_words if word in answer.lower()
    )

    score += min(confidence_score * 5, 30)

    if confidence_score < 2:
        feedback.append("Use more confident action words like 'developed', 'implemented'.")

    # Sentiment analysis
    sentiment = TextBlob(answer).sentiment.polarity

    if sentiment > 0:
        score += 20
    else:
        feedback.append("Answer sounds neutral. Show more confidence and positivity.")

    # Technical keywords
    tech_keywords = [
        "python", "project", "machine learning",
        "api", "database", "flask", "sql"
    ]

    tech_score = sum(
        1 for word in tech_keywords if word in answer.lower()
    )

    score += min(tech_score * 5, 20)

    if tech_score == 0:
        feedback.append("Add technical details to strengthen your answer.")

    score = min(score, 100)

    return {
        "score": score,
        "confidence": confidence_score * 10,
        "sentiment": sentiment,
        "feedback": feedback
    }