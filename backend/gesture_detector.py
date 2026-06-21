import cv2
import numpy as np
import tensorflow as tf
import os
import time
from collections import Counter
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

# ── Load LSTM Model ────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, '..', 'data', 'gestures', 'signbridge_lstm_model.keras')
LABELS_PATH = os.path.join(BASE_DIR, '..', 'data', 'gestures', 'labels.npy')
HAND_MODEL_PATH = os.path.join(BASE_DIR, '..', 'data', 'hand_landmarker.task')

# Load LSTM model
print("[LOADING] LSTM model...")
lstm_model = tf.keras.models.load_model(MODEL_PATH)
print("[OK] LSTM Model loaded!")

# Load labels
raw_labels = np.load(LABELS_PATH, allow_pickle=True)
if isinstance(raw_labels, np.ndarray) and raw_labels.shape == ():
    labels = list(raw_labels.item().keys())
else:
    labels = [str(l) for l in raw_labels]
print(f"[OK] Labels: {labels}")

# ── MediaPipe New Tasks API Setup ──────────────────
base_options = mp_python.BaseOptions(
    model_asset_path=HAND_MODEL_PATH
)
hand_options = mp_vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.4,
    min_hand_presence_confidence=0.4,
    min_tracking_confidence=0.3
)
hand_landmarker = mp_vision.HandLandmarker.create_from_options(hand_options)
print("[OK] MediaPipe Hand Landmarker ready!")

# ── Gesture Detector Class ─────────────────────────
class GestureDetector:
    def __init__(self):
        # Sequence buffer — stores last 30 frames of landmarks
        self.sequence = []
        self.sequence_length = 30
        
        # Prediction smoothing — last 5 predictions
        self.prediction_history = []
        self.history_length = 5
        
        # Cooldown — prevent spam predictions
        self.last_prediction_time = 0
        self.cooldown_seconds = 4
        
        # Accumulated signs for multi-sign session
        self.accumulated_signs = []
        self.max_accumulated = 5

        # FIXED: Relocated inside the instance constructor namespace
        self.HAND_CONNECTIONS = [
            (0,1),(1,2),(2,3),(3,4),
            (0,5),(5,6),(6,7),(7,8),
            (0,9),(9,10),(10,11),(11,12),
            (0,13),(13,14),(14,15),(15,16),
            (0,17),(17,18),(18,19),(19,20),
            (5,9),(9,13),(13,17)
        ]
    
    def extract_landmarks(self, frame):
        """Extract 63 landmark values using new MediaPipe API"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )
    
        detection_result = hand_landmarker.detect(mp_image)
    
        if detection_result.hand_landmarks:
            hand_lms = detection_result.hand_landmarks[0]
        
            landmarks = []
            for lm in hand_lms:
                landmarks.extend([lm.x, lm.y, lm.z])
        
            return np.array(landmarks), hand_lms
    
        return None, None
    
    def predict_sign(self):
        # Allow prediction with as few as 15 frames by resampling up to 30
        if len(self.sequence) < 15:
            return None, 0.0
    
        # Take whatever we have and resample to sequence_length
        raw_sequence = np.array(self.sequence)
    
        if len(raw_sequence) != self.sequence_length:
            # Resample to exactly 30 frames using interpolation
            original_len = raw_sequence.shape[0]
            indices = np.linspace(0, original_len - 1, self.sequence_length)
            resampled = np.zeros((self.sequence_length, raw_sequence.shape[1]), dtype=np.float32)
            for i in range(raw_sequence.shape[1]):
                resampled[:, i] = np.interp(indices, np.arange(original_len), raw_sequence[:, i])
            input_data = resampled.reshape(1, self.sequence_length, 63)
        else:
            input_data = raw_sequence.reshape(1, self.sequence_length, 63)
    
        prediction = self.model_predict(input_data)
    
        predicted_index = np.argmax(prediction)
        confidence = float(prediction[predicted_index])
    
        if max(prediction) == 0.0:
            return None, 0.0

        if predicted_index < len(labels):
            predicted_label = labels[predicted_index]
        else:
            return None, 0.0
    
        self.prediction_history.append(predicted_label)
        if len(self.prediction_history) > self.history_length:
            self.prediction_history.pop(0)
    
        return predicted_label, confidence

    def model_predict(self, input_data):
        """Wrapper for model prediction"""
        return lstm_model.predict(input_data, verbose=0)[0]
        
    def get_smoothed_prediction(self):
        """Get most common prediction from history"""
        if not self.prediction_history:
            return None
        
        from collections import Counter
        counter = Counter(self.prediction_history)
        most_common = counter.most_common(1)[0]
        label, count = most_common
    
        required_count = 5 if label == 'emergency' else 4
    
        if count >= required_count:
            return label
    
        return None
    
    def process_frame(self, frame,mirror=True):
        """Main processing function — call this for every camera frame"""
        result = {
            "hand_detected": False,
            "landmarks": None,
            "current_prediction": None,
            "confidence": 0.0,
            "stable_sign": None,
            "new_sign_detected": False,
            "accumulated_signs": self.accumulated_signs.copy(),
            "frame": frame
        }
        if mirror : 
            frame = cv2.flip(frame, 1)
        landmarks, hand_landmarks = self.extract_landmarks(frame)
        
        if landmarks is not None:
            result["hand_detected"] = True
            result["landmarks"] = landmarks
            
            self.sequence.append(landmarks)
            if len(self.sequence) > self.sequence_length:
                self.sequence.pop(0)
            
            # FIXED: Linked your loop directly to your skeletal drawer helper method
            frame = self.draw_landmarks(frame, hand_landmarks)
            
            if len(self.sequence) >= 15:
                predicted_label, confidence = self.predict_sign()
                result["current_prediction"] = predicted_label
                result["confidence"] = confidence
                
                stable_sign = self.get_smoothed_prediction()
                result["stable_sign"] = stable_sign
                
                current_time = time.time()
                time_since_last = current_time - self.last_prediction_time
                
                required_confidence = 0.93 if stable_sign == 'emergency' else 0.85

                if (stable_sign and 
                    confidence >= required_confidence and 
                    time_since_last >= self.cooldown_seconds):
                    
                    result["new_sign_detected"] = True
                    self.last_prediction_time = current_time
                    
                    # Add to accumulated signs only if it's a new unique consecutive sign
                    if len(self.accumulated_signs) < self.max_accumulated:
                        if not self.accumulated_signs or self.accumulated_signs[-1] != stable_sign:
                            self.accumulated_signs.append(stable_sign)
                    
                    result["accumulated_signs"] = self.accumulated_signs.copy()
                    
                    self.sequence = []
                    self.prediction_history = []
        
        else:
            if len(self.sequence) > 0:
                self.sequence.pop(0)
        
        frame = self._draw_info(frame, result)
        result["frame"] = frame
        
        return result
    
    def _draw_info(self, frame, result):
        """Draw prediction info on the camera frame"""
        h, w, _ = frame.shape
        cv2.rectangle(frame, (0, 0), (w, 80), (0, 0, 0), -1)
        
        if result["hand_detected"]:
            status = f"Hand detected | Frames: {len(self.sequence)}/30"
            cv2.putText(frame, status, (10, 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "No hand detected", (10, 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        if result["current_prediction"]:
            conf_pct = round(result["confidence"] * 100, 1)
            pred_text = f"Prediction: {result['current_prediction']} ({conf_pct}%)"
            color = (0, 255, 0) if result["confidence"] >= 0.75 else (0, 165, 255)
            cv2.putText(frame, pred_text, (10, 55),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        if result["accumulated_signs"]:
            signs_text = "Signs: " + " → ".join(result["accumulated_signs"])
            cv2.rectangle(frame, (0, h-40), (w, h), (0, 0, 0), -1)
            cv2.putText(frame, signs_text, (10, h-15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        return frame
    
    def reset_session(self):
        """Reset for new patient session"""
        self.sequence = []
        self.prediction_history = []
        self.accumulated_signs = []
        self.last_prediction_time = 0
        print("[OK] Session reset")
    
    def draw_landmarks(self, frame, hand_landmarks):
        """Public method to draw landmarks on frame using new Tasks API"""
        if hand_landmarks:
            h, w, _ = frame.shape
            for start_idx, end_idx in self.HAND_CONNECTIONS:
                if start_idx < len(hand_landmarks) and end_idx < len(hand_landmarks):
                    pt1 = (int(hand_landmarks[start_idx].x * w), int(hand_landmarks[start_idx].y * h))
                    pt2 = (int(hand_landmarks[end_idx].x * w), int(hand_landmarks[end_idx].y * h))
                    cv2.line(frame, pt1, pt2, (255, 255, 255), 2) # Clean white skeletal bone lines
            
            for lm in hand_landmarks:
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1) # High-visibility green nodes
        return frame


# ── Quick Camera Test ──────────────────────────────
if __name__ == "__main__":
    print("\n=== SignBridge Gesture Detector Test ===")
    print("Show your hand and perform signs!")
    print("Press 'q' to quit, 'r' to reset session\n")
    
    detector = GestureDetector()
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Camera not found!")
        exit()
    
    print("✅ Camera opened successfully!")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        result = detector.process_frame(frame)
        
        if result["new_sign_detected"]:
            print(f"\n🤟 NEW SIGN DETECTED: {result['stable_sign']}")
            print(f"   Confidence: {round(result['confidence']*100, 1)}%")
            print(f"   All signs so far: {result['accumulated_signs']}")
        
        cv2.imshow('SignBridge — Gesture Detector', result["frame"])
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r'):
            detector.reset_session()
            print("Session reset!")
    
    cap.release()
    cv2.destroyAllWindows()