def compute_score(answers: dict) -> float:
    if not answers: return 0.0
    total = sum(answers.values())
    max_score = len(answers) * 2
    return round(total / max_score, 2)

def interpret_score(current: float, previous: float | None):
    if previous is None: trend = "Baseline"
    elif current > previous + 0.1: trend = "Worsening"
    elif current < previous - 0.1: trend = "Improving"
    else: trend = "Stable"

    interpretation = []
    if current < 0.3:
        status = "Stable"
        interpretation = ["Symptoms are minimal or absent", "condition appears stable", "Continue routine monitoring"]
    elif current < 0.6:
        status = "Watchful"
        interpretation = ["Some symptoms have increased", "May indicate rising stress on the system", "No emergency signs detected"]
    else:
        status = "High Risk"
        interpretation = ["Significant symptoms detected", "High likelihood of complications", "Immediate medical attention recommended"]
    return status, trend, interpretation

def recommendations_for(disease: str, score: float):
    base = {
        "retinopathy": ["Maintain stable blood glucose", "Limit screen strain", "Schedule regular eye exams"],
        "nephropathy": ["Monitor blood pressure", "Reduce salt intake", "Stay hydrated"],
        "neuropathy": ["Inspect feet daily", "Avoid walking barefoot", "Maintain glucose control"]
    }
    if score > 0.6:
        base[disease].append("Consult specialist urgently")
    return base[disease]
