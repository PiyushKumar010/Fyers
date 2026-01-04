import React, { useState, useEffect } from 'react';
import './AdvancedStrategyBuilder.css';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const AdvancedStrategyBuilder = () => {
  const [symbol, setSymbol] = useState('NSE:SBIN-EQ');
  const [interval, setInterval] = useState('5');
  const [duration, setDuration] = useState(30);
  const [strategy, setStrategy] = useState('supertrend_rsi');
  const [parameters, setParameters] = useState({});
  const [loading, setLoading] = useState(false);
  const [signals, setSignals] = useState([]);
  const [backtestResults, setBacktestResults] = useState(null);
  const [availableStrategies, setAvailableStrategies] = useState([]);
  const [showBacktest, setShowBacktest] = useState(false);

  useEffect(() => {
    fetchAvailableStrategies();
  }, []);

  const fetchAvailableStrategies = async () => {
    try {
      const response = await fetch(`${BASE_URL}/api/advanced-strategies/available-strategies`);
      const data = await response.json();
      setAvailableStrategies(data.strategies);
    } catch (error) {
      console.error('Error fetching strategies:', error);
    }
  };

  const generateSignals = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${BASE_URL}/api/advanced-strategies/generate-signals`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbol,
          interval,
          duration,
          strategy_name: strategy,
          parameters
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate signals');
      }
      
      const data = await response.json();
      setSignals(data.signals);
    } catch (error) {
      console.error('Error generating signals:', error);
      alert('Error generating signals: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const runBacktest = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${BASE_URL}/api/advanced-strategies/backtest`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbol,
          interval,
          duration,
          strategy_name: strategy,
          parameters,
          initial_capital: 100000
        }),
      });
      
      if (!response.ok) throw new Error('Failed to run backtest');
      
      const data = await response.json();
      setBacktestResults(data.backtest_results);
      setShowBacktest(true);
    } catch (error) {
      console.error('Error running backtest:', error);
      alert('Error running backtest: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const selectedStrategy = availableStrategies.find(s => s.name === strategy);

  return (
    <div className="advanced-strategy-builder">
      <div className="strategy-header">
        <h1>
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
          </svg>
          Advanced Strategy Builder
        </h1>
        <p>Build, test, and analyze trading strategies with multiple indicators</p>
      </div>

      <div className="strategy-content">
        {/* Configuration Panel */}
        <div className="config-panel">
          <h2>Strategy Configuration</h2>
          
          <div className="form-section">
            <div className="form-group">
              <label>Symbol</label>
              <input
                type="text"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                placeholder="e.g., NSE:SBIN-EQ"
              />
            </div>

            <div className="form-group">
              <label>Interval</label>
              <select value={interval} onChange={(e) => setInterval(e.target.value)}>
                <option value="1">1 Minute</option>
                <option value="5">5 Minutes</option>
                <option value="15">15 Minutes</option>
                <option value="30">30 Minutes</option>
                <option value="60">1 Hour</option>
                <option value="D">Daily</option>
              </select>
            </div>

            <div className="form-group">
              <label>Duration (days)</label>
              <input
                type="number"
                value={duration}
                onChange={(e) => setDuration(parseInt(e.target.value))}
                min="1"
                max="365"
              />
            </div>

            <div className="form-group">
              <label>Strategy</label>
              <select value={strategy} onChange={(e) => setStrategy(e.target.value)}>
                {availableStrategies.map(s => (
                  <option key={s.name} value={s.name}>{s.name}</option>
                ))}
              </select>
            </div>
          </div>

          {selectedStrategy && (
            <div className="strategy-description">
              <h3>Strategy Details</h3>
              <p>{selectedStrategy.description}</p>
              
              <h4>Parameters</h4>
              <div className="parameters-list">
                {Object.entries(selectedStrategy.parameters).map(([key, desc]) => (
                  <div key={key} className="parameter-item">
                    <label>{key}</label>
                    <small>{desc}</small>
                    <input
                      type="text"
                      placeholder="Default"
                      onChange={(e) => {
                        const value = e.target.value;
                        if (value) {
                          setParameters(prev => ({
                            ...prev,
                            [key]: isNaN(value) ? value : parseFloat(value)
                          }));
                        }
                      }}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="action-buttons">
            <button 
              className="btn-primary" 
              onClick={generateSignals}
              disabled={loading}
            >
              {loading ? 'Generating...' : '📊 Generate Signals'}
            </button>
            
            <button 
              className="btn-secondary" 
              onClick={runBacktest}
              disabled={loading}
            >
              {loading ? 'Running...' : '🎯 Run Backtest'}
            </button>
          </div>
        </div>

        {/* Results Panel */}
        <div className="results-panel">
          {!showBacktest ? (
            <>
              <h2>Trading Signals</h2>
              {signals.length > 0 ? (
                <div className="signals-list">
                  <div className="signals-summary">
                    <div className="summary-card">
                      <span className="label">Total Signals</span>
                      <span className="value">{signals.length}</span>
                    </div>
                    <div className="summary-card buy">
                      <span className="label">Buy Signals</span>
                      <span className="value">
                        {signals.filter(s => s.type === 'BUY').length}
                      </span>
                    </div>
                    <div className="summary-card sell">
                      <span className="label">Sell Signals</span>
                      <span className="value">
                        {signals.filter(s => s.type === 'SELL').length}
                      </span>
                    </div>
                  </div>

                  <div className="signals-table">
                    <table>
                      <thead>
                        <tr>
                          <th>Timestamp</th>
                          <th>Type</th>
                          <th>Price</th>
                          <th>Strategy</th>
                          <th>Details</th>
                        </tr>
                      </thead>
                      <tbody>
                        {signals.map((signal, index) => (
                          <tr key={index} className={signal.type.toLowerCase()}>
                            <td>{new Date(signal.timestamp).toLocaleString()}</td>
                            <td>
                              <span className={`signal-badge ${signal.type.toLowerCase()}`}>
                                {signal.type}
                              </span>
                            </td>
                            <td>₹{signal.price.toFixed(2)}</td>
                            <td>{signal.strategy}</td>
                            <td>
                              <button 
                                className="btn-details"
                                onClick={() => alert(JSON.stringify(signal.indicators, null, 2))}
                              >
                                View
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="empty-state">
                  <p>📈 No signals generated yet</p>
                  <p className="hint">Configure your strategy and click "Generate Signals" to see trading opportunities</p>
                </div>
              )}
            </>
          ) : (
            <>
              <div className="backtest-header">
                <h2>Backtest Results</h2>
                <button 
                  className="btn-back"
                  onClick={() => setShowBacktest(false)}
                >
                  ← Back to Signals
                </button>
              </div>

              {backtestResults && !backtestResults.error ? (
                <div className="backtest-results">
                  <div className="metrics-grid">
                    <div className="metric-card">
                      <span className="metric-label">Initial Capital</span>
                      <span className="metric-value">
                        ₹{backtestResults.initial_capital.toLocaleString()}
                      </span>
                    </div>
                    <div className="metric-card">
                      <span className="metric-label">Final Capital</span>
                      <span className="metric-value">
                        ₹{backtestResults.final_capital.toLocaleString()}
                      </span>
                    </div>
                    <div className={`metric-card ${backtestResults.total_pnl >= 0 ? 'positive' : 'negative'}`}>
                      <span className="metric-label">Total P&L</span>
                      <span className="metric-value">
                        ₹{backtestResults.total_pnl.toLocaleString()} 
                        ({backtestResults.total_pnl_percent.toFixed(2)}%)
                      </span>
                    </div>
                    <div className="metric-card">
                      <span className="metric-label">Total Trades</span>
                      <span className="metric-value">{backtestResults.total_trades}</span>
                    </div>
                    <div className="metric-card positive">
                      <span className="metric-label">Winning Trades</span>
                      <span className="metric-value">{backtestResults.winning_trades}</span>
                    </div>
                    <div className="metric-card negative">
                      <span className="metric-label">Losing Trades</span>
                      <span className="metric-value">{backtestResults.losing_trades}</span>
                    </div>
                    <div className="metric-card">
                      <span className="metric-label">Win Rate</span>
                      <span className="metric-value">{backtestResults.win_rate.toFixed(2)}%</span>
                    </div>
                    <div className="metric-card">
                      <span className="metric-label">Profit Factor</span>
                      <span className="metric-value">{backtestResults.profit_factor.toFixed(2)}</span>
                    </div>
                  </div>

                  <div className="trades-section">
                    <h3>Trade History</h3>
                    <div className="trades-table">
                      <table>
                        <thead>
                          <tr>
                            <th>Entry Time</th>
                            <th>Exit Time</th>
                            <th>Entry Price</th>
                            <th>Exit Price</th>
                            <th>Quantity</th>
                            <th>P&L</th>
                            <th>P&L %</th>
                          </tr>
                        </thead>
                        <tbody>
                          {backtestResults.trades && backtestResults.trades.map((trade, index) => (
                            <tr key={index} className={trade.pnl >= 0 ? 'profit' : 'loss'}>
                              <td>{new Date(trade.entry_time).toLocaleString()}</td>
                              <td>{new Date(trade.exit_time).toLocaleString()}</td>
                              <td>₹{trade.entry_price.toFixed(2)}</td>
                              <td>₹{trade.exit_price.toFixed(2)}</td>
                              <td>{trade.quantity}</td>
                              <td className={trade.pnl >= 0 ? 'positive' : 'negative'}>
                                ₹{trade.pnl.toFixed(2)}
                              </td>
                              <td className={trade.pnl_percent >= 0 ? 'positive' : 'negative'}>
                                {trade.pnl_percent.toFixed(2)}%
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="error-state">
                  <p>❌ {backtestResults?.error || 'Failed to run backtest'}</p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdvancedStrategyBuilder;
