const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

/**
 * Analyze market trend for a given symbol
 * @param {string} symbol - Stock symbol (e.g., 'NSE:RELIANCE-EQ')
 * @param {string} [interval='5'] - Candle interval in minutes
 * @param {number} [duration=5] - Number of days of historical data
 * @returns {Promise<Object>} Analysis results
 */
export async function analyzeTrend(symbol, interval = '5', duration = 5) {
  try {
    const response = await fetch(
      `${BASE_URL}/api/trend/analyze?symbol=${symbol}&interval=${interval}&duration=${duration}`
    );
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to analyze trend');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error in analyzeTrend:', error);
    throw error;
  }
}

/**
 * Get Stochastic Oscillator values for a symbol
 * @param {string} symbol - Stock symbol
 * @param {string} [interval='5'] - Candle interval in minutes
 * @param {number} [duration=5] - Number of days of historical data
 * @param {number} [kPeriod=14] - Lookback period for %K
 * @param {number} [dPeriod=3] - Smoothing period for %D
 * @returns {Promise<Object>} Stochastic values
 */
export async function getStochasticOscillator(
  symbol, 
  interval = '5', 
  duration = 5, 
  kPeriod = 14, 
  dPeriod = 3
) {
  try {
    const params = new URLSearchParams({
      symbol,
      interval,
      duration,
      k_period: kPeriod,
      d_period: dPeriod
    });
    
    const response = await fetch(
      `${BASE_URL}/api/trend/stochastic?${params}`
    );
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to get Stochastic values');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error in getStochasticOscillator:', error);
    throw error;
  }
}

/**
 * Get historical trend data for a symbol
 * @param {string} symbol - Stock symbol
 * @param {string} [interval='5'] - Candle interval in minutes
 * @param {number} [duration=5] - Number of days of historical data
 * @returns {Promise<Object>} Historical trend data
 */
export async function getTrendHistory(symbol, interval = '5', duration = 5) {
  try {
    const response = await fetch(
      `${BASE_URL}/api/trend/history?symbol=${symbol}&interval=${interval}&duration=${duration}`
    );
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to get trend history');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error in getTrendHistory:', error);
    throw error;
  }
}
