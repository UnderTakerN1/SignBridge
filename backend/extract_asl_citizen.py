import os
import cv2
import numpy as np
import pandas as pd
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

# ── Paths ───────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASL_CITIZEN_DIR = os.path.join(BASE_DIR, '..', 'data', 'ASL_Citizen')
VIDEOS_DIR = os.path.join(ASL_CITIZEN_DIR, 'videos')
SPLITS_DIR = os.path.join(ASL_CITIZEN_DIR, 'splits')
HAND_MODEL_PATH = os.path.join(BASE_DIR, '..', 'data', 'hand_landmarker.task')
OUTPUT_PATH = os.path.join(BASE_DIR, '..', 'data', 'gestures', 'medical_landmarks_v2.npy')

SEQUENCE_LENGTH = 30  # frames per sample

# ── Our 12 Signs Mapped To ASL Citizen Glosses ─────
SIGN_TO_GLOSS = {
    "pain": "PAIN",
    "sick": "SICK",
    "help": "HELP",
    "medicine": "MEDICINE",
    "doctor": "DOCTOR1",
    "headache": "HEADACHE",
    "temperature": "HOT",
    "dizzy": "DIZZY",
    "emergency": "DANGER",
    "stomach": "STOMACH",
    "cough": "COUGH",
    "hurt": "HURT"
}

# ── MediaPipe Setup ─────────────────────────────────
base_options = mp_python.BaseOptions(model_asset_path=HAND_MODEL_PATH)
hand_options = mp_vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5
)
hand_landmarker = mp_vision.HandLandmarker.create_from_options(hand_options)
print("✅ MediaPipe Hand Landmarker ready!\n")


def extract_landmarks_from_frame(frame):
    """Extract 63 values (21 landmarks x,y,z) from a single frame"""
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    detection_result = hand_landmarker.detect(mp_image)

    if detection_result.hand_landmarks:
        hand_lms = detection_result.hand_landmarks[0]
        landmarks = []
        for lm in hand_lms:
            landmarks.extend([lm.x, lm.y, lm.z])
        return np.array(landmarks, dtype=np.float32)

    return None


def process_video(video_path):
    """
    Process a single video file, extract hand landmarks for each frame,
    and resample to exactly SEQUENCE_LENGTH frames.
    Returns None if no hand was detected in enough frames.
    """
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        return None

    frame_landmarks = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        landmarks = extract_landmarks_from_frame(frame)
        if landmarks is not None:
            frame_landmarks.append(landmarks)

    cap.release()

    # Need at least a few frames with detected hands to be useful
    if len(frame_landmarks) < 5:
        return None

    frame_landmarks = np.array(frame_landmarks, dtype=np.float32)

    # Resample to exactly SEQUENCE_LENGTH frames using linear interpolation
    original_len = frame_landmarks.shape[0]
    indices = np.linspace(0, original_len - 1, SEQUENCE_LENGTH)

    resampled = np.zeros((SEQUENCE_LENGTH, frame_landmarks.shape[1]), dtype=np.float32)
    for i in range(frame_landmarks.shape[1]):
        resampled[:, i] = np.interp(indices, np.arange(original_len), frame_landmarks[:, i])

    return resampled


def main():
    print("🔄 Loading ASL Citizen splits...")
    train = pd.read_csv(os.path.join(SPLITS_DIR, 'train.csv'))
    val = pd.read_csv(os.path.join(SPLITS_DIR, 'val.csv'))
    test = pd.read_csv(os.path.join(SPLITS_DIR, 'test.csv'))
    all_data = pd.concat([train, val, test])

    final_dataset = {}

    for our_sign, gloss in SIGN_TO_GLOSS.items():
        print(f"\n{'='*50}")
        print(f"Processing sign: '{our_sign}' (gloss: '{gloss}')")
        print(f"{'='*50}")

        matching_rows = all_data[all_data['Gloss'] == gloss]
        print(f"Found {len(matching_rows)} videos for this gloss")

        sequences = []
        skipped = 0

        for idx, row in matching_rows.iterrows():
            video_filename = row['Video file']
            video_path = os.path.join(VIDEOS_DIR, video_filename)

            if not os.path.exists(video_path):
                skipped += 1
                continue

            result = process_video(video_path)

            if result is not None:
                sequences.append(result)
                print(f"  ✅ {video_filename} — {result.shape}")
            else:
                skipped += 1
                print(f"  ⚠️ {video_filename} — no hand detected, skipped")

        final_dataset[our_sign] = sequences
        print(f"\n📊 '{our_sign}': {len(sequences)} usable videos ({skipped} skipped)")

    # ── Save Final Dataset ─────────────────────────
    print(f"\n{'='*50}")
    print("📋 FINAL SUMMARY")
    print(f"{'='*50}")
    total = 0
    for sign, seqs in final_dataset.items():
        print(f"  {sign}: {len(seqs)} videos")
        total += len(seqs)
    print(f"\nTotal usable videos: {total}")

    np.save(OUTPUT_PATH, final_dataset)
    print(f"\n💾 Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()