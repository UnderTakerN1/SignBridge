# SignBridge 

**AI-powered ASL sign language interpreter that lets deaf and hard-of-hearing patients communicate symptoms to medical staff in real time — no interpreter required.**

Built for the **USAII Global AI Hackathon 2026** — Public Services Track: *Fix Systems People Depend On (Direction : Benefits Navigator)*.

---

## The Problem

Deaf and hard-of-hearing patients face a critical, often invisible barrier in healthcare. When they walk into a clinic without a human interpreter present, they have no fast way to communicate symptoms to a doctor or caseworker. Professional interpreters are expensive and frequently unavailable on short notice — community clinics in particular often have no access to one at all.

The result: patients either go without care, or get misunderstood at exactly the moment it matters most.

## What SignBridge Does

A patient signs their symptoms in ASL directly to a camera — live webcam or an uploaded video. SignBridge recognizes the signs, runs them through a real clinical diagnosis engine, and generates a structured, doctor-ready summary in seconds. No interpreter, no delay.


---

## How It Works

👋 Sign  →  👁️ Computer Vision  →  🧠 Clinical AI  →  💬 Doctor Summary

### 1. Computer Vision — Sign Recognition

- **Google MediaPipe** extracts 21 hand landmarks (x, y, z) per video frame.
- A custom **two-layer LSTM neural network** classifies a 30-frame motion sequence into one of **12 medical ASL signs**: `pain`, `sick`, `help`, `medicine`, `doctor`, `headache`, `temperature` (fever), `dizzy`, `emergency`, `stomach`, `cough`, `hurt`.
- Sequences shorter than 30 frames are resampled via linear interpolation, so the model can still make a prediction even on briefer signs.
- A patient can either sign live, or upload a pre-recorded `.mp4` — both paths run through the same detection pipeline.

### 2. Clinical AI — Diagnosis & Triage

- Recognized signs are mapped to clinical symptom codes and sent to the **[Infermedica API](https://infermedica.com/)** — a real diagnosis and triage engine used by healthcare companies, covering 1,700+ symptoms.
- Infermedica returns probability-ranked possible conditions and an evidence-based urgency level (e.g. *"see a doctor within 24 hours"*).
- If the patient indicates their symptoms are severe via a quick follow-up step, the urgency assessment is adjusted accordingly.

### 3. Language AI — Plain-Language Summary

- **Groq (Llama 3.3-70B)** converts the clinical output into a short, structured summary for medical staff — always framed as *"may indicate,"* never a definitive diagnosis.
- The summary includes suggested follow-up questions for the doctor to ask directly.

### 4. Output — Staff Screen

The doctor/caseworker sees: the patient's statement, top 3 possible conditions with probabilities, a color-coded urgency level, a recommended action and timeframe, and a **"Confirm Interpretation"** button they must click before proceeding.

---

## Model Validation — Built On Honesty, Not Just Numbers

We deliberately validated our model the way a credible system should be validated, not the way that produces the best-looking number.

**What went wrong first:** Our initial model reported **91% accuracy**. Investigating further, we found our train/test split was happening *after* data augmentation — meaning augmented copies of the same source video could end up in both the training and test sets. The model wasn't generalizing; it was recognizing its own duplicated examples.

**What we fixed:** We rebuilt the pipeline to split by **original video first**, then augment only the training set, leaving the test set clean and untouched. Re-validated honestly, our real accuracy was closer to 40% — with our original tiny dataset of 88 videos (~7 per sign).

**How we actually solved it:** We migrated from WLASL (the most commonly used ASL dataset, but ~52% of its video links are now dead) to **[ASL Citizen](https://www.microsoft.com/en-us/research/project/asl-citizen/)** (Microsoft Research) — a dataset purpose-recorded by Deaf/HoH community members, hosted directly rather than scraped from expired links. This took us from ~7 videos/sign to ~30 videos/sign across all 12 signs.

**Final, honestly validated result:** Testing against real, unseen ASL Citizen test videos — performed by signers the model had never seen during training — our model correctly recognized **10 of 12 signs reliably** (~83% practical accuracy), with the two weakest signs (`help`, `emergency`) compensated for by our triage architecture below.

| Component | Detail |
|---|---|
| Training videos | 367 (≈30 per sign) |
| Augmentation | Mirroring, time-warping, rotation, noise, translation — applied only to the training split |
| Architecture | 2-layer LSTM (64 units each), dropout 0.4, trained with early stopping on validation accuracy |
| Validation method | Held-out test videos from real, unseen ASL Citizen signers |

---

## Why AI — and Why Not Something Simpler

A static phrasebook or keyword search can show a single word's translation, but it can't:
- Recognize *movement over time* (a sign isn't a static pose — it's a 30-frame sequence)
- Combine multiple symptoms into a coherent clinical picture
- Weigh urgency based on symptom combinations
- Adapt its follow-up questions based on context

We needed sequence-based computer vision for the first point, and a real clinical reasoning engine for the rest — a rules-based lookup table could not do either.

---

## Responsible AI & Human Oversight

SignBridge **never makes a diagnosis.** The AI's job ends at giving medical staff a clear, fast starting point — the decision is always made by a human.

- Every output is explicitly framed as **"may indicate,"** never a diagnosis.
- Medical staff must click **"Confirm Interpretation"** before any action proceeds.
- Sign detection confidence is shown live; predictions below **85%** confidence (raised to **93%** specifically for the safety-critical "emergency" sign) are not accepted as final.
- **The emergency safety net doesn't depend on one fragile gesture.** Our clinical triage engine evaluates the full symptom *combination*, so even if a single sign is misread, a dangerous combination of symptoms can still trigger a high-urgency flag for mandatory human review.

---

## Tech Stack

**Backend:** Python, Flask, Flask-SocketIO, OpenCV, MediaPipe, TensorFlow/Keras, Pandas, scikit-learn

**AI / APIs:** Custom LSTM (TensorFlow), Groq (Llama 3.3-70B), Infermedica Clinical API

**Frontend:** React, Vite, Socket.IO Client

---

## Project Structure

signbridge/

├── backend/

│   ├── app.py                    # Flask + SocketIO server, full pipeline orchestration

│   ├── gesture_detector.py       # MediaPipe + LSTM sign recognition

│   ├── train_model.py            # LSTM training with proper train/test split + augmentation

│   ├── extract_asl_citizen.py    # Landmark extraction from ASL Citizen videos

│   ├── infermedica_handler.py    # Clinical diagnosis + triage API integration

│   ├── nlp_handler.py            # Groq summary generation

│   ├── symptom_matcher.py        # Kaggle-based symptom breakdown (supplementary detail)

│   └── severity_predictor.py     # Supplementary severity scoring

├── frontend/

│   └── src/

│       ├── pages/

│       │   ├── LandingScreen.jsx

│       │   ├── PatientModeSelect.jsx

│       │   ├── PatientScreen.jsx

│       │   └── StaffScreen.jsx

│       └── ThemeContext.jsx

└── data/

├── gestures/                 # Trained model + labels

└── symptoms/                 # Kaggle symptom-severity reference data


---

## Setup

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Create `backend/.env` (see `backend/.env.example`):

GROQ_API_KEY=your_groq_api_key_here

INFERMEDICA_APP_ID=your_infermedica_app_id_here

INFERMEDICA_APP_KEY=your_infermedica_app_key_here

Run it:

```bash
python app.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`

---

## Data Sources

- **[ASL Citizen](https://www.microsoft.com/en-us/research/project/asl-citizen/)** (Microsoft Research) — primary training data, ~30 videos/sign across our 12 medical signs.
- **[WLASL](https://dxli94.github.io/WLASL-Home/)** — used in early development; discontinued as primary source after finding ~52% of video links no longer accessible.
- **[Disease-Symptom Description Dataset](https://www.kaggle.com/datasets/itachi9604/disease-symptom-description-dataset)** (Kaggle) — supplementary symptom-severity reference shown alongside Infermedica's clinical output.
- **Infermedica clinical knowledge base** — accessed via API, not stored or redistributed.

No synthetic or fabricated patient data was used. All training data consists of real recorded ASL performances from public research datasets.

---

## What's Next

- **Beyond isolated signs** — move from single-word recognition to continuous sign language recognition, so patients can sign full sentences instead of individual symptoms.
- **Facial expression and body tracking** — real ASL grammar relies heavily on facial markers and body-relative pointing, especially for signs indicating a body location. We'd integrate MediaPipe Holistic to capture this, not just hand landmarks.
- **Expand the sign vocabulary** — with more training data per sign, reliably support significantly more medical terms beyond our current 12.
- **Full clinical scoring** — route 100% of urgency assessment through Infermedica's validated triage engine, retiring our supplementary Kaggle-based severity reference entirely.
- **Direct collaboration with the Deaf community** — our training data is purpose-recorded but still dictionary-style. Real-world deployment needs Deaf signers directly involved in data collection, model evaluation, and interface design.
- **Pilot in a real clinical setting** — test with real patients and staff under appropriate protocols, beyond a hackathon demo.

---

*This project was built with AI coding assistance for debugging and giving life to this project,  helping also with architecture planning, and parts of this documentation. The main ideas , all core design decisions, testing, and validation were performed and verified by our team.*