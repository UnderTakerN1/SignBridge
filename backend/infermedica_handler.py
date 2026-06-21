import requests
import os
from dotenv import load_dotenv

load_dotenv()

# ── Infermedica API Configuration ─────────────────
INFERMEDICA_APP_ID = os.environ.get("INFERMEDICA_APP_ID")
INFERMEDICA_APP_KEY = os.environ.get("INFERMEDICA_APP_KEY")
INFERMEDICA_BASE_URL = "https://api.infermedica.com/v3"

HEADERS = {
    "App-Id": INFERMEDICA_APP_ID,
    "App-Key": INFERMEDICA_APP_KEY,
    "Content-Type": "application/json"
}

# ── Our ASL Signs Mapped To Infermedica Symptom IDs ──
# Infermedica uses specific symptom IDs from their database
# These are the closest matches to our 12 ASL signs
SIGN_TO_INFERMEDICA = {
    "pain":        ["s_13", "s_50"],    # Abdominal pain + Chest pain
    "sick":        ["s_156", "s_305"],  # Nausea + Vomiting  
    "help":        ["s_650", "s_2100"], # Muscle weakness + Fatigue
    "medicine":    ["s_98"],            # Fever (most common reason for medication)
    "doctor":      ["s_21", "s_156"],   # Headache + Nausea (general consultation)
    "headache":    ["s_21"],            # Headache
    "temperature": ["s_98"],            # Fever
    "dizzy":       ["s_370"],           # Dizziness
    "emergency":   ["s_50", "s_31"],    # Chest pain + Chest pain during rest
    "stomach":     ["s_13"],            # Abdominal pain
    "cough":       ["s_102"],           # Cough
    "hurt":        ["s_13", "s_650"]    # Abdominal pain + Muscle weakness
}

# ── Triage Level Mapping ───────────────────────────
TRIAGE_TO_DISPLAY = {
    "emergency":         {
        "label": "CRITICAL",
        "score": 95,
        "color": "#ef4444",
        "emoji": "🚨",
        "action": "SEEK EMERGENCY CARE IMMEDIATELY",
        "time": "Right now — call emergency services"
    },
    "consultation_24":   {
        "label": "HIGH",
        "score": 70,
        "color": "#f97316",
        "emoji": "⚠️",
        "action": "See a doctor within 24 hours",
        "time": "Same day — urgent care needed"
    },
    "consultation":      {
        "label": "MEDIUM",
        "score": 45,
        "color": "#eab308",
        "emoji": "🟡",
        "action": "Schedule a doctor appointment",
        "time": "Within 48-72 hours"
    },
    "self_care":         {
        "label": "LOW",
        "score": 20,
        "color": "#22c55e",
        "emoji": "🟢",
        "action": "Monitor symptoms and rest",
        "time": "If symptoms persist after 72 hours"
    }
}


def get_symptom_ids(signs_sequence):
    """Convert our ASL sign labels to Infermedica symptom IDs"""
    symptom_ids = set()
    for sign in signs_sequence:
        ids = SIGN_TO_INFERMEDICA.get(sign.lower(), [])
        symptom_ids.update(ids)
    return list(symptom_ids)


def run_diagnosis(signs_sequence, patient_info=None):
    if patient_info is None:
        patient_info = {"age": {"value": 35}, "sex": "male"}

    symptom_ids = get_symptom_ids(signs_sequence)
    if not symptom_ids:
        return _fallback_result(signs_sequence, "No matching symptoms found")

    evidence = [
        {"id": sid, "choice_id": "present", "source": "initial"}
        for sid in symptom_ids
    ]

    payload = {
        "sex": patient_info.get("sex", "male"),
        "age": patient_info.get("age", {"value": 35}),
        "evidence": evidence,
        "extras": {"disable_groups": True}
    }

    try:
        print(f"   Calling Infermedica diagnosis API...")
        print(f"   Symptoms: {symptom_ids}")

        response = requests.post(
            f"{INFERMEDICA_BASE_URL}/diagnosis",
            headers=HEADERS,
            json=payload,
            timeout=10
        )

        if response.status_code != 200:
            print(f"   ⚠️ API error: {response.status_code} — {response.text}")
            return _fallback_result(signs_sequence, f"API error: {response.status_code}")

        data = response.json()
        return _process_diagnosis_result(data, signs_sequence)

    except Exception as e:
        print(f"   ⚠️ Infermedica error: {e}")
        return _fallback_result(signs_sequence, str(e))


def run_triage(signs_sequence, patient_info=None):
    if patient_info is None:
        patient_info = {"age": {"value": 35}, "sex": "male"}

    symptom_ids = get_symptom_ids(signs_sequence)
    if not symptom_ids:
        return TRIAGE_TO_DISPLAY["consultation"]

    evidence = [
        {"id": sid, "choice_id": "present", "source": "initial"}
        for sid in symptom_ids
    ]

    payload = {
        "sex": patient_info.get("sex", "male"),
        "age": patient_info.get("age", {"value": 35}),
        "evidence": evidence
    }

    try:
        print(f"   Calling Infermedica triage API...")

        response = requests.post(
            f"{INFERMEDICA_BASE_URL}/triage",
            headers=HEADERS,
            json=payload,
            timeout=10
        )

        if response.status_code != 200:
            print(f"   ⚠️ Triage error: {response.status_code} — {response.text}")
            return TRIAGE_TO_DISPLAY["consultation"]

        data = response.json()
        triage_level = data.get("triage_level", "consultation")
        print(f"   ✅ Triage level: {triage_level}")

        return {
            **TRIAGE_TO_DISPLAY.get(triage_level, TRIAGE_TO_DISPLAY["consultation"]),
            "raw_triage_level": triage_level,
            "serious": data.get("serious", [])
        }

    except Exception as e:
        print(f"   ⚠️ Triage error: {e}")
        return TRIAGE_TO_DISPLAY["consultation"]

def get_follow_up_questions(signs_sequence, patient_info=None):
    """
    Get Infermedica's suggested follow-up questions
    These are clinically validated questions based on symptoms
    """
    if patient_info is None:
        patient_info = {"age": {"value": 35}, "sex": "male"}

    symptom_ids = get_symptom_ids(signs_sequence)

    if not symptom_ids:
        return []

    evidence = [
        {"id": sid, "choice_id": "present", "source": "initial"}
        for sid in symptom_ids
    ]

    payload = {
        "sex": patient_info.get("sex", "male"),
        "age": patient_info.get("age", {"value": 35}),
        "evidence": evidence,
        "extras": {"disable_groups": True}
    }

    try:
        response = requests.post(
            f"{INFERMEDICA_BASE_URL}/diagnosis",
            headers=HEADERS,
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            question = data.get("question", {})
            if question:
                return [question.get("text", "")]

        return []

    except Exception as e:
        return []


def _process_diagnosis_result(data, signs_sequence):
    """Process raw Infermedica response into our standard format"""

    conditions = data.get("conditions", [])
    question = data.get("question", {})

    # Format conditions
    formatted_conditions = []
    for condition in conditions[:5]:
        formatted_conditions.append({
            "disease": condition.get("name", "Unknown"),
            "probability": round(condition.get("probability", 0) * 100, 1),
            "match_percentage": round(condition.get("probability", 0) * 100, 1),
            "description": f"Probability: {round(condition.get('probability', 0) * 100, 1)}%",
            "precautions": []
        })

    # Get follow-up question
    follow_up_questions = []
    if question:
        follow_up_questions.append(question.get("text", ""))

    return {
        "possible_conditions": formatted_conditions,
        "possible_conditions_simple": [c["disease"] for c in formatted_conditions[:3]],
        "follow_up_questions": follow_up_questions,
        "normalized_symptoms": get_symptom_ids(signs_sequence),
        "urgency_level": 5,
        "found": len(formatted_conditions) > 0,
        "source": "infermedica"
    }


def _fallback_result(signs_sequence, reason):
    """Fallback when Infermedica is unavailable"""
    print(f"   Using fallback result. Reason: {reason}")
    return {
        "possible_conditions": [],
        "possible_conditions_simple": [],
        "follow_up_questions": [],
        "normalized_symptoms": [],
        "urgency_level": 5,
        "found": False,
        "source": "fallback",
        "fallback_reason": reason
    }

# ── Follow-up Answer to Additional Symptom IDs ────
DURATION_TO_SYMPTOMS = {
    "today":   [],                    # acute — no extra symptoms
    "2 days":  ["s_2907"],            # fever present in past 72 hours
    "1 week":  ["s_1547"],            # fatigue more than 6 months? no — skip
    "more":    ["s_1547"]             # chronic fatigue indicator
}

SEVERITY_TO_SYMPTOMS = {
    "mild":        [],
    "moderate":    ["s_2100"],        # fatigue
    "severe":      ["s_2100", "s_650"], # fatigue + muscle weakness
    "unbearable":  ["s_2100", "s_650", "s_305"]  # + vomiting
}


def run_diagnosis_with_context(signs_sequence, follow_up_answers=None, patient_info=None):
    """
    Enhanced diagnosis that incorporates follow-up answers
    as additional symptom evidence for more accurate results
    """
    if patient_info is None:
        patient_info = {"age": {"value": 35}, "sex": "male"}

    # Get base symptom IDs from signs
    symptom_ids = set(get_symptom_ids(signs_sequence))

    # Add extra symptoms based on follow-up answers
    if follow_up_answers:
        duration = follow_up_answers.get("duration", "").lower()
        severity = follow_up_answers.get("severity", "").lower()

        # Add duration-based symptoms
        for key, ids in DURATION_TO_SYMPTOMS.items():
            if key in duration:
                symptom_ids.update(ids)

        # Add severity-based symptoms
        for key, ids in SEVERITY_TO_SYMPTOMS.items():
            if key in severity:
                symptom_ids.update(ids)

    symptom_ids = list(symptom_ids)

    if not symptom_ids:
        return _fallback_result(signs_sequence, "No symptoms")

    evidence = [
        {"id": sid, "choice_id": "present", "source": "initial"}
        for sid in symptom_ids
    ]

    payload = {
        "sex": patient_info.get("sex", "male"),
        "age": patient_info.get("age", {"value": 35}),
        "evidence": evidence,
        "extras": {"disable_groups": True}
    }

    try:
        print(f"   Enhanced diagnosis with {len(symptom_ids)} symptoms: {symptom_ids}")

        response = requests.post(
            f"{INFERMEDICA_BASE_URL}/diagnosis",
            headers=HEADERS,
            json=payload,
            timeout=10
        )

        if response.status_code != 200:
            return _fallback_result(signs_sequence, f"API error: {response.status_code}")

        data = response.json()
        return _process_diagnosis_result(data, signs_sequence)

    except Exception as e:
        return _fallback_result(signs_sequence, str(e))


def run_triage_with_context(signs_sequence, follow_up_answers=None, patient_info=None):
    """
    Enhanced triage that incorporates follow-up answers
    """
    if patient_info is None:
        patient_info = {"age": {"value": 35}, "sex": "male"}

    symptom_ids = set(get_symptom_ids(signs_sequence))

    if follow_up_answers:
        duration = follow_up_answers.get("duration", "").lower()
        severity = follow_up_answers.get("severity", "").lower()

        for key, ids in DURATION_TO_SYMPTOMS.items():
            if key in duration:
                symptom_ids.update(ids)

        for key, ids in SEVERITY_TO_SYMPTOMS.items():
            if key in severity:
                symptom_ids.update(ids)

    symptom_ids = list(symptom_ids)

    evidence = [
        {"id": sid, "choice_id": "present", "source": "initial"}
        for sid in symptom_ids
    ]

    payload = {
        "sex": patient_info.get("sex", "male"),
        "age": patient_info.get("age", {"value": 35}),
        "evidence": evidence
    }

    try:
        response = requests.post(
            f"{INFERMEDICA_BASE_URL}/triage",
            headers=HEADERS,
            json=payload,
            timeout=10
        )

        if response.status_code != 200:
            return TRIAGE_TO_DISPLAY["consultation"]

        data = response.json()
        triage_level = data.get("triage_level", "consultation")
        print(f"   ✅ Enhanced triage level: {triage_level}")

        return {
            **TRIAGE_TO_DISPLAY.get(triage_level, TRIAGE_TO_DISPLAY["consultation"]),
            "raw_triage_level": triage_level,
            "serious": data.get("serious", [])
        }

    except Exception as e:
        return TRIAGE_TO_DISPLAY["consultation"]


# ── Test ───────────────────────────────────────────
if __name__ == "__main__":
    print("=== Testing Infermedica Integration ===\n")

    print("TEST 1: Diagnosis for headache + dizzy + stomach")
    result = run_diagnosis(["headache", "dizzy", "stomach"])
    print(f"Conditions found: {len(result['possible_conditions'])}")
    for c in result['possible_conditions'][:3]:
        print(f"  - {c['disease']}: {c['probability']}%")

    print("\nTEST 2: Triage for headache + dizzy + stomach")
    triage = run_triage(["headache", "dizzy", "stomach"])
    print(f"Triage level: {triage['label']}")
    print(f"Action: {triage['action']}")

    print("\nTEST 3: Emergency signs")
    triage_emergency = run_triage(["emergency", "pain", "hurt"])
    print(f"Triage level: {triage_emergency['label']}")
    print(f"Action: {triage_emergency['action']}")

    print("\nTEST 4: Cough + fever + sick")
    result4 = run_diagnosis(["cough", "temperature", "sick"])
    print(f"Conditions found: {len(result4['possible_conditions'])}")
    for c in result4['possible_conditions'][:3]:
        print(f"  - {c['disease']}: {c['probability']}%")
    triage4 = run_triage(["cough", "temperature", "sick"])
    print(f"Triage: {triage4['label']} — {triage4['action']}")
    print("\nTEST 5: Headache + dizzy WITH context (severe, 2 days)")
    result5 = run_diagnosis_with_context(
        signs_sequence=["headache", "dizzy", "stomach"],
        follow_up_answers={"duration": "2 days", "severity": "severe"}
    )
    print(f"Conditions: {[(c['disease'], c['probability']) for c in result5['possible_conditions'][:3]]}")
    triage5 = run_triage_with_context(
        signs_sequence=["headache", "dizzy", "stomach"],
        follow_up_answers={"duration": "2 days", "severity": "severe"}
    )
    print(f"Enhanced triage: {triage5['label']} — {triage5['action']}")

