import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';

import ChatScreen    from '../screens/ChatScreen';
import ScanScreen    from '../screens/ScanScreen';
import PreviewScreen from '../screens/PreviewScreen';
import ResultScreen  from '../screens/ResultScreen';

const Stack = createStackNavigator();

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator
        initialRouteName="Chat"
        screenOptions={{ headerShown: false }}
      >
        <Stack.Screen name="Chat"    component={ChatScreen} />
        <Stack.Screen name="Scan"    component={ScanScreen} />
        <Stack.Screen name="Preview" component={PreviewScreen} />
        <Stack.Screen name="Result"  component={ResultScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
