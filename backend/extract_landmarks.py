import os
import json
# pyrefly: ignore [missing-import]
import cv2
import mediapipe as mp
import numpy as np

# 1. Define our 12 target medical signs
MEDICAL_SIGNS = {
    "pain", "sick", "help", "medicine", "doctor", "headache", 
    "temperature", "dizzy", "emergency", "stomach", "cough", "hurt"
}

# 2. Paths matching your structure
JSON_PATH = os.path.join("..", "data", "wlasl", "WLASL_v0.3.json")
VIDEOS_DIR = os.path.join("..", "data", "wlasl", "videos")
OUTPUT_DIR = os.path.join("..", "data", "gestures")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 3. Initialize MediaPipe Tasks Hand Landmarker in IMAGE mode
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# Using IMAGE mode completely removes the timestamp verification rules
options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path='hand_landmarker.task'),
    running_mode=VisionRunningMode.IMAGE,
    num_hands=1,
    min_hand_detection_confidence=0.5
)

def extract_landmarks_from_video(video_path, landmarker):
    cap = cv2.VideoCapture(video_path)
    sequence_landmarks = []
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Convert OpenCV frame to MediaPipe Image object
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        
        # Run detection as an isolated, static image frame
        detection_result = landmarker.detect(mp_image)
        
        frame_landmarks = []
        if detection_result.hand_landmarks:
            # Grab the 21 keypoints of the first detected hand
            for lm in detection_result.hand_landmarks[0]:
                frame_landmarks.extend([lm.x, lm.y, lm.z])
        else:
            # Padding with zeros if no hand is detected in this frame
            frame_landmarks = [0.0] * (21 * 3)
            
        sequence_landmarks.append(frame_landmarks)
        
    cap.release()
    return sequence_landmarks

def extract_and_pad_sequence(video_path, landmarker, max_frames=30):
    raw_landmarks = extract_landmarks_from_video(video_path, landmarker)
    
    if len(raw_landmarks) >= max_frames:
        return raw_landmarks[:max_frames]
    else:
        padding = [[0.0] * (21 * 3)] * (max_frames - len(raw_landmarks))
        return raw_landmarks + padding

def process_dataset():
    print(f"🔄 Loading dataset index...")
    with open(JSON_PATH, 'r') as f:
        data = json.load(f)
        
    all_data = {}
    
    # Create the landmarker instance
    with HandLandmarker.create_from_options(options) as landmarker:
        for entry in data:
            word = entry["gloss"]
            if word in MEDICAL_SIGNS:
                print(f"📦 Processing signs for: '{word}'")
                all_data[word] = []
                
                for instance in entry["instances"]:
                    video_id = instance["video_id"]
                    video_file_name = f"{video_id}.mp4"
                    video_path = os.path.join(VIDEOS_DIR, video_file_name)
                    
                    if not os.path.exists(video_path):
                        continue
                    
                    landmarks_matrix = extract_and_pad_sequence(video_path, landmarker)
                    all_data[word].append(landmarks_matrix)
                    
        # Save structural dictionary arrays to disk
        np.save(os.path.join(OUTPUT_DIR, "medical_landmarks.npy"), all_data)
        print("🏁 Feature engineering complete! Saved arrays to data/gestures/medical_landmarks.npy")

if __name__ == "__main__":
    process_dataset()