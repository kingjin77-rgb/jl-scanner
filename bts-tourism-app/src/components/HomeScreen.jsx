import { useState } from 'react';
import { CITIES, LANGUAGES, CONCERT_INFO } from '../data/tourismData';
import StarRating from './StarRating';

export default function HomeScreen({ onCitySelect, language, onLanguageChange }) {
  const [showLangMenu, setShowLangMenu] = useState(false);
  const currentLang = LANGUAGES.find(l => l.code === language) || LANGUAGES[0];

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
            BTS ARMY Travel Guide
          </h1>
          <p style={{ fontSize: '12px', color: '#c084fc', letterSpacing: '1px' }}>
            부산 인근 도시 여행 • For International ARMY
          </p>
        </div>

        {/* Concert banner */}
        <div style={{
          marginTop: '1.25rem',
          background: 'rgba(168,85,247,0.2)',
          border: '1px solid rgba(168,85,247,0.4)',
          borderRadius: '12px',
          padding: '0.875rem',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
        }}>
          <div style={{ fontSize: '28px' }}>🎤</div>
          <div>
            <p style={{ fontSize: '12px', color: '#c084fc', fontWeight: 600, marginBottom: '2px' }}>
              BTS World Tour "Arirang"
            </p>
            <p style={{ fontSize: '11px', color: '#e9d5ff' }}>
              June 12–13, 2026 • Busan Asiad Stadium
            </p>
            <p style={{ fontSize: '10px', color: '#a78bfa', marginTop: '2px' }}>
              🏨 Stay in nearby cities — save money, see more!
            </p>
          </div>
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
          🗺️ Choose Your Nearby City
          <span style={{
            fontSize: '10px',
            background: '#7c3aed',
            color: '#ffffff',
            padding: '2px 8px',
            borderRadius: '10px',
            fontWeight: 600,
          }}>
            {CITIES.length} cities
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
            💡 Smart ARMY Travel Tips
          </h3>
          {[
            '🚄 All cities under 1 hour from Busan by KTX or metro',
            '💰 Hotel prices 60–80% cheaper than central Busan during concert week',
            '🌱 Vegan & Halal options carefully curated in every city',
            '💜 RM-visited art spots included in Gyeongju & Changwon',
            '🗣️ English-speaking staff at all recommended spots',
          ].map((tip, i) => (
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
