import React, { useState, useEffect } from 'react';
import { MdInsights } from 'react-icons/md';
import { ALL_SYMBOLS, normalizeSymbol } from '../constants/stocks';
import './IndicatorsDashboard.css';

const IndicatorsDashboard = () => {
  const [symbol, setSymbol] = useState('NSE:SBIN-EQ');
  const [customSymbol, setCustomSymbol] = useState('');
  const [interval, setInterval] = useState('5');
  const [duration, setDuration] = useState(30);
  const [selectedIndicators, setSelectedIndicators] = useState(['rsi', 'macd', 'supertrend']);
  const [availableIndicators, setAvailableIndicators] = useState([]);
  const [indicatorData, setIndicatorData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchAvailableIndicators();
  }, []);

  const fetchAvailableIndicators = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/advanced-strategies/available-indicators');
      const data = await response.json();
      setAvailableIndicators(data.indicators);
    } catch (error) {
      console.error('Error fetching indicators:', error);
    }
  };

  const calculateIndicators = async () => {
    const activeSymbol = customSymbol ? normalizeSymbol(customSymbol) : symbol;
    
    if (!activeSymbol) {
      alert('Please select or enter a symbol');
      return;
    }
    
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/advanced-strategies/calculate-indicators', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbol: activeSymbol,
          interval,
          duration,
          indicators: selectedIndicators.length > 0 ? selectedIndicators : ['all'],
          config: {}
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to calculate indicators');
      }
      
      const data = await response.json();
      setIndicatorData(data);
    } catch (error) {
      console.error('Error calculating indicators:', error);
      alert('Error calculating indicators: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const toggleIndicator = (indicatorName) => {
    setSelectedIndicators(prev => {
      if (prev.includes(indicatorName)) {
        return prev.filter(i => i !== indicatorName);
      } else {
        return [...prev, indicatorName];
      }
    });
  };

  const getIndicatorValue = (indicatorName) => {
    if (!indicatorData || !indicatorData.latest) return 'N/A';
    
    const latest = indicatorData.latest;
    
    if (indicatorName === 'rsi') {
      return latest.rsi ? latest.rsi.toFixed(2) : 'N/A';
    } else if (indicatorName === 'macd') {
      return latest.macd ? `${latest.macd.toFixed(2)} / ${latest.signal?.toFixed(2)}` : 'N/A';
    } else if (indicatorName === 'supertrend') {
      return latest.supertrend ? latest.supertrend.toFixed(2) : 'N/A';
    } else if (indicatorName === 'bollinger') {
      return latest.upper_band ? `${latest.upper_band.toFixed(2)} / ${latest.lower_band?.toFixed(2)}` : 'N/A';
    } else if (indicatorName === 'adx') {
      return latest.adx ? latest.adx.toFixed(2) : 'N/A';
    } else if (indicatorName === 'atr') {
      return latest.atr ? latest.atr.toFixed(2) : 'N/A';
    } else if (indicatorName === 'stochastic') {
      return latest.stoch_k ? `K: ${latest.stoch_k.toFixed(2)} D: ${latest.stoch_d?.toFixed(2)}` : 'N/A';
    } else if (indicatorName === 'ema') {
      return latest.ema_21 ? latest.ema_21.toFixed(2) : 'N/A';
    } else if (indicatorName === 'sma') {
      return latest.sma_20 ? latest.sma_20.toFixed(2) : 'N/A';
    }
    
    return 'N/A';
  };

  const getSignalColor = (indicatorName) => {
    if (!indicatorData || !indicatorData.latest) return 'neutral';
    
    const latest = indicatorData.latest;
    const close = latest.close;
    
    if (indicatorName === 'rsi') {
      if (latest.rsi < 30) return 'bullish';
      if (latest.rsi > 70) return 'bearish';
      return 'neutral';
    } else if (indicatorName === 'macd') {
      if (latest.macd > latest.signal) return 'bullish';
      if (latest.macd < latest.signal) return 'bearish';
      return 'neutral';
    } else if (indicatorName === 'supertrend') {
      if (close > latest.supertrend) return 'bullish';
      if (close < latest.supertrend) return 'bearish';
      return 'neutral';
    } else if (indicatorName === 'adx') {
      if (latest.adx > 25) return 'bullish';
      return 'neutral';
    }
    
    return 'neutral';
  };

  return (
    <div className="indicators-dashboard">
      <div className="dashboard-header">
        <h1>
          <MdInsights size={32} />
          Technical Indicators Dashboard
        </h1>
        <p>Real-time technical analysis and indicator calculations</p>
      </div>

      <div className="dashboard-content">
        {/* Controls */}
        <div className="controls-panel">
          <div className="symbol-config">
            <div className="form-group-inline">
              <label>Symbol</label>
              <div className="symbol-input-group">
                <select
                  value={symbol}
                  onChange={(e) => {
                    setSymbol(e.target.value);
                    setCustomSymbol("");
                  }}
                  disabled={!!customSymbol}
                >
                  <option value="">Select or enter custom...</option>
                  {ALL_SYMBOLS.map((s) => (
                    <option key={s.value} value={s.value}>
                      {s.label}
                    </option>
                  ))}
                </select>
                <span className="or-text">OR</span>
                <input
                  type="text"
                  value={customSymbol}
                  onChange={(e) => {
                    setCustomSymbol(e.target.value);
                    setSymbol("");
                  }}
                  placeholder="e.g., RELIANCE"
                  disabled={!!symbol}
                />
              </div>
            </div>

            <div className="form-group-inline">
              <label>Interval</label>
              <select value={interval} onChange={(e) => setInterval(e.target.value)}>
                <option value="1">1m</option>
                <option value="5">5m</option>
                <option value="15">15m</option>
                <option value="30">30m</option>
                <option value="60">1h</option>
                <option value="D">1d</option>
              </select>
            </div>

            <div className="form-group-inline">
              <label>Duration</label>
              <input
                type="number"
                value={duration}
                onChange={(e) => setDuration(parseInt(e.target.value))}
                min="1"
                max="365"
              />
            </div>

            <button 
              className="btn-calculate"
              onClick={calculateIndicators}
              disabled={loading}
            >
              {loading ? '⏳ Calculating...' : '🔄 Calculate'}
            </button>
          </div>

          <div className="indicator-selector">
            <h3>Select Indicators</h3>
            <div className="indicator-chips">
              {availableIndicators
                .filter(indicator => indicator.name !== 'pivot_points')
                .map(indicator => (
                <div
                  key={indicator.name}
                  className={`indicator-chip ${selectedIndicators.includes(indicator.name) ? 'selected' : ''}`}
                  onClick={() => toggleIndicator(indicator.name)}
                  title={indicator.description}
                >
                  {indicator.name.toUpperCase()}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Indicators Display */}
        {indicatorData && indicatorData.latest && (
          <div className="indicators-display">
            <div className="current-price-card">
              <div className="price-label">Current Price</div>
              <div className="price-value">
                ₹{indicatorData.latest.close?.toFixed(2) || 'N/A'}
              </div>
              <div className="price-info">
                <span>High: ₹{indicatorData.latest.high?.toFixed(2)}</span>
                <span>Low: ₹{indicatorData.latest.low?.toFixed(2)}</span>
              </div>
            </div>

            <div className="indicators-grid">
              {selectedIndicators.map(indicator => {
                const indicatorInfo = availableIndicators.find(i => i.name === indicator);
                const value = getIndicatorValue(indicator);
                const signalColor = getSignalColor(indicator);
                
                return (
                  <div key={indicator} className={`indicator-card ${signalColor}`}>
                    <div className="indicator-header">
                      <h4>{indicator.toUpperCase()}</h4>
                      <span className={`signal-dot ${signalColor}`}></span>
                    </div>
                    <div className="indicator-value">{value}</div>
                    <div className="indicator-description">
                      {indicatorInfo?.description || ''}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Data Table */}
            <div className="data-table-section">
              <h3>Historical Data (Last 20 candles)</h3>
              <div className="data-table-container">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Open</th>
                      <th>High</th>
                      <th>Low</th>
                      <th>Close</th>
                      {selectedIndicators.includes('rsi') && <th>RSI</th>}
                      {selectedIndicators.includes('macd') && <th>MACD</th>}
                      {selectedIndicators.includes('supertrend') && <th>Supertrend</th>}
                      {selectedIndicators.includes('adx') && <th>ADX</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {indicatorData.data && indicatorData.data.slice(-20).map((row, index) => (
                      <tr key={index}>
                        <td>{new Date(row.timestamp).toLocaleTimeString()}</td>
                        <td>₹{row.open?.toFixed(2)}</td>
                        <td className="price-high">₹{row.high?.toFixed(2)}</td>
                        <td className="price-low">₹{row.low?.toFixed(2)}</td>
                        <td className="price-close">₹{row.close?.toFixed(2)}</td>
                        {selectedIndicators.includes('rsi') && (
                          <td className={row.rsi < 30 ? 'bullish' : row.rsi > 70 ? 'bearish' : ''}>
                            {row.rsi?.toFixed(2) || '-'}
                          </td>
                        )}
                        {selectedIndicators.includes('macd') && (
                          <td>{row.macd?.toFixed(2) || '-'}</td>
                        )}
                        {selectedIndicators.includes('supertrend') && (
                          <td>{row.supertrend?.toFixed(2) || '-'}</td>
                        )}
                        {selectedIndicators.includes('adx') && (
                          <td>{row.adx?.toFixed(2) || '-'}</td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {!indicatorData && (
          <div className="empty-state">
            <p>📈 No indicator data available</p>
            <p className="hint">Select indicators and click "Calculate" to see real-time analysis</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default IndicatorsDashboard;
