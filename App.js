import React from 'react';  
import { useFonts, SpaceGrotesk_700Bold } from '@expo-google-fonts/space-grotesk';
import { Nunito_400Regular, Nunito_700Bold } from '@expo-google-fonts/nunito';
import { ScanProvider } from './frontend/context/ScanContext';
import AppNavigator from './frontend/navigation/AppNavigator';
import './global.css';

export default function App() {
  const [fontsLoaded] = useFonts({
    SpaceGrotesk_700Bold,
    Nunito_400Regular,
    Nunito_700Bold,
  });

  if (!fontsLoaded) return null;

  return (
    <ScanProvider>
      <AppNavigator />
    </ScanProvider>
  );
}
