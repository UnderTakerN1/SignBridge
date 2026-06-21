import { useNavigate } from 'react-router-dom';
import { useTheme } from '../ThemeContext';

function PatientModeSelect() {
    const navigate = useNavigate();
    const { colors } = useTheme();

    return (
        <div style={{
            minHeight: '100vh',
            background: colors.bgGradient,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '40px 20px',
            fontFamily: "'Inter', -apple-system, sans-serif",
            textAlign: 'center'
        }}>
            <h1 style={{ color: colors.text, fontSize: '2rem', marginBottom: '12px' }}>
                How would you like to sign?
            </h1>
            <p style={{ color: colors.textMuted, fontSize: '1rem', marginBottom: '40px', maxWidth: '480px' }}>
                Choose live camera to sign in real time, or upload a recorded video.
            </p>

            <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap', justifyContent: 'center' }}>
                <button
                    onClick={() => navigate('/patient/live')}
                    style={{
                        backgroundColor: colors.accent,
                        color: '#ffffff',
                        border: 'none',
                        borderRadius: '14px',
                        padding: '28px 36px',
                        fontSize: '1rem',
                        fontWeight: '600',
                        cursor: 'pointer',
                        boxShadow: `0 4px 20px ${colors.accentGlow}`,
                        minWidth: '220px'
                    }}
                >
                    🎥<br />Use Live Camera
                </button>

                <button
                    onClick={() => navigate('/patient/upload')}
                    style={{
                        backgroundColor: 'transparent',
                        color: colors.text,
                        border: `1px solid ${colors.border}`,
                        borderRadius: '14px',
                        padding: '28px 36px',
                        fontSize: '1rem',
                        fontWeight: '600',
                        cursor: 'pointer',
                        minWidth: '220px'
                    }}
                >
                    📹<br />Upload a Video
                </button>
            </div>

            <button
                onClick={() => navigate('/')}
                style={{
                    marginTop: '40px',
                    backgroundColor: 'transparent',
                    border: 'none',
                    color: colors.textFaint,
                    cursor: 'pointer',
                    fontSize: '0.9rem'
                }}
            >
                ← Back to Home
            </button>
        </div>
    );
}

export default PatientModeSelect;