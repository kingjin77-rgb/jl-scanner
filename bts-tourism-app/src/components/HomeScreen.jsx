import { useState, useMemo } from 'react';
import { CITIES, LANGUAGES, I18N } from '../data/tourismData';

function useConcertCountdown() {
  return useMemo(() => {
    const now = new Date();
    const concert = new Date('2026-06-12T18:00:00+09:00');
    const diff = concert - now;
    if (diff <= 0) return { days: 0, hours: 0, minutes: 0, past: true };
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    return { days, hours, minutes, past: false };
  }, []);
}

export default function HomeScreen({ onCitySelect, language, onLanguageChange }) {
  const [showLangMenu, setShowLangMenu] = useState(false);
  const currentLang = LANGUAGES.find(l => l.code === language) || LANGUAGES[0];
  const t = I18N[language] || I18N.en;
  const countdown = useConcertCountdown();

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(180deg, #1a0533 0%, #2d0a4e 40%, #f5f0ff 40%)',
    }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(160deg, #1a0533 0%, #4a0e7a 100%)',
        padding: '1.5rem 1.25rem 2.5rem',
        position: 'relative',
      }}>
        {/* Language selector */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem', position: 'relative' }}>
          <button
            onClick={() => setShowLangMenu(!showLangMenu)}
            style={{
              background: 'rgba(255,255,255,0.1)',
              border: '1px solid rgba(168,85,247,0.4)',
              borderRadius: '20px',
              padding: '6px 14px',
              color: '#e9d5ff',
              fontSize: '13px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontWeight: 500,
            }}
          >
            {currentLang.flag} {currentLang.name} ▾
          </button>
          {showLangMenu && (
            <div style={{
              position: 'absolute',
              top: '100%',
              right: 0,
              marginTop: '6px',
              background: '#ffffff',
              borderRadius: '12px',
              boxShadow: '0 8px 24px rgba(0,0,0,0.2)',
              overflow: 'hidden',
              zIndex: 100,
              minWidth: '140px',
            }}>
              {LANGUAGES.map(lang => (
                <button
                  key={lang.code}
                  onClick={() => { onLanguageChange(lang.code); setShowLangMenu(false); }}
                  style={{
                    width: '100%',
                    padding: '10px 16px',
                    background: lang.code === language ? '#faf5ff' : 'transparent',
                    border: 'none',
                    textAlign: 'left',
                    cursor: 'pointer',
                    fontSize: '13px',
                    color: lang.code === language ? '#7c3aed' : '#374151',
                    fontWeight: lang.code === language ? 600 : 400,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    borderBottom: '1px solid #f3f4f6',
                  }}
                >
                  {lang.flag} {lang.name}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* App branding */}
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '36px', marginBottom: '8px', filter: 'drop-shadow(0 0 12px rgba(168,85,247,0.7))' }}>💜</div>
          <h1 style={{ fontSize: '22px', fontWeight: 800, color: '#ffffff', marginBottom: '4px' }}>
            {t.appTitle}
          </h1>
          <p style={{ fontSize: '12px', color: '#c084fc', letterSpacing: '1px' }}>
            {t.appSubtitle}
          </p>
        </div>

        {/* Concert D-Day Countdown */}
        <div style={{
          marginTop: '1.25rem',
          background: 'rgba(255,255,255,0.07)',
          border: '1px solid rgba(168,85,247,0.35)',
          borderRadius: '16px',
          padding: '1rem',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
            <span style={{ fontSize: '18px' }}>🎤</span>
            <div>
              <p style={{ fontSize: '12px', color: '#c084fc', fontWeight: 700 }}>{t.concertLabel}</p>
              <p style={{ fontSize: '10px', color: '#a78bfa' }}>{t.concertVenue}</p>
            </div>
          </div>

          {/* Countdown blocks */}
          {!countdown.past ? (
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
              {[
                { val: countdown.days, label: language === 'ko' ? '일' : language === 'ja' ? '日' : language === 'zh' ? '天' : 'Days' },
                { val: countdown.hours, label: language === 'ko' ? '시간' : language === 'ja' ? '時間' : language === 'zh' ? '小时' : 'Hrs' },
                { val: countdown.minutes, label: language === 'ko' ? '분' : language === 'ja' ? '分' : language === 'zh' ? '分' : 'Min' },
              ].map(({ val, label }) => (
                <div key={label} style={{
                  flex: 1, background: 'rgba(168,85,247,0.25)',
                  borderRadius: '12px', padding: '8px 4px',
                  textAlign: 'center', border: '1px solid rgba(168,85,247,0.3)',
                }}>
                  <p style={{ fontSize: '22px', fontWeight: 900, color: '#ffffff', lineHeight: 1, marginBottom: '2px' }}>
                    {String(val).padStart(2, '0')}
                  </p>
                  <p style={{ fontSize: '9px', color: '#c084fc', fontWeight: 600, letterSpacing: '0.5px' }}>
                    {label}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ textAlign: 'center', color: '#c084fc', fontSize: '14px', fontWeight: 700 }}>
              🎉 Concert Day!
            </p>
          )}

          <p style={{ fontSize: '10px', color: '#a78bfa', textAlign: 'center', marginTop: '8px' }}>
            {t.concertTip}
          </p>
        </div>
      </div>

      {/* City cards */}
      <div style={{ padding: '1.25rem', marginTop: '-0.5rem' }}>
        <h2 style={{
          fontSize: '16px',
          fontWeight: 700,
          color: '#374151',
          marginBottom: '1rem',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
        }}>
          {t.chooseCityTitle}
          <span style={{
            fontSize: '10px',
            background: '#7c3aed',
            color: '#ffffff',
            padding: '2px 8px',
            borderRadius: '10px',
            fontWeight: 600,
          }}>
            {CITIES.length}
          </span>
        </h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {CITIES.map((city, i) => (
            <CityCard key={city.id} city={city} index={i} onSelect={onCitySelect} />
          ))}
        </div>

        {/* Bottom tips */}
        <div style={{
          marginTop: '1.5rem',
          background: 'linear-gradient(135deg, #faf5ff, #f0fdf4)',
          border: '1px solid #e9d5ff',
          borderRadius: '16px',
          padding: '1.25rem',
        }}>
          <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#6b21a8', marginBottom: '0.75rem' }}>
            {t.tipsTitle}
          </h3>
          {t.tips.map((tip, i) => (
            <p key={i} style={{ fontSize: '12px', color: '#374151', marginBottom: '6px', lineHeight: 1.5 }}>{tip}</p>
          ))}
        </div>
      </div>
    </div>
  );
}

function CityCard({ city, index, onSelect }) {
  const [pressed, setPressed] = useState(false);

  const colorMap = {
    gyeongju: { bg: 'linear-gradient(135deg, #92400e, #b45309)', light: '#fef3c7' },
    yangsan: { bg: 'linear-gradient(135deg, #14532d, #15803d)', light: '#dcfce7' },
    ulsan: { bg: 'linear-gradient(135deg, #1e3a8a, #2563eb)', light: '#dbeafe' },
    gimhae: { bg: 'linear-gradient(135deg, #4c1d95, #7c3aed)', light: '#ede9fe' },
    changwon: { bg: 'linear-gradient(135deg, #991b1b, #dc2626)', light: '#fee2e2' },
  };
  const colors = colorMap[city.id] || { bg: 'linear-gradient(135deg, #4a0e7a, #7c3aed)', light: '#f5f0ff' };

  return (
    <div
      onClick={() => onSelect(city)}
      onMouseDown={() => setPressed(true)}
      onMouseUp={() => setPressed(false)}
      onTouchStart={() => setPressed(true)}
      onTouchEnd={() => setPressed(false)}
      style={{
        background: '#ffffff',
        borderRadius: '16px',
        overflow: 'hidden',
        boxShadow: pressed ? '0 2px 8px rgba(107,33,168,0.15)' : '0 4px 16px rgba(107,33,168,0.12)',
        cursor: 'pointer',
        transform: pressed ? 'scale(0.98)' : 'scale(1)',
        transition: 'all 0.15s ease',
        animation: `fadeInUp 0.4s ease ${index * 0.08}s both`,
        display: 'flex',
        alignItems: 'stretch',
      }}
    >
      {/* Color strip */}
      <div style={{
        width: '6px',
        background: colors.bg,
        flexShrink: 0,
      }} />

      {/* Content */}
      <div style={{ padding: '1rem', flex: 1, display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* Emoji badge */}
        <div style={{
          width: '52px',
          height: '52px',
          borderRadius: '14px',
          background: colors.light,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '26px',
          flexShrink: 0,
        }}>
          {city.emoji}
        </div>

        {/* Text */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#111827' }}>
              {city.nameEn}
            </h3>
            <span style={{ fontSize: '13px', color: '#6b7280' }}>{city.nameKo}</span>
          </div>
          <p style={{ fontSize: '12px', color: '#6b7280', marginBottom: '6px' }}>
            {city.tagline}
          </p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{
              fontSize: '10px',
              background: '#f5f0ff',
              color: '#7c3aed',
              padding: '2px 8px',
              borderRadius: '10px',
              fontWeight: 600,
            }}>
              🚄 {city.distance}
            </span>
          </div>
        </div>

        {/* Arrow */}
        <div style={{ fontSize: '18px', color: '#d1d5db', flexShrink: 0 }}>›</div>
      </div>
    </div>
  );
}
