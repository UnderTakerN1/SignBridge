import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import socket from '../socket';
import { useTheme } from '../ThemeContext';

function parseSummary(text) {
  if (!text) return [];
  // Split by sentences/newlines into digestible chunks
  return text
    .split(/\n+/)
    .map(line => line.trim())
    .filter(line => line.length > 0);
}

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

function StaffScreen() {
  const location = useLocation();
  const navigate = useNavigate();
  const { colors } = useTheme();
  const result = location.state?.result;
  const [confirmStatus, setConfirmStatus] = useState('idle');

  useEffect(() => {
    setConfirmStatus('idle');
  }, [result]);

  const handleConfirm = () => {
    if (!result || confirmStatus !== 'idle') {
      return;
    }

    setConfirmStatus('confirming');
    socket.emit('confirm_interpretation', { signs: result.signs_detected });
    window.requestAnimationFrame(() => {
      setConfirmStatus('confirmed');
    });
  };

  if (!result) {
    return (
      <div style={{
        background: colors.bgGradient,
        minHeight: '100vh',
        padding: '40px 20px',
        fontFamily: "'Inter', -apple-system, sans-serif"
      }}>
        <div style={{ maxWidth: '700px', margin: '0 auto' }}>

          <div
            onClick={() => navigate('/')}
            style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', marginBottom: '32px' }}
          >
            <div style={{
              width: '36px', height: '36px', borderRadius: '10px',
              background: `linear-gradient(135deg, ${colors.accent}, #8b5cf6)`,
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.1rem'
            }}>💬</div>
            <span style={{ color: colors.text, fontWeight: '700', fontSize: '1.1rem' }}>
              Sign<span style={{ color: colors.accent }}>Bridge</span>
            </span>
          </div>

          <h1 style={{ color: colors.text, fontSize: '1.8rem', marginBottom: '8px' }}>
            No active patient session yet
          </h1>
          <p style={{ color: colors.textMuted, marginBottom: '36px' }}>
            While you wait, here are some quick ASL medical sign references your team may find useful.
          </p>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
            gap: '14px'
          }}>
            {[
              { sign: 'Pain', emoji: '😖', link: 'https://www.signingsavvy.com/sign/PAIN' },
              { sign: 'Headache', emoji: '🤕', link: 'https://www.signingsavvy.com/sign/HEADACHE' },
              { sign: 'Dizzy', emoji: '😵', link: 'https://www.signingsavvy.com/sign/DIZZY' },
              { sign: 'Stomach', emoji: '🤢', link: 'https://www.signingsavvy.com/sign/STOMACH' },
              { sign: 'Cough', emoji: '😤', link: 'https://www.signingsavvy.com/sign/COUGH' },
              { sign: 'Fever', emoji: '🌡️', link: 'https://www.signingsavvy.com/sign/FEVER' },
              { sign: 'Help', emoji: '🆘', link: 'https://www.signingsavvy.com/sign/HELP' },
              { sign: 'Doctor', emoji: '👨‍⚕️', link: 'https://www.signingsavvy.com/sign/DOCTOR' },
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
                  padding: '18px',
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
                <div style={{ fontSize: '1.8rem', marginBottom: '8px' }}>{item.emoji}</div>
                <div style={{ color: colors.text, fontWeight: '600' }}>{item.sign}</div>
                <div style={{ color: colors.textFaint, fontSize: '0.75rem', marginTop: '4px' }}>
                  ▶ Watch sign
                </div>
              </a>
            ))}
          </div>

          <p style={{ color: colors.textFaint, fontSize: '0.85rem', marginTop: '24px' }}>
            For full ASL medical sign references, see{' '}
            <a href="https://www.signingsavvy.com" target="_blank" rel="noopener noreferrer" style={{ color: colors.accent }}>
              SigningSavvy
            </a>{' '}
            or{' '}
            <a href="https://www.handspeak.com" target="_blank" rel="noopener noreferrer" style={{ color: colors.accent }}>
              HandSpeak
            </a>.
          </p>

          <button
            onClick={() => navigate('/patient')}
            style={{
              marginTop: '32px',
              backgroundColor: colors.accent,
              color: '#fff',
              border: 'none',
              borderRadius: '12px',
              padding: '14px 28px',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            Start a patient session
          </button>
        </div>
      </div>
    );
  }

  const confidenceColor = result.urgency_score >= 75
    ? '#22c55e'
    : result.urgency_score >= 50
      ? '#f59e0b'
      : '#ef4444';

  const possibleConditionsDetailed = Array.isArray(result.possible_conditions_detailed)
    ? [...result.possible_conditions_detailed].sort(
      (left, right) => (right.probability ?? 0) - (left.probability ?? 0),
    )
    : null;

  const confirmButtonLabel =
    confirmStatus === 'confirmed'
      ? 'Confirmed ✅'
      : confirmStatus === 'confirming'
        ? 'Confirming...'
        : '✅ Confirm Interpretation';

  return (
    <div className="app-shell">
      <div style={{
        maxWidth: '900px',
        margin: '0 auto',
        padding: '20px 20px 0',
        display: 'flex',
        justifyContent: 'flex-start'
      }}>
        <button
          onClick={() => navigate('/')}
          style={{
            backgroundColor: 'transparent',
            border: 'none',
            color: colors.textMuted,
            cursor: 'pointer',
            fontSize: '0.9rem'
          }}
        >
          ← Home
        </button>
      </div>
      {result.is_emergency && (
        <div className="alert-banner alert-banner--fixed">
          🚨 EMERGENCY — Immediate action required
        </div>
      )}

      <div className="page" style={{ paddingTop: result.is_emergency ? '72px' : undefined }}>
        <header className="hero">
          <div className="eyebrow">Staff mode</div>
          <h1 className="headline">SignBridge — Staff Panel</h1>
          <div className="subhead">Review the interpreted result and confirm the response</div>
        </header>

        <div className="dashboard">
          <div className="stack">
            <section className="surface card">
              <div className="card__heading">Interpreted summary</div>
              <h2 className="card__title">Pipeline output</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {parseSummary(result.ai_summary).map((line, i) => (
                  <div key={i} style={{
                    padding: '10px 14px',
                    backgroundColor: 'rgba(255,255,255,0.05)',
                    borderRadius: '10px',
                    borderLeft: '3px solid #3b82f6',
                    fontSize: '0.95rem',
                    lineHeight: '1.5'
                  }}>
                    {line}
                  </div>
                ))}
              </div>
            </section>

            <section className="surface card">
              <div className="card__heading">Need category</div>
              <h2 className="card__title">{result.urgency_label}</h2>
            </section>

            <section className="surface card">
              <div className="card__heading">Confidence score</div>
              <div className="confidence" style={{ color: confidenceColor }}>
                <div
                  className="confidence__bar"
                  style={{ '--confidence-width': `${result.urgency_score}%` }}
                >
                  <div
                    className="confidence__fill"
                    style={{ '--confidence-start': confidenceColor, '--confidence-end': confidenceColor }}
                  />
                </div>
                <div className="confidence__meta">
                  <span>{result.urgency_score}% confidence</span>
                  {result.urgency_score < 60 && (
                    <span>⚠️ Low confidence — verify manually before proceeding</span>
                  )}
                </div>
              </div>
            </section>

            <section className="surface card">
              <div className="card__heading">Possible eligibility</div>
              {possibleConditionsDetailed?.length > 0 ? (
                <>
                  <div className="section__meta">Patient may qualify for:</div>
                  <div className="condition-list">
                    {possibleConditionsDetailed.map((item) => {
                      const probability = Number.isFinite(item.probability) ? item.probability : 0;
                      const percentage = Math.max(0, Math.min(probability, 100));

                      return (
                        <div className="condition-item" key={item.disease}>
                          <div className="condition-item__header">
                            <span className="condition-item__name">{item.disease}</span>
                            <span className="condition-item__probability">{Math.round(percentage)}%</span>
                          </div>
                          <div className="condition-item__bar">
                            <div
                              className="condition-item__fill"
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </>
              ) : result.possible_conditions?.length > 0 ? (
                <>
                  <div className="section__meta">Patient may qualify for:</div>
                  <ul className="condition-list condition-list--flat">
                    {result.possible_conditions.map((condition, index) => (
                      <li key={`${condition}-${index}`}>{condition}</li>
                    ))}
                  </ul>
                </>
              ) : (
                <div>No eligibility matches found.</div>
              )}
              <div className="section__meta">⚠️ Suggestion only. Final determination must be made by staff.</div>
            </section>
          </div>

          <aside className="stack">
            <section className="surface card">
              <div className="card__heading">Send response to patient</div>
              <h2 className="card__title">Confirm interpretation</h2>
              <button
                type="button"
                className={`action-button action-button--confirm action-button--${confirmStatus}`}
                onClick={handleConfirm}
                disabled={confirmStatus !== 'idle'}
              >
                {confirmStatus === 'confirming' ? 'Confirming...' : confirmButtonLabel}
              </button>
              <button type="button" className="action-button action-button--secondary">
                Send to Patient Screen
              </button>
              <button
                type="button"
                onClick={() => navigate('/')}
                className="action-button action-button--secondary"
                style={{ marginTop: '10px' }}
              >
                🏠 Back to Home
              </button>
            </section>
          </aside>
        </div>
      </div>
    </div>
  );
}

export default StaffScreen;
