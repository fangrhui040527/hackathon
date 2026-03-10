// API configuration
// When running the backend locally, use your machine's local IP.
// The Expo app on your phone needs to reach this address.
import { Platform } from 'react-native';

// Use localhost for web, ngrok tunnel for native devices
const LOCAL_IP = '172.20.10.3'; // ← Your PC's IP (update if network changes)
const PORT = 8000; // All services on one port

// If using ngrok/localtunnel, set your tunnel URL here
const NGROK_URL = ''; // disabled — using direct LAN IP instead

export const API_URL =
  Platform.OS === 'web'
    ? `http://localhost:${PORT}`
    : `http://${LOCAL_IP}:${PORT}`;
