import pandas as pd
import os
from symptom_matcher import get_urgency_label

# Load severity dataset
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data', 'symptoms')

df_severity = pd.read_csv(os.path.join(DATA_DIR, 'Symptom-severity.csv'))
df_severity.columns = df_severity.columns.str.strip()
df_severity['Symptom'] = df_severity['Symptom'].str.strip().str.lower().str.replace(' ', '_')

# Build severity lookup
severity_lookup = dict(zip(df_severity['Symptom'], df_severity['weight']))

# Recommended actions based on urgency
URGENCY_ACTIONS = {
    "CRITICAL": {
        "action": "SEEK EMERGENCY CARE IMMEDIATELY",
        "time": "Right now — call emergency services",
        "color": "red",
        "emoji": "🚨"
    },
    "HIGH": {
        "action": "See a doctor within 2-4 hours",
        "time": "Same day — urgent care needed",
        "color": "orange",
        "emoji": "⚠️"
    },
    "MEDIUM": {
        "action": "Schedule a doctor appointment today",
        "time": "Within 24 hours",
        "color": "yellow",
        "emoji": "🟡"
    },
    "LOW": {
        "action": "Monitor symptoms and rest",
        "time": "Within 48-72 hours if symptoms persist",
        "color": "green",
        "emoji": "🟢"
    }
}

# High risk symptom combinations
HIGH_RISK_COMBINATIONS = [
    ["chest_pain", "muscle_pain"],
    ["chest_pain", "abdominal_pain"],
    ["stomach_pain", "vomiting", "nausea"],
    ["chest_pain", "back_pain"],
    ["dizziness", "weakness_in_limbs"],
    ["high_fever", "headache", "nausea"],
]

# Emergency symptoms that always trigger critical
EMERGENCY_SYMPTOMS = [
    "chest_pain",
    "weakness_of_one_body_side",
    "loss_of_consciousness",
]

def check_emergency_symptoms(normalized_symptoms):
    """Check if any symptom is an immediate emergency"""
    for symptom in normalized_symptoms:
        if symptom in EMERGENCY_SYMPTOMS:
            return True, symptom
    return False, None

def check_high_risk_combinations(normalized_symptoms):
    """Check if symptom combination is high risk"""
    symptom_set = set(normalized_symptoms)
    for combo in HIGH_RISK_COMBINATIONS:
        if all(s in symptom_set for s in combo):
            return True, combo
    return False, None

def calculate_detailed_severity(normalized_symptoms, base_urgency):
    """
    Calculate detailed severity assessment
    
    Parameters:
    - normalized_symptoms: list of symptom names from dataset
    - base_urgency: urgency score 0-10 from symptom_matcher
    
    Returns:
    - detailed severity assessment dict
    """
    
    # Check for emergency symptoms first
    is_emergency, emergency_symptom = check_emergency_symptoms(normalized_symptoms)
    if is_emergency:
        return {
            "severity_score": 10,
            "urgency_label": "CRITICAL",
            "is_emergency": True,
            "emergency_trigger": emergency_symptom,
            "high_risk_combination": None,
            "recommended_action": URGENCY_ACTIONS["CRITICAL"]["action"],
            "time_to_doctor": URGENCY_ACTIONS["CRITICAL"]["time"],
            "color": URGENCY_ACTIONS["CRITICAL"]["color"],
            "emoji": URGENCY_ACTIONS["CRITICAL"]["emoji"],
            "symptom_breakdown": get_symptom_breakdown(normalized_symptoms)
        }
    
    # Check for high risk combinations
    is_high_risk, risk_combo = check_high_risk_combinations(normalized_symptoms)
    
    # Adjust urgency if high risk combination detected
    adjusted_urgency = base_urgency
    if is_high_risk:
        adjusted_urgency = min(10, base_urgency + 2)
    
    # Multiple symptoms increase urgency
    if len(normalized_symptoms) >= 4:
        adjusted_urgency = min(10, adjusted_urgency + 0.5)  # was +1
    
    # Get urgency label
    urgency_label = get_urgency_label(adjusted_urgency)
    
    # Get recommended action
    action_data = URGENCY_ACTIONS[urgency_label]
    
    return {
        "severity_score": round(adjusted_urgency, 1),
        "urgency_label": urgency_label,
        "is_emergency": False,
        "emergency_trigger": None,
        "high_risk_combination": risk_combo,
        "recommended_action": action_data["action"],
        "time_to_doctor": action_data["time"],
        "color": action_data["color"],
        "emoji": action_data["emoji"],
        "symptom_breakdown": get_symptom_breakdown(normalized_symptoms)
    }

def get_symptom_breakdown(normalized_symptoms):
    """
    Get severity weight for each individual symptom
    """
    breakdown = []
    for symptom in normalized_symptoms:
        weight = severity_lookup.get(symptom, 3)
        breakdown.append({
            "symptom": symptom,
            "severity_weight": weight,
            "level": "High" if weight >= 6 else "Medium" if weight >= 4 else "Low"
        })
    
    # Sort by severity weight descending
    breakdown.sort(key=lambda x: x['severity_weight'], reverse=True)
    return breakdown

def format_severity_for_display(severity_data):
    """
    Format severity data for staff screen display
    """
    emoji = severity_data['emoji']
    label = severity_data['urgency_label']
    score = severity_data['severity_score']
    action = severity_data['recommended_action']
    time = severity_data['time_to_doctor']
    
    display = f"""
{emoji} URGENCY: {label} ({score}/10)
━━━━━━━━━━━━━━━━━━━━━━━━━━
ACTION: {action}
TIME: {time}
"""
    
    if severity_data['is_emergency']:
        display += f"\n🚨 EMERGENCY TRIGGER: {severity_data['emergency_trigger']}"
    
    if severity_data['high_risk_combination']:
        combo = ' + '.join(severity_data['high_risk_combination'])
        display += f"\n⚠️ HIGH RISK COMBINATION: {combo}"
    
    display += "\n\nSYMPTOM BREAKDOWN:"
    for s in severity_data['symptom_breakdown']:
        display += f"\n  • {s['symptom']}: {s['level']} (weight: {s['severity_weight']})"
    
    return display


# ── Test ──────────────────────────────────────────
if __name__ == "__main__":
    print("=== Testing Severity Predictor ===\n")

    # Test 1 — headache + dizzy + sick (medium)
    print("TEST 1: headache + dizzy + sick")
    result1 = calculate_detailed_severity(
        normalized_symptoms=["headache", "dizziness", "nausea", "vomiting"],
        base_urgency=6.1
    )
    print(format_severity_for_display(result1))

    print("\n" + "="*40 + "\n")

    # Test 2 — chest pain (should be critical/high)
    print("TEST 2: chest pain + back pain")
    result2 = calculate_detailed_severity(
        normalized_symptoms=["chest_pain", "back_pain", "muscle_pain"],
        base_urgency=5.4
    )
    print(format_severity_for_display(result2))

    print("\n" + "="*40 + "\n")

    # Test 3 — emergency trigger
    print("TEST 3: emergency trigger")
    result3 = calculate_detailed_severity(
        normalized_symptoms=["chest_pain", "weakness_of_one_body_side"],
        base_urgency=8.0
    )
    print(format_severity_for_display(result3))