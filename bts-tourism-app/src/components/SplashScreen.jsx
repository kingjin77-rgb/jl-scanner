import { useEffect, useState } from 'react';
import { CONCERT_INFO } from '../data/tourismData';

export default function SplashScreen({ onDone }) {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const t1 = setTimeout(() => setPhase(1), 400);
    const t2 = setTimeout(() => setPhase(2), 1200);
    const t3 = setTimeout(() => setPhase(3), 2200);
    const t4 = setTimeout(() => onDone(), 3600);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); clearTimeout(t4); };
  }, [onDone]);

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(160deg, #1a0533 0%, #2d0a4e 30%, #4a0e7a 65%, #6b21a8 100%)',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Background decorative circles */}
      <div style={{
        position: 'absolute', top: '-80px', right: '-80px',
        width: 250, height: 250,
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(168,85,247,0.3) 0%, transparent 70%)',
      }} />
      <div style={{
        position: 'absolute', bottom: '-60px', left: '-60px',
        width: 200, height: 200,
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(124,58,237,0.4) 0%, transparent 70%)',
      }} />

      {/* Main heart emoji */}
      <div style={{
        fontSize: '72px',
        opacity: phase >= 1 ? 1 : 0,
        transform: phase >= 1 ? 'scale(1)' : 'scale(0.3)',
        transition: 'all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)',
        animation: phase >= 2 ? 'floatHeart 3s ease-in-out infinite' : 'none',
        marginBottom: '1.5rem',
        filter: 'drop-shadow(0 0 20px rgba(168,85,247,0.8))',
      }}>
        💜
      </div>

      {/* App title */}
      <div style={{
        textAlign: 'center',
        opacity: phase >= 2 ? 1 : 0,
        transform: phase >= 2 ? 'translateY(0)' : 'translateY(20px)',
        transition: 'all 0.6s ease',
        marginBottom: '2rem',
      }}>
        <h1 style={{
          fontSize: '28px',
          fontWeight: 800,
          color: '#ffffff',
          letterSpacing: '-0.5px',
          lineHeight: 1.2,
          marginBottom: '8px',
        }}>
          BTS ARMY
        </h1>
        <h2 style={{
          fontSize: '15px',
          fontWeight: 500,
          color: '#c084fc',
          letterSpacing: '3px',
          textTransform: 'uppercase',
          marginBottom: '6px',
        }}>
          Busan Tourism Guide
        </h2>
        <p style={{
          fontSize: '12px',
          color: '#a78bfa',
          fontWeight: 400,
        }}>
          부산 근처 도시 여행 가이드
        </p>
      </div>

      {/* Concert info card */}
      <div style={{
        background: 'rgba(255,255,255,0.08)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(168,85,247,0.3)',
        borderRadius: '16px',
        padding: '1.25rem 1.75rem',
        textAlign: 'center',
        opacity: phase >= 3 ? 1 : 0,
        transform: phase >= 3 ? 'translateY(0)' : 'translateY(20px)',
        transition: 'all 0.5s ease',
        maxWidth: '280px',
        width: '100%',
      }}>
        <p style={{ fontSize: '11px', color: '#c084fc', fontWeight: 600, letterSpacing: '2px', marginBottom: '6px' }}>
          🎤 CONCERT INFO
        </p>
        <p style={{ fontSize: '16px', fontWeight: 800, color: '#ffffff', marginBottom: '4px' }}>
          {CONCERT_INFO.artist} — "{CONCERT_INFO.tour.split('"')[1]}"
        </p>
        <p style={{ fontSize: '12px', color: '#e9d5ff', marginBottom: '4px' }}>
          📍 {CONCERT_INFO.venue}
        </p>
        <p style={{ fontSize: '12px', color: '#c084fc', fontWeight: 600 }}>
          📅 {CONCERT_INFO.dates[0]} & {CONCERT_INFO.dates[1]}
        </p>
      </div>

      {/* Loading dots */}
      <div style={{
        position: 'absolute',
        bottom: '2.5rem',
        display: 'flex',
        gap: '8px',
        opacity: phase >= 2 ? 1 : 0,
        transition: 'opacity 0.4s ease',
      }}>
        {[0,1,2].map(i => (
          <div key={i} style={{
            width: 8, height: 8,
            borderRadius: '50%',
            background: '#a855f7',
            animation: `pulse 1.4s ease-in-out ${i * 0.2}s infinite`,
          }} />
        ))}
      </div>
    </div>
  );
}
