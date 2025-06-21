// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Debug logging
console.log('=== API CONFIGURATION DEBUG ===');
console.log('Environment variables:', {
  REACT_APP_API_URL: process.env.REACT_APP_API_URL,
  NODE_ENV: process.env.NODE_ENV
});
console.log('Using API_BASE_URL:', API_BASE_URL);
console.log('=== END DEBUG ===');

// Force local API if no environment variable is set
const FINAL_API_URL = API_BASE_URL.includes('vercel') ? 'http://localhost:8000' : API_BASE_URL;

console.log('FINAL API URL:', FINAL_API_URL);

export { FINAL_API_URL as API_BASE_URL }; 