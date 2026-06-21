import { useNavigate } from 'react-router-dom';
import { useTheme } from '../ThemeContext';

function LandingScreen() {
    const navigate = useNavigate();
    const { theme, toggleTheme, colors } = useTheme();

    return (
        <div style={{
            minHeight: '100vh',
            background: colors.bgGradient,
            position: 'relative',
            overflow: 'hidden',
            fontFamily: "'Inter', -apple-system, sans-serif",
            transition: 'background 0.3s ease'
        }}>

            {/* Ambient background glow shapes */}
            <div style={{
                position: 'absolute',
                top: '-10%',
                left: '-5%',
                width: '500px',
                height: '500px',
                borderRadius: '50%',
                background: `radial-gradient(circle, ${colors.accentGlow}, transparent 70%)`,
                filter: 'blur(60px)',
                animation: 'drift 8s ease-in-out infinite'
            }} />
            <div style={{
                position: 'absolute',
                bottom: '-10%',
                right: '-5%',
                width: '450px',
                height: '450px',
                borderRadius: '50%',
                background: `radial-gradient(circle, ${colors.accentGlow}, transparent 70%)`,
                filter: 'blur(60px)',
                animation: 'drift 10s ease-in-out infinite reverse'
            }} />

            <style>{`
        @keyframes drift {
          0%, 100% { transform: translate(0, 0); }
          50% { transform: translate(30px, -20px); }
        }
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulseGlow {
          0%, 100% { box-shadow: 0 0 30px ${colors.accentGlow}; }
          50% { box-shadow: 0 0 50px ${colors.accentGlow}; }
        }
      `}</style>

            {/* Theme Toggle */}
            <button
                onClick={toggleTheme}
                style={{
                    position: 'absolute',
                    top: '24px',
                    right: '24px',
                    backgroundColor: colors.surfaceLight,
                    border: `1px solid ${colors.border}`,
                    borderRadius: '999px',
                    padding: '10px 16px',
                    cursor: 'pointer',
                    color: colors.text,
                    fontSize: '0.9rem',
                    zIndex: 10
                }}
            >
                {theme === 'dark' ? '☀️ Light' : '🌙 Dark'}
            </button>

            <div style={{
                position: 'relative',
                zIndex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                padding: '60px 20px 40px',
                textAlign: 'center'
            }}>

                {/* Logo */}
                <div style={{
                    width: '72px',
                    height: '72px',
                    borderRadius: '18px',
                    background: `linear-gradient(135deg, ${colors.accent}, #8b5cf6)`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginBottom: '24px',
                    animation: 'pulseGlow 3s ease-in-out infinite',
                    fontSize: '2rem'
                }}>
                    💬
                </div>

                <h1 key={theme} style={{
                    fontSize: '3.2rem',
                    fontWeight: '800',
                    marginBottom: '12px',
                    letterSpacing: '-0.02em',
                    animation: 'fadeUp 0.6s ease',
                    color: colors.text
                }}>
                    Sign<span style={{ color: colors.accent }}>Bridge</span>
                </h1>

                <p style={{
                    color: colors.textMuted,
                    fontSize: '1.2rem',
                    maxWidth: '580px',
                    marginBottom: '40px',
                    animation: 'fadeUp 0.6s ease 0.1s both'
                }}>
                    AI-powered sign language interpretation for medical communication
                </p>

                {/* Problem → Solution narrative */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '20px',
                    flexWrap: 'wrap',
                    justifyContent: 'center',
                    marginBottom: '40px',
                    animation: 'fadeUp 0.6s ease 0.2s both'
                }}>
                    <div style={{
                        backgroundColor: colors.surfaceLight,
                        border: `1px solid ${colors.border}`,
                        borderRadius: '14px',
                        padding: '18px 22px',
                        maxWidth: '220px'
                    }}>
                        <div style={{ fontSize: '1.6rem', marginBottom: '6px' }}>🌍</div>
                        <div style={{ color: colors.text, fontWeight: '700', fontSize: '0.95rem' }}>
                            430M+ people
                        </div>
                        <div style={{ color: colors.textFaint, fontSize: '0.8rem' }}>
                            live with hearing loss worldwide
                        </div>
                    </div>

                    <div style={{ color: colors.textFaint, fontSize: '1.5rem' }}>→</div>

                    <div style={{
                        backgroundColor: colors.surfaceLight,
                        border: `1px solid ${colors.border}`,
                        borderRadius: '14px',
                        padding: '18px 22px',
                        maxWidth: '220px'
                    }}>
                        <div style={{ fontSize: '1.6rem', marginBottom: '6px' }}>🏥</div>
                        <div style={{ color: colors.text, fontWeight: '700', fontSize: '0.95rem' }}>
                            No interpreter
                        </div>
                        <div style={{ color: colors.textFaint, fontSize: '0.8rem' }}>
                            often available at point of care
                        </div>
                    </div>

                    <div style={{ color: colors.textFaint, fontSize: '1.5rem' }}>→</div>

                    <div style={{
                        backgroundColor: colors.surfaceLight,
                        border: `1px solid ${colors.accent}`,
                        borderRadius: '14px',
                        padding: '18px 22px',
                        maxWidth: '220px'
                    }}>
                        <div style={{ fontSize: '1.6rem', marginBottom: '6px' }}>✅</div>
                        <div style={{ color: colors.accent, fontWeight: '700', fontSize: '0.95rem' }}>
                            SignBridge
                        </div>
                        <div style={{ color: colors.textFaint, fontSize: '0.8rem' }}>
                            bridges the gap in real time
                        </div>
                    </div>
                </div>

                {/* Pipeline visual */}
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    flexWrap: 'wrap',
                    justifyContent: 'center',
                    marginBottom: '36px',
                    padding: '16px 24px',
                    backgroundColor: colors.surfaceLight,
                    border: `1px solid ${colors.border}`,
                    borderRadius: '16px',
                    animation: 'fadeUp 0.6s ease 0.3s both'
                }}>
                    {['👋 Sign', '👁️ Vision AI', '🧠 Clinical AI', '💬 Summary'].map((step, i) => (
                        <div key={step} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <span style={{ color: colors.text, fontSize: '0.9rem', fontWeight: '600' }}>{step}</span>
                            {i < 3 && <span style={{ color: colors.textFaint }}>→</span>}
                        </div>
                    ))}
                </div>

                {/* How It Works - Detailed Cards */}
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                    gap: '16px',
                    marginBottom: '44px',
                    maxWidth: '780px',
                    width: '100%',
                    animation: 'fadeUp 0.6s ease 0.32s both'
                }}>
                    {[
                        {
                            icon: '👁️',
                            title: 'Computer Vision',
                            desc: 'MediaPipe extracts hand landmarks; a custom LSTM model recognizes ASL medical signs from real motion sequences.'
                        },
                        {
                            icon: '🧠',
                            title: 'Clinical AI',
                            desc: 'Recognized signs are sent to Infermedica — a real diagnosis & triage engine used by healthcare companies.'
                        },
                        {
                            icon: '💬',
                            title: 'Plain-Language Summary',
                            desc: 'Groq (Llama 3.3) turns clinical output into a clear, doctor-ready summary in seconds.'
                        }
                    ].map((card) => (
                        <div key={card.title} style={{
                            backgroundColor: colors.surfaceLight,
                            border: `1px solid ${colors.border}`,
                            borderRadius: '16px',
                            padding: '24px',
                            textAlign: 'left'
                        }}>
                            <div style={{ fontSize: '1.8rem', marginBottom: '10px' }}>{card.icon}</div>
                            <div style={{ color: colors.text, fontWeight: '700', fontSize: '1rem', marginBottom: '6px' }}>
                                {card.title}
                            </div>
                            <div style={{ color: colors.textMuted, fontSize: '0.85rem', lineHeight: '1.5' }}>
                                {card.desc}
                            </div>
                        </div>
                    ))}
                </div>

                <p style={{
                    color: colors.textMuted,
                    fontSize: '0.95rem',
                    maxWidth: '600px',
                    marginBottom: '20px',
                    fontStyle: 'italic',
                    animation: 'fadeUp 0.6s ease 0.33s both'
                }}>
                    "Every claim below is validated against real, unseen ASL signers — not just our own testing."
                </p>

                {/* Stats row */}
                <div style={{
                    display: 'flex',
                    gap: '32px',
                    marginBottom: '44px',
                    flexWrap: 'wrap',
                    justifyContent: 'center',
                    animation: 'fadeUp 0.6s ease 0.35s both'
                }}>
                    {[
                        { value: '12', label: 'Medical signs' },
                        { value: '70.9%', label: 'Validated accuracy' },
                        { value: '3', label: 'AI systems combined' }
                    ].map((stat) => (
                        <div key={stat.label} style={{ textAlign: 'center' }}>
                            <div style={{ color: colors.accent, fontSize: '2rem', fontWeight: '800' }}>{stat.value}</div>
                            <div style={{ color: colors.textFaint, fontSize: '0.8rem' }}>{stat.label}</div>
                        </div>
                    ))}
                </div>

                {/* CTA Buttons */}
                <div style={{
                    display: 'flex',
                    gap: '16px',
                    flexWrap: 'wrap',
                    justifyContent: 'center',
                    animation: 'fadeUp 0.6s ease 0.4s both'
                }}>
                    <button
                        onClick={() => navigate('/patient')}
                        style={{
                            backgroundColor: colors.accent,
                            color: '#ffffff',
                            border: 'none',
                            borderRadius: '12px',
                            padding: '16px 32px',
                            fontSize: '1rem',
                            fontWeight: '600',
                            cursor: 'pointer',
                            boxShadow: `0 4px 20px ${colors.accentGlow}`,
                            transition: 'transform 0.2s'
                        }}
                        onMouseEnter={(e) => { e.target.style.transform = 'translateY(-2px)'; }}
                        onMouseLeave={(e) => { e.target.style.transform = 'translateY(0)'; }}
                    >
                        🎥 I'm a Patient — Start Signing
                    </button>

                    <button
                        onClick={() => navigate('/staff')}
                        style={{
                            backgroundColor: 'transparent',
                            color: colors.textMuted,
                            border: `1px solid ${colors.border}`,
                            borderRadius: '12px',
                            padding: '16px 32px',
                            fontSize: '1rem',
                            fontWeight: '600',
                            cursor: 'pointer',
                            transition: 'background-color 0.2s'
                        }}
                        onMouseEnter={(e) => e.target.style.backgroundColor = colors.surfaceLight}
                        onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
                    >
                        👨‍⚕️ I'm Medical Staff
                    </button>
                </div>
                {/* About / Team Section */}
                <div style={{
                    marginTop: '60px',
                    paddingTop: '40px',
                    borderTop: `1px solid ${colors.border}`,
                    width: '100%',
                    maxWidth: '600px',
                    animation: 'fadeUp 0.6s ease 0.5s both'
                }}>
                    <h2 style={{ color: colors.text, fontSize: '1.3rem', fontWeight: '700', marginBottom: '8px' }}>
                        It was Built by 2 Undergraduate Students
                    </h2>
                    <p style={{ color: colors.textMuted, fontSize: '0.95rem', maxWidth: '480px', margin: '0 auto 24px' }}>
                        We combined computer vision, a real clinical diagnosis engine, and
                        language AI — and validated every claim against real, unseen test data
                        rather than just trusting our first results.
                    </p>

                    <div style={{ display: 'flex', gap: '16px', justifyContent: 'center', flexWrap: 'wrap' }}>
                        {['Ahmed Reda SAHABI', 'Youssef Figuigui'].map((name) => (
                            <div key={name} style={{
                                backgroundColor: colors.surfaceLight,
                                border: `1px solid ${colors.border}`,
                                borderRadius: '12px',
                                padding: '14px 24px',
                                color: colors.text,
                                fontSize: '0.9rem',
                                fontWeight: '600'
                            }}>
                                {name}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Footer */}
                <footer style={{
                    marginTop: '40px',
                    display: 'flex',
                    gap: '20px',
                    flexWrap: 'wrap',
                    justifyContent: 'center',
                    animation: 'fadeUp 0.6s ease 0.6s both'
                }}>
                    <a href="https://github.com/YOUR_USERNAME/signbridge" target="_blank" rel="noopener noreferrer"
                        style={{ color: colors.textFaint, fontSize: '0.85rem', textDecoration: 'none' }}>
                        GitHub
                    </a>
                    <span style={{ color: colors.border }}>•</span>
                    <a href="#" target="_blank" rel="noopener noreferrer"
                        style={{ color: colors.textFaint, fontSize: '0.85rem', textDecoration: 'none' }}>
                        Devpost
                    </a>
                    <span style={{ color: colors.border }}>•</span>
                    <span style={{ color: colors.textFaint, fontSize: '0.85rem' }}>
                        USAII Global AI Hackathon 2026
                    </span>
                </footer>
            </div>
        </div>
    );
}

export default LandingScreen;