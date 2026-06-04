import { useEffect, useState } from 'react';
import StarRating from './StarRating';
import { I18N } from '../data/tourismData';

const TAG_LABELS = {
  vegan: '🌱 Vegan-Friendly', halal: '🌙 Halal Certified',
  'rm-connection': '💜 RM-Visited Spot', english: '🗣️ English Staff',
  japanese: '🗣️ Japanese Menu', chinese: '🗣️ Chinese Menu',
  french: '🗣️ French Info', thai: '🗣️ Thai Info',
  temple: '⛩️ Temple Cuisine', experience: '✨ Interactive Experience',
  free: '🎁 Free Admission', budget: '💚 Budget-Friendly',
  unesco: '🏛️ UNESCO Heritage', card: '💳 Card Payment OK',
  nature: '🌲 Nature Trail', adventure: '🎡 Adventure Activity',
  performance: '🎭 Live Performance', history: '🏛️ Historical Site',
  art: '🎨 Art & Culture', family: '👨‍👩‍👦 Family-Friendly',
};

export default function DetailModal({ item, language, onClose }) {
  const [visible, setVisible] = useState(false);
  const t = I18N[language] || I18N.en;

  useEffect(() => {
    setTimeout(() => setVisible(true), 10);
    const handleEsc = (e) => { if (e.key === 'Escape') handleClose(); };
    window.addEventListener('keydown', handleEsc);
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', handleEsc);
      document.body.style.overflow = '';
    };
  }, []);

  const handleClose = () => {
    setVisible(false);
    setTimeout(onClose, 300);
  };

  const isRestaurant = !!item.mainMenus;
  const isAttraction = !!item.btsConnection;
  const isAccommodation = !!item.isAccommodation;

  return (
    <div
      onClick={handleClose}
      style={{
        position: 'fixed',
        inset: 0,
        background: `rgba(26,5,51,${visible ? 0.75 : 0})`,
        display: 'flex',
        alignItems: 'flex-end',
        justifyContent: 'center',
        zIndex: 1000,
        transition: 'background 0.3s ease',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: '#ffffff',
          borderRadius: '24px 24px 0 0',
          width: '100%',
          maxWidth: 480,
          maxHeight: '90vh',
          overflowY: 'auto',
          transform: visible ? 'translateY(0)' : 'translateY(100%)',
          transition: 'transform 0.35s cubic-bezier(0.34, 1.1, 0.64, 1)',
        }}
      >
        {/* Drag handle */}
        <div style={{ padding: '12px', display: 'flex', justifyContent: 'center' }}>
          <div style={{ width: 40, height: 4, borderRadius: 2, background: '#e5e7eb' }} />
        </div>

        {/* BTS connection banner */}
        {item.btsConnection && (
          <div style={{
            margin: '0 1.25rem 1rem',
            background: 'linear-gradient(135deg, #fef3c7, #fde68a)',
            borderRadius: '14px',
            padding: '12px 16px',
          }}>
            <p style={{ fontSize: '11px', color: '#92400e', fontWeight: 700, marginBottom: '4px' }}>
              💜 BTS CONNECTION — {item.btsMember}
            </p>
            <p style={{ fontSize: '13px', color: '#78350f', lineHeight: 1.5 }}>
              {item.btsConnection}
            </p>
            {item.btsConnectionKo && (
              <p style={{ fontSize: '12px', color: '#92400e', marginTop: '4px', opacity: 0.8 }}>
                {item.btsConnectionKo}
              </p>
            )}
          </div>
        )}

        {/* Header */}
        <div style={{ padding: '0 1.25rem 1rem' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px', marginBottom: '1rem' }}>
            <div style={{
              width: '60px', height: '60px',
              borderRadius: '16px',
              background: '#f5f0ff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '30px',
              flexShrink: 0,
            }}>
              {item.emoji}
            </div>
            <div style={{ flex: 1 }}>
              <h2 style={{ fontSize: '20px', fontWeight: 800, color: '#111827', marginBottom: '2px' }}>
                {item.nameEn}
              </h2>
              <p style={{ fontSize: '13px', color: '#6b7280' }}>{item.nameKo}</p>
              <p style={{ fontSize: '12px', color: '#9ca3af', marginTop: '2px' }}>{item.category}</p>
            </div>
          </div>

          {/* Ratings */}
          <div style={{
            display: 'flex',
            gap: '10px',
            marginBottom: '1rem',
            flexWrap: 'wrap',
          }}>
            <div style={{
              flex: 1,
              background: '#fffbeb',
              borderRadius: '12px',
              padding: '10px 14px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              minWidth: '140px',
            }}>
              <span style={{ fontSize: '20px' }}>⭐</span>
              <div>
                <p style={{ fontSize: '11px', color: '#92400e', fontWeight: 600 }}>{t.googleRating}</p>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <StarRating rating={item.googleRating} size={13} />
                  <span style={{ fontSize: '15px', fontWeight: 800, color: '#111827' }}>{item.googleRating}</span>
                </div>
              </div>
            </div>
            <div style={{
              flex: 1,
              background: '#f0fdf4',
              borderRadius: '12px',
              padding: '10px 14px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              minWidth: '140px',
            }}>
              <span style={{ fontSize: '20px' }}>📝</span>
              <div>
                <p style={{ fontSize: '11px', color: '#166534', fontWeight: 600 }}>{t.naverBlogs}</p>
                <p style={{ fontSize: '15px', fontWeight: 800, color: '#111827' }}>
                  {item.naverBlogCount.toLocaleString()}+
                </p>
              </div>
            </div>
          </div>

          {/* Highlight */}
          <div style={{
            background: '#faf5ff',
            borderRadius: '12px',
            padding: '12px 14px',
            borderLeft: '4px solid #7c3aed',
            marginBottom: '1rem',
          }}>
            <p style={{ fontSize: '13px', color: '#374151', lineHeight: 1.6 }}>
              {item.highlight}
            </p>
          </div>
        </div>

        <div style={{ height: '1px', background: '#f3f4f6', margin: '0 1.25rem' }} />

        {/* Details sections */}
        <div style={{ padding: '1rem 1.25rem' }}>

          {/* Accommodation price comparison */}
          {isAccommodation && (
            <Section title={t.savingsLabel}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '8px' }}>
                <div style={{ background: '#f0fdf4', borderRadius: '10px', padding: '10px', border: '1px solid #bbf7d0' }}>
                  <p style={{ fontSize: '10px', color: '#065f46', fontWeight: 600, marginBottom: '2px' }}>{t.normalPrice}</p>
                  <p style={{ fontSize: '14px', fontWeight: 800, color: '#111827' }}>{item.priceRange}</p>
                </div>
                <div style={{ background: '#fff7ed', borderRadius: '10px', padding: '10px', border: '1px solid #fed7aa' }}>
                  <p style={{ fontSize: '10px', color: '#9a3412', fontWeight: 600, marginBottom: '2px' }}>{t.concertWeekPrice}</p>
                  <p style={{ fontSize: '14px', fontWeight: 800, color: '#ea580c' }}>{item.concertWeekPrice}</p>
                </div>
              </div>
              <div style={{ background: '#d1fae5', borderRadius: '10px', padding: '10px' }}>
                <p style={{ fontSize: '13px', color: '#065f46', fontWeight: 700 }}>✅ {item.savings}</p>
              </div>
            </Section>
          )}

          {/* Menus (restaurants) */}
          {isRestaurant && item.mainMenus && (
            <Section title={t.signatureMenus}>
              {item.mainMenus.map((menu, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <span style={{ color: '#a855f7', fontWeight: 700, fontSize: '14px' }}>•</span>
                  <div>
                    <span style={{ fontSize: '13px', color: '#111827', fontWeight: 500 }}>{menu}</span>
                    {item.mainMenusKo && item.mainMenusKo[i] && (
                      <span style={{ fontSize: '12px', color: '#9ca3af', marginLeft: '6px' }}>
                        ({item.mainMenusKo[i]})
                      </span>
                    )}
                  </div>
                </div>
              ))}
              {item.priceRange && (
                <div style={{
                  marginTop: '8px', display: 'inline-flex',
                  alignItems: 'center', gap: '4px',
                  background: '#f3f4f6', padding: '4px 12px', borderRadius: '10px',
                }}>
                  <span style={{ fontSize: '12px', color: '#374151', fontWeight: 600 }}>
                    {t.priceRange}: {item.priceRange}
                  </span>
                </div>
              )}
            </Section>
          )}

          {/* Hours & Admission (attractions) */}
          {isAttraction && (
            <Section title={t.visitInfo}>
              <InfoRow icon="💰" label={t.admission} value={item.admissionFee} />
              <InfoRow icon="🕐" label={t.hours} value={item.openHours} />
            </Section>
          )}

          {/* Features */}
          {item.features && item.features.length > 0 && (
            <Section title={isAccommodation ? t.accommodationFeatures : t.features}>
              {item.features.map((f, i) => (
                <div key={i} style={{ display: 'flex', gap: '8px', marginBottom: '5px' }}>
                  <span style={{ color: '#7c3aed', flexShrink: 0 }}>✓</span>
                  <span style={{ fontSize: '13px', color: '#374151' }}>{f}</span>
                </div>
              ))}
            </Section>
          )}

          {/* Language support */}
          {item.languages && item.languages.length > 0 && (
            <Section title={t.languages}>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {item.languages.map(lang => (
                  <span key={lang} style={{
                    background: '#eff6ff', color: '#1d4ed8',
                    fontSize: '12px', padding: '4px 12px',
                    borderRadius: '20px', fontWeight: 600,
                  }}>
                    🗣️ {lang}
                  </span>
                ))}
              </div>
            </Section>
          )}

          {/* Tags */}
          <Section title={t.categories}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {item.tags.map(tag => {
                const label = TAG_LABELS[tag];
                if (!label) return null;
                return (
                  <span key={tag} style={{
                    background: '#f5f0ff',
                    color: '#6b21a8',
                    fontSize: '12px',
                    padding: '4px 12px',
                    borderRadius: '20px',
                    fontWeight: 600,
                  }}>
                    {label}
                  </span>
                );
              })}
            </div>
          </Section>

          {/* Address */}
          <Section title={t.address}>
            <p style={{ fontSize: '13px', color: '#374151', marginBottom: '4px' }}>
              {item.addressEn || item.address}
            </p>
            {item.address && item.addressEn && (
              <p style={{ fontSize: '12px', color: '#9ca3af' }}>{item.address}</p>
            )}
          </Section>

          {/* Action buttons */}
          <div style={{ display: 'flex', gap: '8px', marginTop: '1rem', marginBottom: '0.5rem' }}>
            <a
              href={item.mapUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                flex: 1,
                background: 'linear-gradient(135deg, #4285f4, #2563eb)',
                color: '#ffffff',
                padding: '12px',
                borderRadius: '12px',
                textAlign: 'center',
                textDecoration: 'none',
                fontSize: '13px',
                fontWeight: 700,
                display: 'block',
              }}
            >
              {t.googleMaps}
            </a>
            <a
              href={item.naverUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                flex: 1,
                background: 'linear-gradient(135deg, #03c75a, #02b350)',
                color: '#ffffff',
                padding: '12px',
                borderRadius: '12px',
                textAlign: 'center',
                textDecoration: 'none',
                fontSize: '13px',
                fontWeight: 700,
                display: 'block',
              }}
            >
              {t.naverReviews}
            </a>
          </div>

          <button
            onClick={handleClose}
            style={{
              width: '100%',
              padding: '14px',
              background: '#f3f4f6',
              border: 'none',
              borderRadius: '12px',
              fontSize: '14px',
              color: '#374151',
              fontWeight: 600,
              cursor: 'pointer',
              marginBottom: '1rem',
            }}
          >
            {t.close}
          </button>
        </div>
      </div>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: '1.25rem' }}>
      <h3 style={{ fontSize: '13px', fontWeight: 700, color: '#6b7280', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        {title}
      </h3>
      {children}
    </div>
  );
}

function InfoRow({ icon, label, value }) {
  return (
    <div style={{ display: 'flex', gap: '10px', marginBottom: '8px', alignItems: 'flex-start' }}>
      <span style={{ fontSize: '14px', flexShrink: 0, marginTop: '1px' }}>{icon}</span>
      <div>
        <span style={{ fontSize: '11px', color: '#9ca3af', fontWeight: 600, display: 'block' }}>{label}</span>
        <span style={{ fontSize: '13px', color: '#374151', fontWeight: 500 }}>{value}</span>
      </div>
    </div>
  );
}
