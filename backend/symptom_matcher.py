import pandas as pd
import os

# Load Kaggle datasets
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data', 'symptoms')

# Load all 4 CSV files
df_dataset = pd.read_csv(os.path.join(DATA_DIR, 'dataset.csv'))
df_severity = pd.read_csv(os.path.join(DATA_DIR, 'Symptom-severity.csv'))
df_description = pd.read_csv(os.path.join(DATA_DIR, 'symptom_Description.csv'))
df_precaution = pd.read_csv(os.path.join(DATA_DIR, 'symptom_precaution.csv'))

# Clean column names (remove extra spaces)
df_dataset.columns = df_dataset.columns.str.strip()
df_severity.columns = df_severity.columns.str.strip()
df_description.columns = df_description.columns.str.strip()
df_precaution.columns = df_precaution.columns.str.strip()

# Clean severity data
df_severity['Symptom'] = df_severity['Symptom'].str.strip().str.lower().str.replace(' ', '_')

# Build severity lookup dictionary
severity_lookup = dict(zip(df_severity['Symptom'], df_severity['weight']))

def normalize_symptom(symptom):
    """
    Normalize symptom name to match dataset format
    Maps our 12 ASL signs to actual dataset symptom names
    """
    sign_to_symptom = {
        "pain":        ["joint_pain", "muscle_pain", "chest_pain", "abdominal_pain"],
        "sick":        ["nausea", "vomiting"],
        "help":        ["weakness_in_limbs", "muscle_weakness"],
        "medicine":    ["nausea"],
        "doctor":      ["stomach_pain"],
        "headache":    ["headache"],
        "temperature": ["high_fever", "mild_fever"],
        "dizzy":       ["dizziness"],
        "emergency":   ["chest_pain"],
        "stomach":     ["stomach_pain", "abdominal_pain", "swelling_of_stomach"],
        "cough":       ["cough"],
        "hurt":        ["muscle_pain", "joint_pain", "back_pain"]
    }

    return sign_to_symptom.get(symptom.lower(), [symptom.lower()])

def get_all_symptoms_from_row(row):
    """Extract all symptoms from a dataset row"""
    symptoms = []
    for col in df_dataset.columns:
        if col != 'Disease' and pd.notna(row[col]):
            symptoms.append(str(row[col]).strip().lower())
    return symptoms

def match_symptoms_to_diseases(signs_sequence):
    """
    Given a list of ASL signs, find matching diseases
    """
    # Normalize signs to symptom names
    normalized_symptoms = []
    for sign in signs_sequence:
        mapped = normalize_symptom(sign)
        if isinstance(mapped, list):
            normalized_symptoms.extend(mapped)
        else:
            normalized_symptoms.append(mapped)
    
    # Remove duplicates
    normalized_symptoms = list(set(normalized_symptoms))
    
    # Build unique disease → symptom set mapping
    disease_symptom_map = {}
    
    for _, row in df_dataset.iterrows():
        disease = row['Disease'].strip()
        row_symptoms = get_all_symptoms_from_row(row)
        
        if disease not in disease_symptom_map:
            disease_symptom_map[disease] = set()
        
        # Add symptoms to set (automatically removes duplicates)
        for s in row_symptoms:
            disease_symptom_map[disease].add(s.strip().lower())
    
    # Now score each disease based on unique symptom matches
    disease_scores = {}

    for disease, symptom_set in disease_symptom_map.items():
        matches = sum(1 for s in normalized_symptoms if s in symptom_set)
    
        if matches > 0:
            # Match percentage — how many of OUR symptoms does this disease have
            match_percentage = (matches / len(normalized_symptoms)) * 100
        
            # Specificity score — penalize diseases with too many symptoms
            # A disease with 5 symptoms that matches 3 is more specific
            # than a disease with 15 symptoms that matches 3
            specificity = (matches / len(symptom_set)) * 100
        
            # Combined score — balance between match and specificity
            combined_score = (match_percentage * 0.6) + (specificity * 0.4)
        
            disease_scores[disease] = {
                "matches": matches,
                "percentage": round(match_percentage, 1),
                "specificity": round(specificity, 1),
                "combined_score": round(combined_score, 1),
                "total_symptoms": len(symptom_set)
            }

    # Sort by combined score
    sorted_diseases = sorted(disease_scores.items(), key=lambda x: x[1]['combined_score'],reverse=True)
    
    # Get top 5 conditions
    top_conditions = []
    for disease, score_data in sorted_diseases[:5]:
        # Get description
        desc_row = df_description[
            df_description['Disease'].str.strip() == disease
        ]
        description = desc_row['Description'].values[0] if len(desc_row) > 0 else "No description available"
        
        # Get precautions
        prec_row = df_precaution[
            df_precaution['Disease'].str.strip() == disease
        ]
        precautions = []
        if len(prec_row) > 0:
            for i in range(1, 5):
                col = f'Precaution_{i}'
                if col in prec_row.columns and pd.notna(prec_row[col].values[0]):
                    precautions.append(prec_row[col].values[0])
        
        top_conditions.append({
            "disease": disease,
            "match_score": score_data['matches'],
            "match_percentage": score_data['percentage'],
            "specificity": score_data['specificity'],
            "combined_score": score_data['combined_score'],
            "total_disease_symptoms": score_data['total_symptoms'],
            "description": description[:100] + "..." if len(description) > 100 else description,
            "precautions": precautions[:2]
        })
    
    # Calculate urgency
    urgency_level = calculate_urgency(normalized_symptoms)
    
    return {
        "input_signs": signs_sequence,
        "normalized_symptoms": normalized_symptoms,
        "possible_conditions": top_conditions,
        "urgency_level": urgency_level,
        "urgency_label": get_urgency_label(urgency_level),
        "found": len(top_conditions) > 0
    }

def calculate_urgency(normalized_symptoms):
    """
    Calculate urgency score 0-10 based on symptom severity weights
    """
    total_severity = 0
    count = 0
    
    for symptom in normalized_symptoms:
        # Clean symptom name for lookup
        clean = symptom.strip().lower()
        if clean in severity_lookup:
            total_severity += severity_lookup[clean]
            count += 1
    
    if count == 0:
        return 5  # Default medium urgency
    
    avg_severity = total_severity / count
    urgency = round((avg_severity / 7) * 10, 1)
    
    return urgency

def get_urgency_label(urgency_level):
    """Convert urgency number to label"""
    if urgency_level >= 8:
        return "CRITICAL"
    elif urgency_level >= 6:
        return "HIGH"
    elif urgency_level >= 4:
        return "MEDIUM"
    else:
        return "LOW"

# Test the matcher
if __name__ == "__main__":
    print("=== Testing Symptom Matcher ===\n")
    
    # Test 1 — headache + dizzy + sick
    result = match_symptoms_to_diseases(["headache", "dizzy", "sick"])
    print(f"Input signs: {result['input_signs']}")
    print(f"Normalized symptoms: {result['normalized_symptoms']}")
    print(f"Urgency: {result['urgency_level']}/10 — {result['urgency_label']}")
    print(f"\nTop conditions:")
    for condition in result['possible_conditions'][:3]:
        print(f"  - {condition['disease']}")
        print(f"    Match: {condition['match_score']} symptoms ({condition['match_percentage']}%)")
        print(f"    Specificity: {condition['specificity']}%")
        print(f"    Combined score: {condition['combined_score']}")
        print(f"    Description: {condition['description']}")
    
    print("\n---\n")
    
    # Test 2 — emergency + pain + hurt
    result2 = match_symptoms_to_diseases(["emergency", "pain", "hurt"])
    print(f"Input signs: {result2['input_signs']}")
    print(f"Normalized symptoms: {result2['normalized_symptoms']}")
    print(f"Urgency: {result2['urgency_level']}/10 — {result2['urgency_label']}")
    print(f"\nTop conditions:")
    for condition in result2['possible_conditions'][:3]:
        print(f"  - {condition['disease']}")
        print(f"    Match: {condition['match_score']} symptoms ({condition['match_percentage']}%)")
    
    print("\n---\n")
    
    # Test 3 — stomach + sick + hurt
    result3 = match_symptoms_to_diseases(["stomach", "sick", "hurt"])
    print(f"Input signs: {result3['input_signs']}")
    print(f"Urgency: {result3['urgency_level']}/10 — {result3['urgency_label']}")
    print(f"\nTop conditions:")
    for condition in result3['possible_conditions'][:3]:
        print(f"  - {condition['disease']}")
        print(f"    Match: {condition['match_score']} symptoms ({condition['match_percentage']}%)")