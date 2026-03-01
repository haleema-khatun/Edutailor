def recommend(skills):
    if "Python" in skills and skills["Python"] > 70:
        return "AI / ML Engineer"
    return "Software Developer"
