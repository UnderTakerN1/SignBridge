import cv2
import numpy as np
from gesture_detector import GestureDetector
import os

def test_video(video_path, expected_sign):
    """
    Run a video file through the gesture detector
    and see what it predicts vs the expected sign
    """
    print(f"\n{'='*50}")
    print(f"Testing: {video_path}")
    print(f"Expected sign: {expected_sign}")
    print(f"{'='*50}\n")
    
    detector = GestureDetector()
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print("❌ Could not open video file!")
        return
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Video info: {fps} FPS, {total_frames} frames\n")
    
    all_predictions = []
    
    frame_num = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_num += 1
        result = detector.process_frame(frame)
        
        if result['current_prediction']:
            conf = round(result['confidence'] * 100, 1)
            print(f"Frame {frame_num}: {result['current_prediction']} ({conf}%)")
            all_predictions.append((result['current_prediction'], result['confidence']))
        
        if result['new_sign_detected']:
            print(f"\n🤟 CONFIRMED SIGN: {result['stable_sign']} ({round(result['confidence']*100,1)}%)\n")
    
    cap.release()
    
    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    
    if all_predictions:
        # Most common prediction across all frames
        from collections import Counter
        labels = [p[0] for p in all_predictions]
        most_common = Counter(labels).most_common(3)
        
        print(f"Top predictions across video:")
        for label, count in most_common:
            avg_conf = np.mean([p[1] for p in all_predictions if p[0] == label]) * 100
            print(f"  {label}: appeared {count} times, avg confidence {round(avg_conf,1)}%")
        
        is_correct = most_common[0][0] == expected_sign
        print(f"\n{'✅ CORRECT' if is_correct else '❌ INCORRECT'}")
        print(f"Expected: {expected_sign}, Got: {most_common[0][0]}")
    else:
        print("❌ No predictions made — hand not detected properly")


if __name__ == "__main__":
    # Update these paths to point to actual ASL Citizen video files
    BASE_DIR = "../data/ASL_Citizen/videos"
    
    # Test with a few different signs from ASL Citizen test set
    test_cases = [
        # (filename, expected_sign) - we'll fill these from the CSV
    ]
    
    import pandas as pd
    test_csv = pd.read_csv("../data/ASL_Citizen/splits/test.csv")
    
    our_signs_map = {
        "PAIN": "pain", "SICK": "sick", "HELP": "help",
        "MEDICINE": "medicine", "DOCTOR1": "doctor",
        "HEADACHE": "headache", "HOT": "temperature",
        "DIZZY": "dizzy", "DANGER": "emergency",
        "STOMACH": "stomach", "COUGH": "cough", "HURT": "hurt"
    }
    
    # Pick one test video per sign
    for gloss, our_label in our_signs_map.items():
        matches = test_csv[test_csv['Gloss'] == gloss]
        if len(matches) > 0:
            video_file = matches.iloc[0]['Video file']
            video_path = os.path.join(BASE_DIR, video_file)
            test_video(video_path, our_label)