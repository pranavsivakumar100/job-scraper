// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Force local API if no environment variable is set or if it contains vercel
const FINAL_API_URL = API_BASE_URL.includes('vercel') ? 'http://localhost:8000' : API_BASE_URL;

// Only log in development mode
if (process.env.NODE_ENV === 'development') {
  console.log('API URL:', FINAL_API_URL);
}

export { FINAL_API_URL as API_BASE_URL }; 