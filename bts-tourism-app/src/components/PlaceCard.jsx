import { useState } from 'react';
import StarRating from './StarRating';

const TAG_CONFIG = {
  vegan:      { label: '🌱 Vegan', bg: '#d1fae5', color: '#065f46' },
  halal:      { label: '🌙 Halal', bg: '#dbeafe', color: '#1e40af' },
  'rm-connection': { label: '💜 RM Spot', bg: '#fef3c7', color: '#92400e' },
  english:    { label: '🗣️ ENG', bg: '#f0fdf4', color: '#166534' },
  japanese:   { label: '🗣️ JPN', bg: '#fff7ed', color: '#9a3412' },
  chinese:    { label: '🗣️ CHN', bg: '#fef2f2', color: '#991b1b' },
  french:     { label: '🗣️ FRA', bg: '#eff6ff', color: '#1e40af' },
  thai:       { label: '🗣️ THA', bg: '#f0fdf4', color: '#166534' },
  temple:     { label: '⛩️ Temple', bg: '#fdf4ff', color: '#7e22ce' },
  experience: { label: '✨ Experience', bg: '#fff7ed', color: '#c2410c' },
  free:       { label: '🎁 Free Entry', bg: '#ecfdf5', color: '#064e3b' },
  budget:     { label: '💚 Budget', bg: '#f0fdf4', color: '#15803d' },
  unesco:     { label: '🏛️ UNESCO', bg: '#fefce8', color: '#713f12' },
  card:       { label: '💳 Card OK', bg: '#f8fafc', color: '#475569' },
};

export default function PlaceCard({ item, type, index, onSelect, accentColor }) {
  const [pressed, setPressed] = useState(false);

  const displayTags = item.tags.slice(0, 4);

  return (
    <div
      onClick={() => onSelect(item)}
      onMouseDown={() => setPressed(true)}
      onMouseUp={() => setPressed(false)}
      onTouchStart={() => setPressed(true)}
      onTouchEnd={() => setPressed(false)}
      style={{
        background: '#ffffff',
        borderRadius: '16px',
        overflow: 'hidden',
        boxShadow: pressed ? '0 2px 8px rgba(107,33,168,0.12)' : '0 4px 16px rgba(107,33,168,0.10)',
        cursor: 'pointer',
        transform: pressed ? 'scale(0.98)' : 'scale(1)',
        transition: 'all 0.15s ease',
        animation: `fadeInUp 0.4s ease ${index * 0.07}s both`,
      }}
    >
      {/* BTS connection banner */}
      {item.btsConnection && (
        <div style={{
          background: `linear-gradient(90deg, #fef3c7, #fde68a)`,
          padding: '6px 14px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          borderBottom: '1px solid #fde68a',
        }}>
          <span style={{ fontSize: '12px' }}>
            {item.btsMember === 'RM' ? '💜' : '🎵'}
          </span>
          <span style={{ fontSize: '11px', color: '#92400e', fontWeight: 600, lineHeight: 1.3 }}>
            {item.btsMember} — {item.btsConnection.split(' — ')[1] || item.btsConnection.substring(0, 60)}
          </span>
        </div>
      )}

      <div style={{ padding: '1rem' }}>
        {/* Top row */}
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', marginBottom: '10px' }}>
          {/* Emoji icon */}
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '14px',
            background: '#f5f0ff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '24px',
            flexShrink: 0,
          }}>
            {item.emoji}
          </div>

          {/* Title & info */}
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
              <h3 style={{
                fontSize: '15px',
                fontWeight: 700,
                color: '#111827',
                lineHeight: 1.2,
              }}>
                {item.nameEn}
              </h3>
              {type === 'attraction' && item.admissionFee && (
                <span style={{
                  fontSize: '11px',
                  color: item.admissionFee === 'Free (main halls)' || item.admissionFee.startsWith('Free') ? '#065f46' : accentColor,
                  background: item.admissionFee.startsWith('Free') ? '#d1fae5' : '#f5f0ff',
                  padding: '2px 8px',
                  borderRadius: '8px',
                  fontWeight: 600,
                  flexShrink: 0,
                }}>
                  {item.admissionFee.startsWith('Free') ? '🎁 Free' : item.admissionFee}
                </span>
              )}
              {type === 'restaurant' && item.priceRange && (
                <span style={{
                  fontSize: '11px',
                  color: '#374151',
                  background: '#f3f4f6',
                  padding: '2px 8px',
                  borderRadius: '8px',
                  fontWeight: 500,
                  flexShrink: 0,
                }}>
                  {item.priceRange}
                </span>
              )}
            </div>
            <p style={{ fontSize: '11px', color: '#9ca3af', marginTop: '2px' }}>
              {item.nameKo} • {item.category}
            </p>
          </div>
        </div>

        {/* Ratings row */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <StarRating rating={item.googleRating} size={13} />
            <span style={{ fontSize: '12px', fontWeight: 700, color: '#374151' }}>
              {item.googleRating}
            </span>
            <span style={{ fontSize: '11px', color: '#9ca3af' }}>Google</span>
          </div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            background: '#f0fdf4',
            padding: '3px 8px',
            borderRadius: '8px',
          }}>
            <span style={{ fontSize: '11px', color: '#16a34a' }}>📝</span>
            <span style={{ fontSize: '11px', color: '#16a34a', fontWeight: 600 }}>
              {item.naverBlogCount.toLocaleString()} Naver blogs
            </span>
          </div>
        </div>

        {/* Highlight text */}
        <p style={{
          fontSize: '12px',
          color: '#374151',
          lineHeight: 1.5,
          marginBottom: '10px',
          background: '#faf5ff',
          padding: '8px 10px',
          borderRadius: '10px',
          borderLeft: `3px solid ${accentColor}`,
        }}>
          {item.highlight}
        </p>

        {/* Tags */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '10px' }}>
          {displayTags.map(tag => {
            const cfg = TAG_CONFIG[tag];
            if (!cfg) return null;
            return (
              <span key={tag} style={{
                fontSize: '10px',
                padding: '3px 9px',
                borderRadius: '20px',
                background: cfg.bg,
                color: cfg.color,
                fontWeight: 600,
              }}>
                {cfg.label}
              </span>
            );
          })}
        </div>

        {/* Address & tap for more */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <p style={{ fontSize: '11px', color: '#9ca3af', flex: 1 }}>
            📍 {item.addressEn || item.address}
          </p>
          <span style={{ fontSize: '11px', color: accentColor, fontWeight: 600, flexShrink: 0 }}>
            Details ›
          </span>
        </div>
      </div>
    </div>
  );
}
