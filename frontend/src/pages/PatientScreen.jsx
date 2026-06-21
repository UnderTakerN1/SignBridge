import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import socket from '../socket';
import { useTheme } from '../ThemeContext';

const resourceLinks = {
  'Pain': 'https://www.signingsavvy.com/sign/PAIN',
  'Headache': 'https://www.signingsavvy.com/sign/HEADACHE',
  'Dizzy': 'https://www.signingsavvy.com/sign/DIZZY',
  'Stomach': 'https://www.signingsavvy.com/sign/STOMACH',
  'Cough': 'https://www.signingsavvy.com/sign/COUGH',
  'Fever': 'https://www.signingsavvy.com/sign/FEVER',
  'Help': 'https://www.signingsavvy.com/sign/HELP',
  'Doctor': 'https://www.signingsavvy.com/sign/DOCTOR',
};

function PatientScreen() {
  const navigate = useNavigate();
  const { mode } = useParams();
  const { colors, theme, toggleTheme } = useTheme();

  const [frame, setFrame] = useState(null);
  const [handDetected, setHandDetected] = useState(false);
  const [currentPrediction, setCurrentPrediction] = useState(null);
  const [confidence, setConfidence] = useState(0);
  const [accumulatedSigns, setAccumulatedSigns] = useState([]);
  const [isEmergency, setIsEmergency] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isProcessingVideo, setIsProcessingVideo] = useState(false);

  const handleVideoUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setIsProcessingVideo(true);

    const formData = new FormData();
    formData.append('video', file);

    try {
      const response = await fetch('http://localhost:5000/upload_video_http', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();

      if (!response.ok) {
        setIsProcessingVideo(false);
        alert(`Upload failed: ${data.error}`);
      }
    } catch (err) {
      setIsProcessingVideo(false);
      alert('Upload failed — check console for details');
    }
  };

  const handleFinishSigning = async () => {
    if (accumulatedSigns.length < 2) {
      alert('Please sign at least 2 symptoms before analyzing.');
      return;
    }

    setIsAnalyzing(true);
    try {
      const response = await fetch('http://localhost:5000/finish_signing_http', {
        method: 'POST'
      });
      const data = await response.json();
      if (!response.ok) {
        setIsAnalyzing(false);
        alert(`Error: ${data.error}`);
      }
    } catch (err) {
      setIsAnalyzing(false);
      alert('Failed to analyze symptoms — check console');
    }
  };
  useEffect(() => {
    if (mode === 'live') {
      socket.emit('start_camera');
    }

    socket.on('camera_frame', (data) => {
      setFrame(`data:image/jpeg;base64,${data.frame}`);
      setHandDetected(data.hand_detected);
      setCurrentPrediction(data.current_prediction);
      setConfidence(data.confidence);
    });

    socket.on('sign_detected', (data) => {
      setAccumulatedSigns(data.accumulated_signs);
    });

    socket.on('emergency_alert', () => {
      setIsEmergency(true);
    });

    socket.on('pipeline_result', (data) => {
      setIsAnalyzing(false);
      navigate('/staff', { state: { result: data } });
    });

    socket.on('video_upload_received', () => {
      setIsAnalyzing(false);
      setIsProcessingVideo(true);
    });

    socket.on('video_processing_complete', () => {
      setIsProcessingVideo(false);
      setIsAnalyzing(true);
    });

    return () => {
      if (mode === 'live') {
        socket.emit('stop_camera');
      }
      socket.off('camera_frame');
      socket.off('sign_detected');
      socket.off('emergency_alert');
      socket.off('pipeline_result');
      socket.off('video_upload_received');
      socket.off('video_processing_complete');
    };
  }, [mode]);

  return (
    <div style={{
      background: colors.bgGradient,
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      fontFamily: "'Inter', -apple-system, sans-serif",
      transition: 'background 0.3s ease'
    }}>

      {isEmergency && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0,
          backgroundColor: '#dc2626', color: '#ffffff',
          textAlign: 'center', padding: '16px',
          fontSize: '1.2rem', fontWeight: 'bold',
          zIndex: 1000, animation: 'pulseBanner 1.5s infinite'
        }}>
          🚨 EMERGENCY DETECTED — Staff alerted immediately
        </div>
      )}

      <style>{`
        @keyframes pulseBanner { 0%{opacity:1} 50%{opacity:0.7} 100%{opacity:1} }
        @keyframes chipIn { from{opacity:0;transform:translateY(8px) scale(0.9)} to{opacity:1;transform:translateY(0) scale(1)} }
      `}</style>

      {/* Header — consistent across the whole app */}
      <header style={{
        width: '100%',
        maxWidth: '700px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '24px 20px 0'
      }}>
        <div
          onClick={() => navigate('/')}
          style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}
        >
          <div style={{
            width: '36px', height: '36px', borderRadius: '10px',
            background: `linear-gradient(135deg, ${colors.accent}, #8b5cf6)`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '1.1rem'
          }}>
            💬
          </div>
          <span style={{ color: colors.text, fontWeight: '700', fontSize: '1.1rem' }}>
            Sign<span style={{ color: colors.accent }}>Bridge</span>
          </span>
        </div>

        <button
          onClick={toggleTheme}
          style={{
            backgroundColor: colors.surfaceLight,
            border: `1px solid ${colors.border}`,
            borderRadius: '999px',
            padding: '8px 14px',
            cursor: 'pointer',
            color: colors.text,
            fontSize: '0.85rem'
          }}
        >
          {theme === 'dark' ? '☀️' : '🌙'}
        </button>
      </header>

      {/* Main content */}
      <div style={{
        width: '100%',
        maxWidth: '500px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: '30px 20px',
        flex: 1
      }}>

        <p style={{ color: colors.textMuted, fontSize: '1rem', marginBottom: '30px' }}>
          {mode === 'live' ? 'Show us what you need' : 'Processing your uploaded video'}
        </p>

        {mode === 'live' && (
          <div style={{
            width: '100%', aspectRatio: '4 / 3',
            backgroundColor: colors.surface,
            border: handDetected ? '2px solid #22c55e' : `2px dashed ${colors.border}`,
            borderRadius: '16px', overflow: 'hidden',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            marginBottom: '16px'
          }}>
            {frame
              ? <img src={frame} alt="camera" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
              : <span style={{ color: colors.textFaint, fontSize: '1.1rem' }}>📷 Connecting to camera...</span>
            }
          </div>
        )}

        {mode === 'live' && (
          <button
            onClick={handleFinishSigning}
            disabled={isAnalyzing}
            style={{
              width: '100%',
              backgroundColor: isAnalyzing ? colors.surfaceLight : colors.accent,
              color: isAnalyzing ? colors.textFaint : '#fff',
              border: 'none',
              borderRadius: '12px',
              padding: '14px 28px',
              fontWeight: '600',
              cursor: isAnalyzing ? 'not-allowed' : 'pointer',
              marginBottom: '20px',
              boxShadow: isAnalyzing ? 'none' : `0 4px 16px ${colors.accentGlow}`
            }}
          >
            {isAnalyzing ? '🔄 Analyzing...' : `✅ Done Signing (${accumulatedSigns.length} symptom${accumulatedSigns.length !== 1 ? 's' : ''} so far) — Analyze`}
          </button>
        )}

        {/* UPLOAD MODE — choose file */}
        {mode === 'upload' && !isProcessingVideo && (
          <div style={{
            width: '100%', aspectRatio: '4 / 3',
            backgroundColor: colors.surface,
            border: `2px dashed ${colors.border}`,
            borderRadius: '16px', overflow: 'hidden',
            display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center',
            marginBottom: '16px', gap: '16px'
          }}>
            <span style={{ fontSize: '2rem' }}>📹</span>
            <span style={{ color: colors.textMuted }}>Choose an MP4 video to upload</span>
            <input
              type="file"
              accept="video/mp4"
              onChange={handleVideoUpload}
              style={{ display: 'none' }}
              id="video-upload-input"
            />
            <button
              onClick={() => document.getElementById('video-upload-input').click()}
              style={{
                backgroundColor: colors.accent, border: 'none', borderRadius: '10px',
                padding: '12px 24px', color: '#fff', cursor: 'pointer', fontWeight: '600'
              }}
            >
              Choose File
            </button>
          </div>
        )}

        {/* UPLOAD MODE — processing preview */}
        {mode === 'upload' && isProcessingVideo && (
          <div style={{
            width: '100%', aspectRatio: '4 / 3',
            backgroundColor: colors.surface,
            border: `2px solid ${colors.accent}`,
            borderRadius: '16px', overflow: 'hidden',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            marginBottom: '16px'
          }}>
            {frame
              ? <img src={frame} alt="processing" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
              : <span style={{ color: colors.textFaint }}>🔄 Processing video...</span>
            }
          </div>
        )}

        {/* Live Prediction */}
        <div style={{ marginBottom: '16px', textAlign: 'center' }}>
          <p style={{ color: colors.textMuted, fontSize: '0.85rem', margin: '4px 0' }}>
            {handDetected ? '✋ Hand detected' : 'No hand detected'}
          </p>
          {currentPrediction && (
            <p style={{ color: colors.text, fontSize: '1rem', margin: '4px 0' }}>
              Detected: <strong>{currentPrediction}</strong> — {confidence}% confidence
            </p>
          )}
        </div>

        {accumulatedSigns.length > 0 && (
          <div style={{
            display: 'flex', flexWrap: 'wrap', gap: '8px',
            justifyContent: 'center', marginBottom: '16px', width: '100%'
          }}>
            {accumulatedSigns.map((sign, i) => (
              <span key={`${sign}-${i}`} style={{
                backgroundColor: colors.surfaceLight,
                border: `1px solid ${colors.accent}`,
                color: colors.text, borderRadius: '999px', padding: '6px 14px',
                fontSize: '0.9rem', animation: 'chipIn 0.3s ease'
              }}>
                {sign}
              </span>
            ))}
          </div>
        )}



        {isAnalyzing && (
          <div style={{
            backgroundColor: colors.surfaceLight,
            border: `1px solid ${colors.border}`,
            borderRadius: '12px',
            padding: '14px 24px', color: colors.textMuted,
            marginBottom: '24px', textAlign: 'center'
          }}>
            🔄 Analyzing symptoms...
          </div>
        )}

        {/* ASL Sign Reference */}
        <div style={{
          width: '100%',
          marginTop: '24px',
          paddingTop: '24px',
          borderTop: `1px solid ${colors.border}`
        }}>
          <p style={{ color: colors.textMuted, fontSize: '0.9rem', marginBottom: '14px', textAlign: 'center' }}>
            Not sure how to sign? Tap a card to see the ASL sign:
          </p>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))',
            gap: '10px'
          }}>
            {[
              { sign: 'Pain', emoji: '😖', link: resourceLinks['Pain'] },
              { sign: 'Headache', emoji: '🤕', link: resourceLinks['Headache'] },
              { sign: 'Dizzy', emoji: '😵', link: resourceLinks['Dizzy'] },
              { sign: 'Stomach', emoji: '🤢', link: resourceLinks['Stomach'] },
              { sign: 'Cough', emoji: '😤', link: resourceLinks['Cough'] },
              { sign: 'Fever', emoji: '🌡️', link: resourceLinks['Fever'] },
              { sign: 'Help', emoji: '🆘', link: resourceLinks['Help'] },
              { sign: 'Doctor', emoji: '👨‍⚕️', link: resourceLinks['Doctor'] },
            ].map((item) => (
              <a
                key={item.sign}
                href={item.link}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  backgroundColor: colors.surfaceLight,
                  border: `1px solid ${colors.border}`,
                  borderRadius: '12px',
                  padding: '14px 10px',
                  textAlign: 'center',
                  textDecoration: 'none',
                  cursor: 'pointer',
                  display: 'block',
                  transition: 'transform 0.15s, border-color 0.15s'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.borderColor = colors.accent;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.borderColor = colors.border;
                }}
              >
                <div style={{ fontSize: '1.5rem', marginBottom: '6px' }}>{item.emoji}</div>
                <div style={{ color: colors.text, fontWeight: '600', fontSize: '0.85rem' }}>{item.sign}</div>
                <div style={{ color: colors.textFaint, fontSize: '0.7rem', marginTop: '3px' }}>
                  ▶ Watch sign
                </div>
              </a>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default PatientScreen;