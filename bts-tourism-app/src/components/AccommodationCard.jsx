import { useState } from 'react';
import StarRating from './StarRating';

export default function AccommodationCard({ item, index, onSelect, accentColor, t }) {
  const [pressed, setPressed] = useState(false);

  return (
    <div
      onClick={() => onSelect({ ...item, isAccommodation: true })}
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
      {/* Savings banner */}
      <div style={{
        background: 'linear-gradient(90deg, #d1fae5, #a7f3d0)',
        padding: '6px 14px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <span style={{ fontSize: '11px', color: '#065f46', fontWeight: 700 }}>
          💰 {item.savings}
        </span>
        <span style={{
          fontSize: '10px',
          background: '#059669',
          color: '#ffffff',
          padding: '2px 8px',
          borderRadius: '8px',
          fontWeight: 700,
        }}>
          {item.type}
        </span>
      </div>

      <div style={{ padding: '1rem' }}>
        {/* Top row */}
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', marginBottom: '10px' }}>
          <div style={{
            width: '48px', height: '48px',
            borderRadius: '14px',
            background: '#f0fdf4',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '24px', flexShrink: 0,
          }}>
            {item.emoji}
          </div>
          <div style={{ flex: 1 }}>
            <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#111827', lineHeight: 1.2, marginBottom: '2px' }}>
              {item.nameEn}
            </h3>
            <p style={{ fontSize: '11px', color: '#9ca3af' }}>{item.nameKo}</p>
          </div>
        </div>

        {/* Price comparison */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '8px',
          marginBottom: '10px',
        }}>
          <div style={{
            background: '#f0fdf4', borderRadius: '10px', padding: '8px',
            border: '1px solid #bbf7d0',
          }}>
            <p style={{ fontSize: '10px', color: '#065f46', fontWeight: 600, marginBottom: '2px' }}>
              {t.normalPrice}
            </p>
            <p style={{ fontSize: '13px', fontWeight: 800, color: '#111827' }}>
              {item.priceRange.split(' / ')[0]}
            </p>
          </div>
          <div style={{
            background: '#fff7ed', borderRadius: '10px', padding: '8px',
            border: '1px solid #fed7aa',
          }}>
            <p style={{ fontSize: '10px', color: '#9a3412', fontWeight: 600, marginBottom: '2px' }}>
              {t.concertWeekPrice}
            </p>
            <p style={{ fontSize: '13px', fontWeight: 800, color: '#ea580c' }}>
              {item.concertWeekPrice}
            </p>
          </div>
        </div>

        {/* Ratings */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <StarRating rating={item.googleRating} size={12} />
            <span style={{ fontSize: '12px', fontWeight: 700, color: '#374151' }}>{item.googleRating}</span>
            <span style={{ fontSize: '11px', color: '#9ca3af' }}>Google</span>
          </div>
          <div style={{
            display: 'flex', alignItems: 'center', gap: '4px',
            background: '#f0fdf4', padding: '3px 8px', borderRadius: '8px',
          }}>
            <span style={{ fontSize: '11px', color: '#16a34a', fontWeight: 600 }}>
              📝 {item.naverBlogCount.toLocaleString()} Naver
            </span>
          </div>
        </div>

        {/* Highlight */}
        <p style={{
          fontSize: '12px', color: '#374151', lineHeight: 1.5,
          background: '#f0fdf4', padding: '8px 10px', borderRadius: '10px',
          borderLeft: `3px solid #059669`, marginBottom: '10px',
        }}>
          {item.highlight}
        </p>

        {/* Address & CTA */}
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
