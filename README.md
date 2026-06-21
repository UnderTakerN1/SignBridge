# SignBridge 

AI-powered ASL sign language interpreter that helps deaf and hard-of-hearing patients communicate symptoms to medical staff — in real time, no interpreter required.

It was built for **USAII Global AI Hackathon 2026** — In the Public Services Track: Fix Systems People Depend On (Benefits Navigator).

---

## The core Problem

Deaf and hard-of-hearing patients face a critical barrier in healthcare: without a human interpreter present, they have no fast way to communicate symptoms to medical staff. Professional interpreters are expensive and rarely available on short notice — so patients either go without care, or get misunderstood at moments that matter most.

## What It Does

A patient signs their symptoms in ASL directly to a camera (live webcam or uploaded video). SignBridge recognizes the signs, runs them through a real clinical diagnosis engine, and generates a structured, doctor-ready summary — all in seconds, with no interpreter required.

## How It Works
👋 Sign → 👁️ Computer Vision → 🧠 Clinical AI → 💬 Doctor Summary

1. **Computer Vision** — Google MediaPipe extracts hand landmarks; a custom-trained LSTM neural network classifies 30-frame motion sequences into one of 12 medical ASL signs.
2. **Clinical AI** — Recognized signs are sent to the **Infermedica API**, a clinical-grade diagnosis and triage engine, which returns probability-ranked conditions and an urgency level.
3. **Language AI** — **Groq (Llama 3.3)** converts the clinical output into a plain-language summary for medical staff, always framed as "may indicate," never a diagnosis.

## Tech Stack

**Backend:** Python, Flask, Flask-SocketIO, OpenCV, MediaPipe, TensorFlow/Keras, Groq API, Infermedica API, Pandas

**Frontend:** React, Vite, Socket.IO Client

## Validated Performance

We tested our model on real, unseen ASL Citizen test videos (signers never seen during training) — not just our own testing:

- **12 medical signs** recognized: pain, sick, help, medicine, doctor, headache, fever, dizzy, emergency, stomach, cough, hurt
- **~83% real-world accuracy** on unseen signers
- Trained on 367 videos (~30 per sign) from [ASL Citizen](https://www.microsoft.com/en-us/research/project/asl-citizen/) (Microsoft Research)

We caught and fixed a real data leakage bug during development — our first model reported a misleading 91% accuracy due to train/test contamination from data augmentation; honest re-validation revealed the true number and let us fix it properly.

## Setup

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

Create a `.env` file in `backend/` (see `.env.example`):
GROQ_API_KEY=your_groq_api_key_here

INFERMEDICA_APP_ID=your_infermedica_app_id_here

INFERMEDICA_APP_KEY=your_infermedica_app_key_here

Run the backend:
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

## Responsible AI

SignBridge never makes a diagnosis. Every output is framed as "may indicate," and medical staff must click **"Confirm Interpretation"** before any action is taken. Cases with low confidence or high/critical urgency are flagged for mandatory human review — the AI's role is to bridge communication, not replace clinical judgment.

## What's Next

- Expand from isolated signs to continuous conversational ASL
- Add facial expression and body-position tracking (MediaPipe Holistic) — real ASL grammar depends on it
- Validate directly with the Deaf community

## Team

Built by [Your Name] and [Person B's Name] in 7 days.

---

*Data sources: [ASL Citizen](https://www.microsoft.com/en-us/research/project/asl-citizen/) (Microsoft Research), [Disease-Symptom Description Dataset](https://www.kaggle.com/datasets/itachi9604/disease-symptom-description-dataset) (Kaggle), Infermedica clinical knowledge base.*
