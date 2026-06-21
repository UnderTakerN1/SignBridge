import { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

export function ThemeProvider({ children }) {
    const [theme, setTheme] = useState(() => {
        return localStorage.getItem('signbridge-theme') || 'dark';
    });

    useEffect(() => {
        localStorage.setItem('signbridge-theme', theme);
        document.documentElement.setAttribute('data-theme', theme);
    }, [theme]);

    const toggleTheme = () => {
        setTheme(prev => prev === 'dark' ? 'light' : 'dark');
    };

    const colors = theme === 'dark' ? {
        bg: '#0a0a0a',
        bgGradient: 'linear-gradient(135deg, #0a0a0a 0%, #111827 50%, #0a0a0a 100%)',
        surface: '#1a1a1a',
        surfaceLight: 'rgba(255,255,255,0.05)',
        border: 'rgba(255,255,255,0.1)',
        text: '#ffffff',
        textMuted: '#9ca3af',
        textFaint: '#6b7280',
        accent: '#3b82f6',
        accentGlow: 'rgba(59, 130, 246, 0.4)'
    } : {
        bg: '#f8fafc',
        bgGradient: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #f8fafc 100%)',
        surface: '#ffffff',
        surfaceLight: 'rgba(0,0,0,0.03)',
        border: 'rgba(0,0,0,0.1)',
        text: '#0f172a',
        textMuted: '#475569',
        textFaint: '#94a3b8',
        accent: '#2563eb',
        accentGlow: 'rgba(37, 99, 235, 0.3)'
    };

    return (
        <ThemeContext.Provider value={{ theme, toggleTheme, colors }}>
            {children}
        </ThemeContext.Provider>
    );
}

export function useTheme() {
    return useContext(ThemeContext);
}