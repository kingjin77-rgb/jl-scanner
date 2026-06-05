import { useState } from 'react';
import SplashScreen from './components/SplashScreen';
import HomeScreen from './components/HomeScreen';
import CityScreen from './components/CityScreen';
import DetailModal from './components/DetailModal';

export default function App() {
  const [screen, setScreen] = useState('splash');
  const [selectedCity, setSelectedCity] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [language, setLanguage] = useState('en');

  const handleSplashDone = () => setScreen('home');

  const handleCitySelect = (city) => {
    setSelectedCity(city);
    setScreen('city');
  };

  const handleBack = () => {
    setSelectedCity(null);
    setScreen('home');
  };

  const handleItemSelect = (item) => setSelectedItem(item);
  const handleCloseDetail = () => setSelectedItem(null);

  return (
    <div style={{ maxWidth: 480, margin: '0 auto', minHeight: '100vh', position: 'relative' }}>
      {screen === 'splash' && <SplashScreen onDone={handleSplashDone} />}
      {screen === 'home' && (
        <HomeScreen
          onCitySelect={handleCitySelect}
          language={language}
          onLanguageChange={setLanguage}
        />
      )}
      {screen === 'city' && selectedCity && (
        <CityScreen
          city={selectedCity}
          language={language}
          onBack={handleBack}
          onItemSelect={handleItemSelect}
        />
      )}
      {selectedItem && (
        <DetailModal
          item={selectedItem}
          language={language}
          onClose={handleCloseDetail}
        />
      )}
    </div>
  );
}
