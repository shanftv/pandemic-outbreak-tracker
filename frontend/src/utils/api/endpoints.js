// Use environment variable for API URL, fallback to localhost for development
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
export const ENDPOINTS = {
  PREDICTIONS_SUMMARY: `${API_BASE_URL}/predictions/summary`,
  DANGER_ZONES_GEOJSON: `${API_BASE_URL}/danger-zones/geojson`,
  SIMULATIONS: `${API_BASE_URL}/simulations`,
};