import { useState } from 'react';
import { RESTAURANTS, ATTRACTIONS, TRANSPORT, ACCOMMODATIONS, I18N } from '../data/tourismData';
import PlaceCard from './PlaceCard';
import AccommodationCard from './AccommodationCard';

export default function CityScreen({ city, language, onBack, onItemSelect }) {
  const [activeTab, setActiveTab] = useState('restaurants');
  const [filter, setFilter] = useState('all');
  const t = I18N[language] || I18N.en;

  const restaurants = RESTAURANTS.filter(r => r.cityId === city.id);
  const attractions = ATTRACTIONS.filter(a => a.cityId === city.id);
  const accommodations = ACCOMMODATIONS.filter(h => h.cityId === city.id);
  const transport = TRANSPORT[city.id];

  const filterOptions = [
    { key: 'all', label: t.filterAll },
    { key: 'vegan', label: t.filterVegan },
    { key: 'halal', label: t.filterHalal },
    { key: 'rm-connection', label: t.filterRM },
    { key: 'english', label: t.filterEnglish },
  ];

  const filteredRestaurants = filter === 'all' ? restaurants : restaurants.filter(r => r.tags.includes(filter));
  const filteredAttractions = filter === 'all' ? attractions : attractions.filter(a => a.tags.includes(filter));

  const colorMap = {
    gyeongju: '#b45309', yangsan: '#15803d',
    ulsan: '#2563eb', gimhae: '#7c3aed', changwon: '#dc2626',
  };
  const accentColor = colorMap[city.id] || '#7c3aed';

  const tabs = [
    { key: 'restaurants', label: t.tabRestaurants },
    { key: 'attractions', label: t.tabAttractions },
    { key: 'accommodation', label: t.tabAccommodation },
    { key: 'transport', label: t.tabTransport },
  ];

  return (
    <div style={{ minHeight: '100vh', background: '#f5f0ff' }}>
      {/* Header */}
      <div style={{
        background: `linear-gradient(160deg, #1a0533, ${accentColor})`,
        padding: '1.5rem 1.25rem 3.5rem',
      }}>
        <button
          onClick={onBack}
          style={{
            background: 'rgba(255,255,255,0.12)',
            border: '1px solid rgba(255,255,255,0.2)',
            borderRadius: '10px',
            padding: '8px 14px',
            color: '#ffffff',
            cursor: 'pointer',
            fontSize: '13px',
            marginBottom: '1.25rem',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontWeight: 500,
          }}
        >
          {t.backBtn}
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '64px', height: '64px',
            borderRadius: '18px',
            background: 'rgba(255,255,255,0.15)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '34px',
          }}>
            {city.emoji}
          </div>
          <div>
            <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#ffffff', lineHeight: 1.1 }}>
              {city.nameEn}
            </h1>
            <p style={{ fontSize: '15px', color: 'rgba(255,255,255,0.7)', marginTop: '2px' }}>
              {city.nameKo} • {city.tagline}
            </p>
            <span style={{
              display: 'inline-block', marginTop: '6px',
              fontSize: '11px', background: 'rgba(255,255,255,0.2)',
              color: '#ffffff', padding: '2px 10px',
              borderRadius: '10px', fontWeight: 600,
            }}>
              🚄 {city.distance}
            </span>
          </div>
        </div>
      </div>

      {/* Tab bar */}
      <div style={{
        margin: '0 1.25rem',
        marginTop: '-1.75rem',
        background: '#ffffff',
        borderRadius: '16px',
        boxShadow: '0 4px 20px rgba(107,33,168,0.15)',
        display: 'flex',
        overflow: 'hidden',
        position: 'relative',
        zIndex: 10,
      }}>
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              flex: 1,
              padding: '10px 2px',
              background: activeTab === tab.key ? `linear-gradient(135deg, #6b21a8, #7c3aed)` : 'transparent',
              border: 'none',
              cursor: 'pointer',
              fontSize: '9px',
              fontWeight: 700,
              color: activeTab === tab.key ? '#ffffff' : '#6b7280',
              transition: 'all 0.2s ease',
              letterSpacing: '0.2px',
              lineHeight: 1.3,
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ padding: '1.25rem' }}>
        {/* Filter pills */}
        {(activeTab === 'restaurants' || activeTab === 'attractions') && (
          <div style={{
            display: 'flex', gap: '6px', overflowX: 'auto',
            paddingBottom: '4px', marginBottom: '1rem', scrollbarWidth: 'none',
          }}>
            {filterOptions.map(opt => (
              <button
                key={opt.key}
                onClick={() => setFilter(opt.key)}
                style={{
                  flexShrink: 0, padding: '6px 14px', borderRadius: '20px',
                  border: filter === opt.key ? 'none' : '1px solid #e9d5ff',
                  background: filter === opt.key ? '#7c3aed' : '#ffffff',
                  color: filter === opt.key ? '#ffffff' : '#7c3aed',
                  fontSize: '11px', fontWeight: 600, cursor: 'pointer',
                  transition: 'all 0.15s ease', whiteSpace: 'nowrap',
                }}
              >
                {opt.label}
              </button>
            ))}
          </div>
        )}

        {activeTab === 'restaurants' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {filteredRestaurants.length === 0
              ? <EmptyState />
              : filteredRestaurants.map((r, i) => (
                  <PlaceCard key={r.id} item={r} type="restaurant" index={i} onSelect={onItemSelect} accentColor={accentColor} t={t} />
                ))}
          </div>
        )}

        {activeTab === 'attractions' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {filteredAttractions.length === 0
              ? <EmptyState />
              : filteredAttractions.map((a, i) => (
                  <PlaceCard key={a.id} item={a} type="attraction" index={i} onSelect={onItemSelect} accentColor={accentColor} t={t} />
                ))}
          </div>
        )}

        {activeTab === 'accommodation' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <AccommodationBanner t={t} accentColor={accentColor} />
            {accommodations.length === 0
              ? <EmptyState />
              : accommodations.map((h, i) => (
                  <AccommodationCard key={h.id} item={h} index={i} onSelect={onItemSelect} accentColor={accentColor} t={t} />
                ))}
          </div>
        )}

        {activeTab === 'transport' && transport && (
          <TransportInfo transport={transport} accentColor={accentColor} t={t} />
        )}
      </div>
    </div>
  );
}

function AccommodationBanner({ t, accentColor }) {
  return (
    <div style={{
      background: `linear-gradient(135deg, #fef3c7, #fde68a)`,
      borderRadius: '14px',
      padding: '12px 16px',
      marginBottom: '4px',
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
    }}>
      <span style={{ fontSize: '28px' }}>🏷️</span>
      <div>
        <p style={{ fontSize: '12px', fontWeight: 700, color: '#92400e', marginBottom: '2px' }}>
          Concert Week Price Surge Alert
        </p>
        <p style={{ fontSize: '11px', color: '#78350f', lineHeight: 1.4 }}>
          Busan hotels: up to 7.5× normal price. Stay here and commute!
        </p>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div style={{ textAlign: 'center', padding: '3rem 1rem', color: '#9ca3af' }}>
      <div style={{ fontSize: '40px', marginBottom: '12px' }}>🔍</div>
      <p style={{ fontSize: '14px', fontWeight: 500 }}>No results for this filter</p>
      <p style={{ fontSize: '12px', marginTop: '6px' }}>Try "All" to see everything</p>
    </div>
  );
}

function TransportInfo({ transport, accentColor, t }) {
  const options = Object.entries(transport).filter(([k]) => k !== 'tip');
  const icons = { byTrain: '🚄', bySubway: '🚇', byBus: '🚌' };
  const labels = { byTrain: 'By Train (KTX)', bySubway: 'By Subway', byBus: 'By Bus' };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {options.map(([key, value]) => (
        <div key={key} style={{
          background: '#ffffff', borderRadius: '14px', padding: '1rem',
          boxShadow: '0 2px 10px rgba(107,33,168,0.08)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <span style={{ fontSize: '24px' }}>{icons[key]}</span>
            <span style={{ fontSize: '13px', fontWeight: 700, color: '#374151' }}>{labels[key]}</span>
          </div>
          <p style={{ fontSize: '13px', color: '#6b7280', lineHeight: 1.5 }}>{value}</p>
        </div>
      ))}

      {transport.tip && (
        <div style={{
          background: '#faf5ff', border: '1px solid #e9d5ff',
          borderRadius: '14px', padding: '1rem',
        }}>
          <p style={{ fontSize: '13px', fontWeight: 700, color: accentColor, marginBottom: '4px' }}>
            {t.proTip}
          </p>
          <p style={{ fontSize: '13px', color: '#374151', lineHeight: 1.5 }}>{transport.tip}</p>
        </div>
      )}

      <div style={{
        background: '#ffffff', borderRadius: '14px', padding: '1rem',
        boxShadow: '0 2px 10px rgba(107,33,168,0.08)',
      }}>
        <p style={{ fontSize: '13px', fontWeight: 700, color: '#374151', marginBottom: '8px' }}>
          {t.transportApps}
        </p>
        {[
          ['Korail App', 'KTX tickets — accepts international cards'],
          ['Naver Maps', 'Navigation in English, Japanese, Chinese'],
          ['T-Money', 'Transit card — works on all buses & subways'],
          ['Kakao Taxi', 'Ride-hailing — English destination input'],
        ].map(([app, desc]) => (
          <div key={app} style={{ display: 'flex', gap: '8px', marginBottom: '6px', alignItems: 'flex-start' }}>
            <span style={{ fontSize: '11px', background: '#f5f0ff', color: '#7c3aed', padding: '2px 8px', borderRadius: '8px', fontWeight: 600, flexShrink: 0, marginTop: '1px' }}>{app}</span>
            <span style={{ fontSize: '12px', color: '#6b7280' }}>{desc}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
