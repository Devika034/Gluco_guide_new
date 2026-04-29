# Each option has a SCORE → used for trend calculation

RETINOPATHY_QUESTIONS = {
    "blurred_vision": {
        "question": "Have you experienced blurred vision recently?",
        "options": {
            "No": 0,
            "Occasionally": 1,
            "Frequently": 2
        }
    },
    "floaters": {
        "question": "Do you notice dark spots or floaters?",
        "options": {
            "No": 0,
            "Sometimes": 1,
            "Often": 2
        }
    },
    "eye_strain": {
        "question": "Do your eyes feel strained or tired?",
        "options": {
            "No": 0,
            "Mild": 1,
            "Severe": 2
        }
    },
    "eye_exam": {
        "question": "When was your last eye examination?",
        "options": {
            "Within 6 months": 0,
            "6–12 months ago": 1,
            "More than 1 year": 2
        }
    }
}

NEPHROPATHY_QUESTIONS = {
    "swelling": {
        "question": "Any swelling in feet or face?",
        "options": {
            "No": 0,
            "Mild": 1,
            "Noticeable": 2
        }
    },
    "urination": {
        "question": "Any change in urination frequency?",
        "options": {
            "Normal": 0,
            "Slight change": 1,
            "Major change": 2
        }
    },
    "fatigue": {
        "question": "How fatigued do you feel?",
        "options": {
            "Normal": 0,
            "Moderate": 1,
            "Severe": 2
        }
    },
    "bp": {
        "question": "Recent blood pressure readings?",
        "options": {
            "Normal": 0,
            "Occasionally high": 1,
            "Frequently high": 2
        }
    }
}

NEUROPATHY_QUESTIONS = {
    "tingling": {
        "question": "Any tingling or numbness in limbs?",
        "options": {
            "No": 0,
            "Occasional": 1,
            "Frequent": 2
        }
    },
    "pain": {
        "question": "Burning or sharp nerve pain?",
        "options": {
            "No": 0,
            "Sometimes": 1,
            "Often": 2
        }
    },
    "balance": {
        "question": "Any balance issues while walking?",
        "options": {
            "No": 0,
            "Rare": 1,
            "Frequent": 2
        }
    },
    "foot_care": {
        "question": "How often do you inspect your feet?",
        "options": {
            "Daily": 0,
            "Occasionally": 1,
            "Rarely": 2
        }
    }
}
