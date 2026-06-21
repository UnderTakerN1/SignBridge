import os
import sys
import io
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
# Fix Windows console encoding for emoji/unicode characters
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import cv2
import base64
import time
import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from infermedica_handler import run_diagnosis_with_context, run_triage_with_context
import tempfile
import threading

camera_lock = threading.Lock()


# ── Import Our AI Components ───────────────────────
from gesture_detector import GestureDetector
from symptom_matcher import match_symptoms_to_diseases, get_urgency_label
from severity_predictor import calculate_detailed_severity, format_severity_for_display
from nlp_handler import generate_medical_summary, generate_sentence_from_signs


# Color mapping - convert word colors to hex for frontend
COLOR_HEX_MAP = {
    "red": "#ef4444",
    "orange": "#f97316", 
    "yellow": "#eab308",
    "green": "#22c55e"
}

# ── Flask + SocketIO Setup ─────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY'] = 'signbridge_secret_2026'
CORS(app, origins="*")
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    logger=False,
    engineio_logger=False,
    ping_interval=25,
    ping_timeout=60
)

# ── Global State ───────────────────────────────────
camera_active = False
camera_thread = None
detector = None
current_session = {
    "accumulated_signs": [],
    "follow_up_answers": {},
    "processing": False,
    "last_full_result": None
}

# ── Full AI Pipeline ───────────────────────────────
def run_full_pipeline(signs_sequence, follow_up_answers=None):
    """
    Run the complete AI pipeline:
    signs -> symptom matcher -> severity predictor -> Groq NLP -> result
    
    Parameters:
    - signs_sequence: list e.g. ["headache", "dizzy", "sick"]
    - follow_up_answers: dict e.g. {"duration": "2 days", "severity": "severe"}
    
    Returns: complete structured result for staff screen
    """
    print(f"\n{'='*50}")
    print(f"[PIPELINE] Running full pipeline for signs: {signs_sequence}")
    print(f"{'='*50}")
    
    try:
        # ── Step 1: Infermedica Diagnosis ─────────────────
        print("Step 1: Running Infermedica clinical diagnosis...")
        infermedica_result = run_diagnosis_with_context(
            signs_sequence=signs_sequence,
            follow_up_answers=follow_up_answers
        )
        print(f"[OK] Found {len(infermedica_result['possible_conditions'])} conditions")
        if infermedica_result['possible_conditions']:
            print(f"   Top: {infermedica_result['possible_conditions'][0]['disease']}")

        # ── Step 2: Infermedica Triage ────────────────────
        print("Step 2: Running Infermedica clinical triage...")
        triage_result = run_triage_with_context(
            signs_sequence=signs_sequence,
            follow_up_answers=follow_up_answers
        )
        print(f"[OK] Triage: {triage_result['label']} ({triage_result['score']}/100)")

        # Boost triage if patient reported severe symptoms
        if follow_up_answers:
            severity = follow_up_answers.get('severity', '').lower()
            if severity in ['severe', 'unbearable'] and triage_result['label'] == 'LOW':
                print("   [UP] Boosting triage from LOW to MEDIUM due to reported severity")
                triage_result = {
                    "label": "MEDIUM",
                    "score": 45,
                    "color": "#eab308",
                    "emoji": "YELLOW",
                    "action": "Schedule a doctor appointment today",
                    "time": "Within 24-48 hours"
                }

        # ── Step 2b: Keep Kaggle for symptom breakdown ────
        print("Step 2b: Getting symptom breakdown from Kaggle...")
        kaggle_data = match_symptoms_to_diseases(signs_sequence)
        severity_data = calculate_detailed_severity(
            normalized_symptoms=kaggle_data.get('normalized_symptoms', []),
            base_urgency=kaggle_data.get('urgency_level', 5)
        )

        # ── Step 3: Groq NLP Summary ──────────────
        print("Step 3: Generating AI summary with Groq...")
        ai_summary = generate_medical_summary(
            signs_sequence=signs_sequence,
            symptom_data=kaggle_data,
            follow_up_answers=follow_up_answers,
            infermedica_conditions=infermedica_result['possible_conditions']
        )
        # ── Step 4: Patient Sentence ──────────────
        print("Step 4: Building patient sentence...")
        patient_sentence = generate_sentence_from_signs(
            signs_sequence=signs_sequence,
            follow_up_answers=follow_up_answers
        )
        print(f"[OK] Sentence: {patient_sentence}")
        
        # ── Step 5: Build Final Result ────────────
        result = {
            "success": True,
            "signs_detected": signs_sequence,
            "patient_statement": patient_sentence,

            # Triage from Infermedica (clinical grade)
            "urgency_label": triage_result['label'],
            "urgency_score": triage_result['score'],
            "urgency_color": triage_result['color'],
            "urgency_emoji": triage_result['emoji'],
            "is_emergency": triage_result['label'] == "CRITICAL",
            "recommended_action": triage_result['action'],
            "time_to_doctor": triage_result['time'],

            # Conditions from Infermedica (real probabilities)
            "possible_conditions": [
                c['disease'] for c in infermedica_result['possible_conditions'][:3]
            ],
            "possible_conditions_detailed": [
                {
                    "disease": c['disease'],
                    "probability": c['probability'],
                    "match_percentage": c['probability'],
                    "description": c['description'],
                    "precautions": c['precautions']
                }
                for c in infermedica_result['possible_conditions'][:3]
            ],

            # Symptom breakdown from Kaggle (visual detail)
            "symptom_breakdown": severity_data.get('symptom_breakdown', []),

            # AI summary from Groq
            "ai_summary": ai_summary['summary'],
            "ai_success": ai_summary['success'],

            # Meta
            "follow_up_answers": follow_up_answers or {},
            "high_risk_combination": None,
            "requires_human_review": triage_result['label'] in ["CRITICAL", "HIGH"],
            "data_source": "infermedica+groq"
        }
        
        print(f"\n[OK] Pipeline complete!")
        print(f"   Emergency: {result['is_emergency']}")
        print(f"   Urgency: {result['urgency_label']}")
        print(f"   Conditions: {result['possible_conditions']}")        
        return result
        
    except Exception as e:
        print(f"[ERROR] Pipeline error: {e}")
        return {
            "success": False,
            "error": str(e),
            "signs_detected": signs_sequence,
            "patient_statement": f"Patient signed: {', '.join(signs_sequence)}",
            "urgency_label": "UNKNOWN",
            "urgency_score": 5,
            "urgency_color": "yellow",
            "urgency_emoji": "WARNING",
            "is_emergency": False,
            "recommended_action": "Manual assessment required",
            "time_to_doctor": "As soon as possible",
            "possible_conditions": [],
            "symptom_breakdown": [],
            "ai_summary": "AI summary unavailable. Please assess patient manually.",
            "ai_success": False,
            "follow_up_answers": follow_up_answers or {},
            "high_risk_combination": None,
            "requires_human_review": True
        }

# ── Camera Thread ──────────────────────────────────
def camera_loop():
    """
    Main camera processing loop
    Runs in background thread
    Sends frames and detections via WebSocket
    """
    
    global camera_active, detector, current_session
    
    print("\n[CAMERA] Starting camera loop...")
    
    # Small delay to ensure previous camera handle fully released
    time.sleep(0.3)
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("[ERROR] Camera not found!")
        socketio.emit('camera_error', {
            'message': 'Camera not found. Please check your camera connection.'
        })
        return
    
    # Set camera resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    print("[OK] Camera started!")
    frame_count = 0
    
    while camera_active:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to read frame")
            break
        
        # Process frame through gesture detector
        result = detector.process_frame(frame,mirror=False)
        
        # Send camera frame every 3rd frame (reduce bandwidth)
        frame_count += 1
        if frame_count % 3 == 0:
            _, buffer = cv2.imencode('.jpg', result["frame"], 
                                    [cv2.IMWRITE_JPEG_QUALITY, 70])
            frame_b64 = base64.b64encode(buffer).decode('utf-8')
            socketio.emit('camera_frame', {
                'frame': frame_b64,
                'hand_detected': result['hand_detected'],
                'current_prediction': result['current_prediction'],
                'confidence': round(result['confidence'] * 100, 1),
                'sequence_progress': len(detector.sequence),
                'sequence_length': 30
            })
        
        # New sign detected!
        if result['new_sign_detected']:
            sign = result['stable_sign']
            confidence = round(result['confidence'] * 100, 1)
            accumulated = result['accumulated_signs']
            
            print(f"\n[SIGN] Sign detected: {sign} ({confidence}%)")
            print(f"   Accumulated: {accumulated}")
            
            # Notify frontend of new sign
            socketio.emit('sign_detected', {
                'sign': sign,
                'confidence': confidence,
                'accumulated_signs': accumulated,
                'total_signs': len(accumulated)
            })
            # Auto-trigger pipeline once max signs reached (safety net)
            if len(accumulated) >= detector.max_accumulated and not current_session['processing']:
                print(f"\n[AUTO] Max signs reached ({len(accumulated)}), auto-running pipeline...")
                current_session['processing'] = True
                pipeline_result = run_full_pipeline(
                    signs_sequence=accumulated,
                    follow_up_answers=current_session.get('follow_up_answers', {})
                )
                current_session['last_full_result'] = pipeline_result
                current_session['processing'] = False
                socketio.emit('pipeline_result', pipeline_result)
            
            # Check if emergency sign
            if sign == 'emergency':
                print("[EMERGENCY] EMERGENCY SIGN DETECTED!")
                socketio.emit('emergency_alert', {
                    'message': 'EMERGENCY DETECTED - Immediate attention required!',
                    'sign': sign,
                    'confidence': confidence
                })
                
                # Run pipeline immediately for emergency
                if not current_session['processing']:
                    current_session['processing'] = True
                    pipeline_result = run_full_pipeline(
                        signs_sequence=accumulated,
                        follow_up_answers=current_session['follow_up_answers']
                    )
                    current_session['last_full_result'] = pipeline_result
                    current_session['processing'] = False
                    socketio.emit('pipeline_result', pipeline_result)
        
        # Small sleep to prevent CPU overload
        time.sleep(0.01)
    
    cap.release()
    print("[CAMERA] Camera stopped")

# ── WebSocket Events ───────────────────────────────

@socketio.on('connect')
def handle_connect():
    """Client connected"""
    print(f"\n[OK] Client connected: {request.sid}")
    emit('connected', {
        'message': 'Connected to SignBridge backend',
        'status': 'ready'
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected"""
    print(f"\n[DISCONNECTED] Client disconnected: {request.sid}")


@socketio.on('start_camera')
def handle_start_camera():
    global camera_active, camera_thread, detector
    
    with camera_lock:
        print("\n[START] Starting camera...")
        
        if camera_active:
            print("   [WARN] Camera already active, ignoring duplicate start")
            emit('camera_status', {'status': 'already_running', 'message': 'Camera already running'})
            return
        
        # Wait for any previous thread to fully finish first
        if camera_thread is not None and camera_thread.is_alive():
            print("   [WAIT] Waiting for previous camera thread to stop...")
            camera_thread.join(timeout=3)
        
        detector = GestureDetector()
        camera_active = True
        
        camera_thread = threading.Thread(target=camera_loop)
        camera_thread.daemon = True
        camera_thread.start()
        
        emit('camera_status', {'status': 'started', 'message': 'Camera started successfully'})
@socketio.on('stop_camera')
def handle_stop_camera():
    global camera_active
    
    with camera_lock:
        print("\n[STOP] Stopping camera...")
        camera_active = False
    
    emit('camera_status', {'status': 'stopped', 'message': 'Camera stopped'})


@socketio.on('submit_follow_up')
def handle_follow_up(data):
    """
    Receive follow-up answers from icon buttons
    Then run the full pipeline with complete context
    """
    global current_session
    
    print(f"\n[FOLLOW-UP] Follow-up answers received: {data}")
    
    # Save follow-up answers
    current_session['follow_up_answers'] = {
        'duration': data.get('duration', 'unknown'),
        'severity': data.get('severity', 'unknown'),
        'cause': data.get('cause', 'unknown'),
        'medicine': data.get('medicine', 'unknown')
    }
    
    # Get accumulated signs
    signs = current_session['accumulated_signs']
    
    if not signs and detector:
        signs = detector.accumulated_signs
    
    if not signs:
        emit('pipeline_error', {
            'message': 'No signs detected yet. Please perform signs first.'
        })
        return
    
    # Run full pipeline
    print(f"[PIPELINE] Running pipeline with signs: {signs}")
    emit('pipeline_status', {'status': 'processing', 'message': 'Analyzing symptoms...'})
    
    current_session['processing'] = True
    pipeline_result = run_full_pipeline(
        signs_sequence=signs,
        follow_up_answers=current_session['follow_up_answers']
    )
    current_session['last_full_result'] = pipeline_result
    current_session['processing'] = False
    
    # Send result to staff screen
    emit('pipeline_result', pipeline_result)
    print("[OK] Pipeline result sent to frontend")

@socketio.on('confirm_interpretation')
def handle_confirm(data):
    """
    Doctor confirms the AI interpretation
    Logs the confirmation
    """
    print(f"\n[CONFIRMED] Doctor confirmed interpretation")
    print(f"   Signs: {data.get('signs', [])}")
    print(f"   Confirmed by: doctor")
    
    emit('interpretation_confirmed', {
        'message': 'Interpretation confirmed by medical staff',
        'signs': data.get('signs', []),
        'timestamp': time.time(),
        'next_step': 'Proceed with consultation based on AI summary'
    })

@socketio.on('reset_session')
def handle_reset():
    """Reset for new patient"""
    global current_session, detector
    
    print("\n[RESET] Resetting session for new patient...")
    
    # Reset session data
    current_session = {
        "accumulated_signs": [],
        "follow_up_answers": {},
        "processing": False,
        "last_full_result": None
    }
    
    # Reset detector
    if detector:
        detector.reset_session()
    
    emit('session_reset', {
        'message': 'Session reset. Ready for new patient.',
        'status': 'ready'
    })
    print("[OK] Session reset complete")

@socketio.on('manual_pipeline_run')
def handle_manual_run(data):
    """
    Manually trigger pipeline with specific signs
    Useful for testing
    """
    signs = data.get('signs', [])
    follow_up = data.get('follow_up', {})
    
    if not signs:
        emit('pipeline_error', {'message': 'No signs provided'})
        return
    
    print(f"\n[MANUAL] Manual pipeline run: {signs}")
    emit('pipeline_status', {'status': 'processing'})
    
    result = run_full_pipeline(signs, follow_up)
    emit('pipeline_result', result)

@socketio.on('finish_signing')
def handle_finish_signing():
    """
    Patient clicks 'I'm done' button — run pipeline immediately
    with whatever signs have been accumulated so far
    """
    global detector, current_session
    
    if detector is None or not detector.accumulated_signs:
        emit('pipeline_error', {
            'message': 'No signs detected yet. Please sign first.'
        })
        return
    
    signs = detector.accumulated_signs
    print(f"\n[FINISH] Patient finished signing manually: {signs}")
    
    emit('pipeline_status', {'status': 'processing', 'message': 'Analyzing symptoms...'})
    
    current_session['processing'] = True
    pipeline_result = run_full_pipeline(
        signs_sequence=signs,
        follow_up_answers=current_session.get('follow_up_answers', {})
    )
    current_session['last_full_result'] = pipeline_result
    current_session['processing'] = False
    
    emit('pipeline_result', pipeline_result)
    print("[OK] Pipeline result sent (manual trigger)")

# ── HTTP Routes ────────────────────────────────────
@app.route('/finish_signing_http', methods=['POST'])
def finish_signing_http():
    """
    HTTP endpoint for 'I'm done' button - more reliable than 
    socket emit for client-to-server actions
    """
    global detector, current_session
    
    print("\n[FINISH-HTTP] Patient finished signing (HTTP)")
    
    if detector is None or not detector.accumulated_signs:
        return jsonify({'error': 'No signs detected yet'}), 400
    
    signs = detector.accumulated_signs
    print(f"   Signs: {signs}")
    
    current_session['processing'] = True
    pipeline_result = run_full_pipeline(
        signs_sequence=signs,
        follow_up_answers=current_session.get('follow_up_answers', {})
    )
    current_session['last_full_result'] = pipeline_result
    current_session['processing'] = False
    
    # Push result via socket (server->client direction, which works reliably)
    socketio.emit('pipeline_result', pipeline_result)
    
    return jsonify({'status': 'processing', 'message': 'Analysis started'})

@app.route('/upload_video_http', methods=['POST'])
def upload_video_http():
    """
    Simple, reliable HTTP endpoint for video upload.
    Bypasses Socket.IO entirely - just a plain file upload.
    """
    global detector
    
    print("\n[VIDEO-HTTP] Received video upload via HTTP POST")
    
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    video_file = request.files['video']
    
    if video_file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
    
    # Save to temp file
    temp_path = os.path.join(tempfile.gettempdir(), f"signbridge_upload_{int(time.time())}.mp4")
    video_file.save(temp_path)
    
    print(f"   Saved temp video: {temp_path}")
    
    # Verify it's a valid video
    test_cap = cv2.VideoCapture(temp_path)
    if not test_cap.isOpened():
        test_cap.release()
        os.remove(temp_path)
        return jsonify({'error': 'Invalid video file'}), 400
    
    test_fps = test_cap.get(cv2.CAP_PROP_FPS)
    test_frames = int(test_cap.get(cv2.CAP_PROP_FRAME_COUNT))
    test_cap.release()
    print(f"   Video verified: {test_fps} FPS, {test_frames} frames")
    
    # Initialize detector if needed
    if detector is None:
        detector = GestureDetector()
    
    # Process in background thread (will emit progress via Socket.IO as before)
    video_thread = threading.Thread(target=process_video_file, args=(temp_path,))
    video_thread.daemon = True
    video_thread.start()
    
    return jsonify({
        'status': 'processing',
        'message': 'Video received and processing started',
        'total_frames': test_frames,
        'fps': test_fps
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'running',
        'service': 'SignBridge Backend',
        'camera_active': camera_active,
        'components': {
            'lstm_model': 'loaded',
            'mediapipe': 'ready',
            'groq_nlp': 'connected',
            'symptom_matcher': 'ready',
            'severity_predictor': 'ready'
        }
    })

@app.route('/test_pipeline', methods=['POST'])
def test_pipeline():
    """
    HTTP endpoint to test the full pipeline
    POST body: {"signs": ["headache", "dizzy"], "follow_up": {...}}
    """
    data = request.get_json()
    signs = data.get('signs', ['headache', 'dizzy'])
    follow_up = data.get('follow_up', {})
    
    result = run_full_pipeline(signs, follow_up)
    return jsonify(result)

@app.route('/reset', methods=['POST'])
def reset():
    """HTTP reset endpoint"""
    global current_session, detector
    current_session = {
        "accumulated_signs": [],
        "follow_up_answers": {},
        "processing": False,
        "last_full_result": None
    }
    if detector:
        detector.reset_session()
    return jsonify({'status': 'reset', 'message': 'Session reset successfully'})


# ── Video File Processing ──────────────────────────
def process_video_file(video_path):
    """
    Process an uploaded video file through the gesture detector,
    frame by frame, same logic as live camera but reading from file
    """
    global detector, current_session
    
    print(f"\n[VIDEO] Processing uploaded video: {video_path}")
    
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print("[ERROR] Could not open video file")
        socketio.emit('video_error', {'message': 'Could not open video file'})
        return
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"   Video: {fps} FPS, {total_frames} frames")
    
    # Reset detector for fresh video processing
    detector.reset_session()
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        result = detector.process_frame(frame)
        
        # Send progress update every 10th frame
        if frame_count % 10 == 0:
            progress = round((frame_count / total_frames) * 100) if total_frames > 0 else 0
            socketio.emit('video_progress', {
                'progress': progress,
                'frame': frame_count,
                'total': total_frames
            })
        
        # Send frame preview every 3rd frame (like live camera)
        if frame_count % 3 == 0:
            _, buffer = cv2.imencode('.jpg', result["frame"], 
                                    [cv2.IMWRITE_JPEG_QUALITY, 70])
            frame_b64 = base64.b64encode(buffer).decode('utf-8')
            socketio.emit('camera_frame', {
                'frame': frame_b64,
                'hand_detected': result['hand_detected'],
                'current_prediction': result['current_prediction'],
                'confidence': round(result['confidence'] * 100, 1),
                'sequence_progress': len(detector.sequence),
                'sequence_length': 30
            })
        
        # New sign detected
        if result['new_sign_detected']:
            sign = result['stable_sign']
            confidence = round(result['confidence'] * 100, 1)
            accumulated = result['accumulated_signs']
            
            print(f"   [SIGN] Sign detected in video: {sign} ({confidence}%)")
            
            socketio.emit('sign_detected', {
                'sign': sign,
                'confidence': confidence,
                'accumulated_signs': accumulated,
                'total_signs': len(accumulated)
            })
            
            if sign == 'emergency':
                socketio.emit('emergency_alert', {
                    'message': 'EMERGENCY DETECTED - Immediate attention required!',
                    'sign': sign,
                    'confidence': confidence
                })
        
        time.sleep(1 / fps if fps > 0 else 0.03)
    
    cap.release()
    
    # Clean up temp file
    try:
        os.remove(video_path)
        print(f"   Cleaned up temp file: {video_path}")
    except OSError:
        pass
    
    final_signs = detector.accumulated_signs
    print(f"   [OK] Video processing complete. Signs detected: {final_signs}")

    socketio.emit('video_processing_complete', {
    'accumulated_signs': final_signs,
    'total_frames_processed': frame_count,
    'message': 'Video processing complete.'
})

    # Automatically run the full pipeline once video ends —
    # no follow-up icons available for uploaded videos, so we 
    # generate the summary immediately with whatever signs we found
    if final_signs:
        print(f"   [AUTO] Running pipeline automatically for uploaded video...")
        pipeline_result = run_full_pipeline(
        signs_sequence=final_signs,
        follow_up_answers=current_session.get('follow_up_answers', {})
        )
        socketio.emit('pipeline_result', pipeline_result)
    else:
        print("   [WARN] No signs detected in video — sending fallback result")
        socketio.emit('pipeline_result', {
        "success": False,
        "signs_detected": [],
        "patient_statement": "No signs were detected in the uploaded video.",
        "urgency_label": "UNKNOWN",
        "urgency_score": 0,
        "urgency_color": "#6b7280",
        "is_emergency": False,
        "recommended_action": "Please try recording the signs more clearly.",
        "possible_conditions": [],
        "possible_conditions_detailed": [],
        "ai_summary": "We couldn't detect any clear signs in this video. Please try again with better lighting or a clearer view of your hands.",
        "ai_success": False,
        "symptom_breakdown": [],
        "follow_up_answers": {},
        "requires_human_review": True
    })


@socketio.on('upload_video')
def handle_video_upload(data):
    """
    Receive base64 video data from frontend, save temporarily, process it
    data: {'video_data': '<base64 string>', 'filename': 'test.mp4'}
    """
    global detector
    
    print("\n[VIDEO] Received video upload request")
    
    try:
        video_b64 = data.get('video_data')
        filename = data.get('filename', 'upload.mp4')
        
        if not video_b64:
            emit('video_error', {'message': 'No video data received'})
            return
        
        print(f"   Filename: {filename}")
        print(f"   Data length: {len(video_b64)} chars")
        
        # Decode base64 to binary — strip data URL prefix if present
        if ',' in video_b64:
            video_b64 = video_b64.split(',', 1)[1]
        
        video_bytes = base64.b64decode(video_b64)
        print(f"   Decoded size: {len(video_bytes)} bytes")
        
        if len(video_bytes) < 1000:
            emit('video_error', {'message': 'Video file too small or corrupted'})
            return
        
        # Save to temp file
        temp_path = os.path.join(tempfile.gettempdir(), f"signbridge_upload_{int(time.time())}.mp4")
        with open(temp_path, 'wb') as f:
            f.write(video_bytes)
        
        print(f"   Saved temp video: {temp_path}")
        
        # Verify the video can be opened by OpenCV
        test_cap = cv2.VideoCapture(temp_path)
        if not test_cap.isOpened():
            test_cap.release()
            os.remove(temp_path)
            emit('video_error', {'message': 'Video file could not be read. Please try a different format (MP4 recommended).'})
            return
        
        test_fps = test_cap.get(cv2.CAP_PROP_FPS)
        test_frames = int(test_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        test_cap.release()
        print(f"   Video verified: {test_fps} FPS, {test_frames} frames")
        
        # Initialize detector if not already
        if detector is None:
            detector = GestureDetector()
        
        emit('video_upload_received', {
            'message': 'Video received, processing...',
            'total_frames': test_frames,
            'fps': test_fps
        })
        
        video_thread = threading.Thread(target=process_video_file, args=(temp_path,))
        video_thread.daemon = True
        video_thread.start()
        
    except Exception as e:
        print(f"   [ERROR] Video upload error: {e}")
        import traceback
        traceback.print_exc()
        emit('video_error', {'message': f'Video upload failed: {str(e)}'})

# ── Start Server ───────────────────────────────────
if __name__ == '__main__':
    print("\n" + "="*50)
    print("SignBridge Backend Starting...")
    print("="*50)
    print(f"   URL: http://localhost:5000")
    print(f"   Health: http://localhost:5000/health")
    print(f"   Test: http://localhost:5000/test_pipeline")
    print("="*50 + "\n")
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False,
        allow_unsafe_werkzeug=True
    )
