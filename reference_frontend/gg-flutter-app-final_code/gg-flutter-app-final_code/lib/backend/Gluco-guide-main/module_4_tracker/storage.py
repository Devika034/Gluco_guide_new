from collections import defaultdict

progress_store = defaultdict(lambda: defaultdict(list))

def save_score(patient_id, disease, score):
    progress_store[patient_id][disease].append(score)

def get_last_score(patient_id, disease):
    history = progress_store[patient_id][disease]
    return history[-2] if len(history) > 1 else None
