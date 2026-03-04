from openai import OpenAI
import random
import os
import re
from textblob import TextBlob

# Use API key
client = OpenAI(api_key="YOUR_OPENAI_API_KEY")  # Replace with your actual API key or set it as an environment variable

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


def analyze_answer(answer):
    """Analyze an interview answer using OpenAI for real, contextual feedback."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert interview coach. Analyze the candidate's answer and provide:
1. A score from 0-100
2. A confidence rating from 0-100
3. Specific, actionable feedback points (2-4 bullet points)

Evaluate based on:
- Clarity and structure of the answer
- Use of specific examples and technical details
- Confidence and professionalism
- Relevance and completeness

Respond in this exact JSON format (no markdown, just raw JSON):
{"score": 75, "confidence": 80, "feedback": ["Point 1", "Point 2", "Point 3"]}"""
                },
                {
                    "role": "user",
                    "content": f"Analyze this interview answer:\n\n{answer}"
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

        # Compute sentiment locally as a supplementary metric
        sentiment = TextBlob(answer).sentiment.polarity

        return {
            "score": min(max(result.get("score", 50), 0), 100),
            "confidence": min(max(result.get("confidence", 50), 0), 100),
            "sentiment": sentiment,
            "feedback": result.get("feedback", ["Good attempt. Keep practicing!"])
        }

    except Exception as e:
        # Fallback to local analysis if API fails
        return _local_analyze_answer(answer)


def _local_analyze_answer(answer):
    """Fallback local analysis if OpenAI API is unavailable."""
    score = 0
    feedback = []

    word_count = len(answer.split())

    # Length score
    if word_count > 80:
        score += 30
    elif word_count > 40:
        score += 20
    else:
        feedback.append("Answer is too short. Add more details and examples.")

    # Confidence words
    confident_words = [
        "implemented", "developed", "built",
        "created", "designed", "improved",
        "optimized", "achieved", "led", "managed"
    ]

    confidence_score = sum(
        1 for word in confident_words if word in answer.lower()
    )

    score += min(confidence_score * 5, 30)

    if confidence_score < 2:
        feedback.append("Use more confident action words like 'developed', 'implemented', 'led'.")

    # Sentiment analysis
    sentiment = TextBlob(answer).sentiment.polarity

    if sentiment > 0:
        score += 20
    else:
        feedback.append("Answer sounds neutral. Show more confidence and positivity.")

    # Technical keywords
    tech_keywords = [
        "python", "project", "machine learning",
        "api", "database", "flask", "sql", "algorithm",
        "architecture", "framework"
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