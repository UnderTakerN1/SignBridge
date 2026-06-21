import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Initialize Groq client — key loaded from .env
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def generate_medical_summary(signs_sequence, symptom_data, follow_up_answers=None, infermedica_conditions=None):
    """
    Generate a structured medical summary for the doctor
    """
    follow_up_context = ""
    if follow_up_answers:
        follow_up_context = f"""
        Additional patient information:
        - Duration: {follow_up_answers.get('duration', 'unknown')}
        - Severity: {follow_up_answers.get('severity', 'unknown')}
        - Cause: {follow_up_answers.get('cause', 'unknown')}
        - Taking medicine: {follow_up_answers.get('medicine', 'unknown')}
        """

    # Use Infermedica conditions if available, otherwise fall back to Kaggle
    if infermedica_conditions:
        conditions_text = ', '.join([
            f"{c['disease']} ({c['probability']}%)" 
            for c in infermedica_conditions[:3]
        ])
        conditions_source = "clinical AI engine (Infermedica)"
    else:
        conditions_text = ', '.join([
            d['disease'] for d in symptom_data.get('possible_conditions', [])[:3]
        ])
        conditions_source = "symptom matching system"

    prompt = f"""
    You are a medical assistant helping a doctor understand 
    a deaf or illiterate patient's symptoms.
    
    The patient communicated through ASL sign language.
    
    Signs detected: {', '.join(signs_sequence)}
    
    Possible conditions identified by {conditions_source}: {conditions_text}
    
    {follow_up_context}
    
    Generate a SHORT structured medical summary for the doctor with:
    1. What the patient is communicating (1 sentence)
    2. Most likely conditions to investigate (max 3) with their probabilities
    3. Urgency assessment
    4. 3 suggested questions for the doctor to ask
    5. Support programs the patient may qualify for (max 2)
    
    IMPORTANT RULES:
    - Always say "may indicate" never "diagnosis is"
    - Always remind doctor to verify directly with patient
    - Keep total response under 150 words
    - Be direct and clinical
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a concise medical assistant. Always emphasize that AI output must be verified by the doctor. Never make definitive diagnoses."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=300,
            temperature=0.3
        )

        return {
            "summary": response.choices[0].message.content,
            "success": True,
            "model": "llama-3.3-70b-versatile"
        }

    except Exception as e:
        return {
            "summary": f"AI summary unavailable. Patient signed: {', '.join(signs_sequence)}. Please proceed with manual assessment.",
            "success": False,
            "error": str(e)
        }

def generate_sentence_from_signs(signs_sequence, follow_up_answers=None):
    """
    Convert a sequence of signs into one coherent patient statement
    """
    follow_up_context = ""
    if follow_up_answers:
        follow_up_context = f"""
        Duration: {follow_up_answers.get('duration', 'unknown')}
        Severity: {follow_up_answers.get('severity', 'unknown')}
        Cause: {follow_up_answers.get('cause', 'unknown')}
        """

    prompt = f"""
    Convert these ASL signs into one clear patient statement:
    Signs: {', '.join(signs_sequence)}
    {follow_up_context}
    
    Write ONE sentence maximum describing what the patient is experiencing.
    Start with "Patient reports..."
    Keep it under 30 words.
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=60,
            temperature=0.2
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"Patient reports: {', '.join(signs_sequence)}"