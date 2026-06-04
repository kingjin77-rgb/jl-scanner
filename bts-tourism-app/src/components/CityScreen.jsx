import { useState } from 'react';
import { RESTAURANTS, ATTRACTIONS, TRANSPORT } from '../data/tourismData';
import PlaceCard from './PlaceCard';

const TAB_LABELS = {
  restaurants: { en: '🍽️ Restaurants', ja: '🍽️ レストラン', zh: '🍽️ 餐厅', fr: '🍽️ Restaurants', th: '🍽️ ร้านอาหาร' },
  attractions: { en: '🗺️ Must-See', ja: '🗺️ 観光地', zh: '🗺️ 景点', fr: '🗺️ À Voir', th: '🗺️ สถานที่ท่องเที่ยว' },
  transport: { en: '🚄 Getting There', ja: '🚄 アクセス', zh: '🚄 交通', fr: '🚄 Transports', th: '🚄 การเดินทาง' },
};

export default function CityScreen({ city, language, onBack, onItemSelect }) {
  const [activeTab, setActiveTab] = useState('restaurants');
  const [filter, setFilter] = useState('all');

  const restaurants = RESTAURANTS.filter(r => r.cityId === city.id);
  const attractions = ATTRACTIONS.filter(a => a.cityId === city.id);
  const transport = TRANSPORT[city.id];

  const filterOptions = [
    { key: 'all', label: 'All' },
    { key: 'vegan', label: '🌱 Vegan' },
    { key: 'halal', label: '🌙 Halal' },
    { key: 'rm-connection', label: '💜 RM Spot' },
    { key: 'english', label: '🗣️ English' },
  ];

  const filteredRestaurants = filter === 'all'
    ? restaurants
    : restaurants.filter(r => r.tags.includes(filter));

  const filteredAttractions = filter === 'all'
    ? attractions
    : attractions.filter(a => a.tags.includes(filter));

  const colorMap = {
    gyeongju: '#b45309',
    yangsan: '#15803d',
    ulsan: '#2563eb',
    gimhae: '#7c3aed',
    changwon: '#dc2626',
  };
  const accentColor = colorMap[city.id] || '#7c3aed';

  return (
    <div style={{ minHeight: '100vh', background: '#f5f0ff' }}>
      {/* Header */}
      <div style={{
        background: `linear-gradient(160deg, #1a0533, ${accentColor})`,
        padding: '1.5rem 1.25rem 3.5rem',
        position: 'relative',
      }}>
        {/* Back button */}
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
          ‹ All Cities
        </button>

        {/* City info */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '64px', height: '64px',
            borderRadius: '18px',
            background: 'rgba(255,255,255,0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
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
              display: 'inline-block',
              marginTop: '6px',
              fontSize: '11px',
              background: 'rgba(255,255,255,0.2)',
              color: '#ffffff',
              padding: '2px 10px',
              borderRadius: '10px',
              fontWeight: 600,
            }}>
              🚄 {city.distance}
            </span>
          </div>
        </div>
      </div>

      {/* Tab bar — floats over header */}
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
        {['restaurants', 'attractions', 'transport'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              flex: 1,
              padding: '12px 4px',
              background: activeTab === tab ? `linear-gradient(135deg, #6b21a8, #7c3aed)` : 'transparent',
              border: 'none',
              cursor: 'pointer',
              fontSize: '10px',
              fontWeight: 700,
              color: activeTab === tab ? '#ffffff' : '#6b7280',
              transition: 'all 0.2s ease',
              letterSpacing: '0.3px',
            }}
          >
            {TAB_LABELS[tab][language] || TAB_LABELS[tab].en}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ padding: '1.25rem' }}>
        {/* Filter pills */}
        {activeTab !== 'transport' && (
          <div style={{
            display: 'flex',
            gap: '6px',
            overflowX: 'auto',
            paddingBottom: '4px',
            marginBottom: '1rem',
            scrollbarWidth: 'none',
          }}>
            {filterOptions.map(opt => (
              <button
                key={opt.key}
                onClick={() => setFilter(opt.key)}
                style={{
                  flexShrink: 0,
                  padding: '6px 14px',
                  borderRadius: '20px',
                  border: filter === opt.key ? 'none' : '1px solid #e9d5ff',
                  background: filter === opt.key ? '#7c3aed' : '#ffffff',
                  color: filter === opt.key ? '#ffffff' : '#7c3aed',
                  fontSize: '11px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  whiteSpace: 'nowrap',
                }}
              >
                {opt.label}
              </button>
            ))}
          </div>
        )}

        {/* Restaurants tab */}
        {activeTab === 'restaurants' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {filteredRestaurants.length === 0 && (
              <EmptyState filter={filter} />
            )}
            {filteredRestaurants.map((r, i) => (
              <PlaceCard key={r.id} item={r} type="restaurant" index={i} onSelect={onItemSelect} accentColor={accentColor} />
            ))}
          </div>
        )}

        {/* Attractions tab */}
        {activeTab === 'attractions' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {filteredAttractions.length === 0 && (
              <EmptyState filter={filter} />
            )}
            {filteredAttractions.map((a, i) => (
              <PlaceCard key={a.id} item={a} type="attraction" index={i} onSelect={onItemSelect} accentColor={accentColor} />
            ))}
          </div>
        )}

        {/* Transport tab */}
        {activeTab === 'transport' && transport && (
          <TransportInfo transport={transport} city={city} accentColor={accentColor} />
        )}
      </div>
    </div>
  );
}

function EmptyState({ filter }) {
  return (
    <div style={{
      textAlign: 'center',
      padding: '3rem 1rem',
      color: '#9ca3af',
    }}>
      <div style={{ fontSize: '40px', marginBottom: '12px' }}>🔍</div>
      <p style={{ fontSize: '14px', fontWeight: 500 }}>No results for "{filter}" filter</p>
      <p style={{ fontSize: '12px', marginTop: '6px' }}>Try "All" to see everything</p>
    </div>
  );
}

function TransportInfo({ transport, city, accentColor }) {
  const options = Object.entries(transport).filter(([k]) => k !== 'tip');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {options.map(([key, value]) => {
        const icons = { byTrain: '🚄', bySubway: '🚇', byBus: '🚌' };
        const labels = { byTrain: 'By Train (KTX)', bySubway: 'By Subway', byBus: 'By Bus' };
        return (
          <div key={key} style={{
            background: '#ffffff',
            borderRadius: '14px',
            padding: '1rem',
            boxShadow: '0 2px 10px rgba(107,33,168,0.08)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
              <span style={{ fontSize: '24px' }}>{icons[key]}</span>
              <span style={{ fontSize: '13px', fontWeight: 700, color: '#374151' }}>{labels[key]}</span>
            </div>
            <p style={{ fontSize: '13px', color: '#6b7280', lineHeight: 1.5 }}>{value}</p>
          </div>
        );
      })}

      {transport.tip && (
        <div style={{
          background: `linear-gradient(135deg, #faf5ff, #f0fdf4)`,
          border: `1px solid #e9d5ff`,
          borderRadius: '14px',
          padding: '1rem',
        }}>
          <p style={{ fontSize: '13px', fontWeight: 700, color: accentColor, marginBottom: '4px' }}>💡 Pro Tip</p>
          <p style={{ fontSize: '13px', color: '#374151', lineHeight: 1.5 }}>{transport.tip}</p>
        </div>
      )}

      <div style={{
        background: '#ffffff',
        borderRadius: '14px',
        padding: '1rem',
        boxShadow: '0 2px 10px rgba(107,33,168,0.08)',
      }}>
        <p style={{ fontSize: '13px', fontWeight: 700, color: '#374151', marginBottom: '8px' }}>
          🎟️ Useful Transport Apps
        </p>
        {[
          ['Korail App', 'KTX tickets — accepts international cards'],
          ['Naver Maps', 'Navigation in English, Japanese, Chinese'],
          ['T-Money', 'Transit card — works on all buses & subways'],
          ['Kakao Taxi', 'Ride-hailing — English destination input available'],
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
