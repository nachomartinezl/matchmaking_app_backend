import numpy as np
from ..models import QuestionnaireSubmit

# --- Paste all four of your calculation functions here ---
def calculate_hexaco_scores(responses):
    """
    Calculates HEXACO personality scores based on responses.

    Args:
        responses (list): A list of 60 numeric responses, where each response is
                         an integer between 1 and 5.

    Returns:
        dict: A dictionary with facet scores and factor scores for HEXACO.

    Raises:
        ValueError: If the responses list does not contain exactly 60 items.
    """
    # Validate input length
    if len(responses) != 60:
        raise ValueError("Responses list must contain exactly 60 items.")

    def reverse_key(value):
        # Reverse the response key for certain items
        return 6 - value

    # Define scoring keys for HEXACO
    scoring_keys = {
        'Honesty-Humility': {
            'Sincerity': [6, 30, 54],
            'Fairness': [12, 36, 60],
            'Greed-Avoidance': [18, 42],
            'Modesty': [24, 48]
        },
        'Emotionality': {
            'Fearfulness': [5, 29, 53],
            'Anxiety': [11, 35],
            'Dependence': [17, 41],
            'Sentimentality': [23, 47, 59]
        },
        'Extraversion': {
            'Social Self-Esteem': [4, 28, 52],
            'Social Boldness': [10, 34, 58],
            'Sociability': [16, 40],
            'Liveliness': [22, 46]
        },
        'Agreeableness': {
            'Forgiveness': [3, 27],
            'Gentleness': [9, 33, 51],
            'Flexibility': [15, 39, 57],
            'Patience': [21, 45]
        },
        'Conscientiousness': {
            'Organization': [2, 26],
            'Diligence': [8, 32],
            'Perfectionism': [14, 38, 50],
            'Prudence': [20, 44, 56]
        },
        'Openness to Experience': {
            'Aesthetic Appreciation': [1, 25],
            'Inquisitiveness': [7, 31],
            'Creativity': [13, 37, 49],
            'Unconventionality': [19, 43, 55]
        }
    }

    # Items that need reverse scoring (adjust indices to 0-based for Python)
    reverse_keyed_items = {i - 1 for i in [1, 4, 6, 10, 12, 14, 15, 19, 20, 21, 22, 24, 26, 28, 30, 31, 33, 35, 36, 38, 39, 41, 42, 44, 45, 46, 48, 49, 50, 52, 54, 56, 57, 59, 60]}

    # Reverse responses where needed
    adjusted_responses = [reverse_key(r) if i in reverse_keyed_items else r for i, r in enumerate(responses)]

    # Calculate facet scores
    facet_scores = {
        facet: np.mean([adjusted_responses[i - 1] for i in indices])
        for factor, facets in scoring_keys.items()
        for facet, indices in facets.items()
    }

    # Calculate factor scores
    factor_scores = {
        factor: np.mean([facet_scores[facet] for facet in facets.keys()])
        for factor, facets in scoring_keys.items()
    }

    return {'Facet Scores': facet_scores, 'Factor Scores': factor_scores}
    
    
def calculate_mbti_scores(responses):
    # NOTE: Your function expects responses from 1-5, but the frontend might send 0/1.
    # We will adjust this in the main service. For now, let's assume it works with 0/1.
    # A simple mapping: 0 -> "A" choice, 1 -> "B" choice
    if len(responses) != 70:
        raise ValueError("Responses list must contain exactly 70 items.")
    
    scoring_keys = {
        'E-I': [0, 7, 14, 21, 28, 35, 42, 49, 56, 63],
        'S-N': [1, 8, 15, 22, 29, 36, 43, 50, 57, 64, 2, 9, 16, 23, 30, 37, 44, 51, 58, 65],
        'T-F': [3, 10, 17, 24, 31, 38, 45, 52, 59, 66, 4, 11, 18, 25, 32, 39, 46, 53, 60, 67],
        'J-P': [5, 12, 19, 26, 33, 40, 47, 54, 61, 68, 6, 13, 20, 27, 34, 41, 48, 55, 62, 69]
    }
    
    mbti_type = ""
    mbti_type += "E" if sum(1 for i in scoring_keys['E-I'] if responses[i] == 0) > 5 else "I"
    mbti_type += "S" if sum(1 for i in scoring_keys['S-N'] if responses[i] == 0) > 10 else "N"
    mbti_type += "T" if sum(1 for i in scoring_keys['T-F'] if responses[i] == 0) > 10 else "F"
    mbti_type += "J" if sum(1 for i in scoring_keys['J-P'] if responses[i] == 0) > 10 else "P"

    return {'MBTI Type': mbti_type}
    
def calculate_attachment_style_scores(responses):
    """
    Calculates attachment style scores based on responses.

    Args:
        responses (list): A list of 20 numeric responses, where each response is
                         an integer between 1 and 5.

    Returns:
        dict: A dictionary containing attachment style scores.

    Raises:
        ValueError: If the responses list does not contain exactly 20 items.
    """
    # Validate input length
    if len(responses) != 20:
        raise ValueError("Responses list must contain exactly 20 items.")

    # Define scoring keys for attachment styles
    scoring_keys = {
        'Secure': [1, 2, 3, 4, 5],
        'Anxious-Preoccupied': [6, 7, 8, 9, 10],
        'Dismissive-Avoidant': [11, 12, 13, 14, 15],
        'Fearful-Avoidant': [16, 17, 18, 19, 20]
    }

    # Calculate scores for each attachment style
    scores = {
        style: sum(responses[i - 1] for i in indices)
        for style, indices in scoring_keys.items()
    }

    return {'Attachment Style Scores': scores}

def calculate_values_scores(responses):
    """
    Calculates Schwartz value scores based on responses.

    Args:
        responses (list): A list of 10 numeric responses, where each response is
                         an integer between 1 and 5.

    Returns:
        dict: A dictionary containing Schwartz value scores.

    Raises:
        ValueError: If the responses list does not contain exactly 10 items.
    """
    # Validate input length
    if len(responses) != 10:
        raise ValueError("Responses list must contain exactly 10 items.")

    # Define Schwartz values
    values = [
        "Power", "Achievement", "Hedonism", "Stimulation", "Self-Direction", "Universalism",
        "Benevolence", "Tradition", "Conformity", "Security"
    ]

    # Map responses to corresponding values
    scores = {values[i]: responses[i] for i in range(10)}

    return {'Values Scores': scores}


# --- Create a master dispatcher function ---
def calculate_scores_from_submission(submission: QuestionnaireSubmit) -> dict:
    """
    Dispatcher function that calls the correct scoring algorithm
    based on the questionnaire name.
    """
    name = submission.questionnaire
    responses = submission.responses

    if name == 'hexaco':
        return calculate_hexaco_scores(responses)
    elif name == 'mbti':
        # Your MBTI test has 2 options per question. The frontend will send [0, 1, 0, 0...].
        return calculate_mbti_scores(responses)
    elif name == 'attachment_styles':
        return calculate_attachment_style_scores(responses)
    elif name == 'schwartz_survey':
        return calculate_values_scores(responses)
    else:
        print(f"Warning: No specific scoring logic found for questionnaire '{name}'.")
        return None