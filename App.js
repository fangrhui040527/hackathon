import React from 'react';
import { useFonts, SpaceGrotesk_700Bold } from '@expo-google-fonts/space-grotesk';
import { Nunito_400Regular, Nunito_700Bold } from '@expo-google-fonts/nunito';
import { ScanProvider } from './src/context/ScanContext';
import AppNavigator from './src/navigation/AppNavigator';

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
