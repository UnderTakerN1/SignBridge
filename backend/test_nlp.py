from nlp_handler import generate_medical_summary, generate_sentence_from_signs

# Test 1 — Medical Summary
print("=== TEST 1: Medical Summary ===")
test_symptom_data = {
    "possible_conditions": [
        {"disease": "Migraine"},
        {"disease": "Hypertension"},
        {"disease": "Vertigo"}
    ],
    "urgency_level": 7
}

result = generate_medical_summary(
    signs_sequence=["headache", "dizzy", "sick"],
    symptom_data=test_symptom_data,
    follow_up_answers={
        "duration": "2 days",
        "severity": "severe",
        "cause": "gradual",
        "medicine": "no"
    }
)

print(result["summary"])
print(f"\nSuccess: {result['success']}")
print(f"Error: {result.get('error', 'none')}")

# Test 2 — Sentence Builder
print("\n=== TEST 2: Sentence Builder ===")
sentence = generate_sentence_from_signs(
    signs_sequence=["headache", "dizzy"],
    follow_up_answers={
        "duration": "today",
        "severity": "moderate"
    }
)
print(sentence)