import { useState, useEffect } from "react";
import { MdTrendingUp, MdRefresh } from "react-icons/md";
import StockSearchInput from "./StockSearchInput";
import { ALL_SYMBOLS } from "../constants/stocks";
import "./AutomatedTrading.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const ALL_STRATEGIES = [
  { value: "RSI", label: "RSI (Relative Strength Index)", description: "Overbought/oversold signals" },
  { value: "MACD", label: "MACD", description: "Trend-following momentum" },
  { value: "SUPERTREND", label: "Supertrend", description: "ATR-based trend detection" },
  { value: "BOLLINGER", label: "Bollinger Bands", description: "Volatility-based signals" },
  { value: "ADX", label: "ADX", description: "Trend strength indicator" },
  { value: "ATR", label: "ATR", description: "Average True Range - volatility measurement" },
  { value: "RENKO", label: "Renko", description: "Price movement-based trend detection" },
];

export default function AutomatedTrading() {
  const [config, setConfig] = useState({
    symbols: ["NSE:RELIANCE-EQ"],
    start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 30 days ago
    end_date: new Date().toISOString().split('T')[0], // Today
    stop_loss_percent: 2.0,
    profit_target_percent: 5.0,
    initial_capital: 100000,
    max_positions: 5,
    position_size_percent: 20,
    strategies: ["RSI", "MACD", "SUPERTREND", "BOLLINGER", "ADX"],
    mode: "HISTORICAL",
    timeframe: "5",
    session_id: `session_${Date.now()}`,
  });

  const [selectedSymbol, setSelectedSymbol] = useState("");
  const [customSymbol, setCustomSymbol] = useState("");

  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [sessionStatus, setSessionStatus] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [showAllTrades, setShowAllTrades] = useState(false);
  const [liveTrades, setLiveTrades] = useState(null);
  const [isLiveMode, setIsLiveMode] = useState(false);

  // Available strategies for selection
  const [availableStrategies, setAvailableStrategies] = useState([]);

  const normalizeSymbol = (sym) => {
    if (!sym) return "";
    const trimmed = sym.trim().toUpperCase();
    if (trimmed.includes(":")) return trimmed;
    return `NSE:${trimmed}-EQ`;
  };

  const handleSymbolDropdownChange = (e) => {
    const value = e.target.value;
    setSelectedSymbol(value);
    setCustomSymbol(""); // Clear custom input when dropdown is used
    if (value) {
      setConfig((prev) => ({ ...prev, symbols: [value] }));
    }
  };

  const handleCustomSymbolChange = (e) => {
    const value = e.target.value;
    setCustomSymbol(value);
    setSelectedSymbol(""); // Clear dropdown when custom input is used
    if (value) {
      const normalized = normalizeSymbol(value);
      setConfig((prev) => ({ ...prev, symbols: [normalized] }));
    }
  };

  // Fetch available strategies
  useEffect(() => {
    fetchAvailableStrategies();
  }, []);

  // On mount: restore active session from localStorage
  useEffect(() => {
    const restoreSession = async () => {
      setInitialLoading(true);
      const savedSessionId = localStorage.getItem('activeSessionId');
      if (savedSessionId) {
        console.log('[RESTORE] Found saved session:', savedSessionId);
        setActiveSession(savedSessionId);
        // Immediately check its status
        await fetchSessionStatus(savedSessionId);
      }
      await fetchSessions();
      setInitialLoading(false);
    };
    
    restoreSession();
  }, []);

  // Save active session to localStorage whenever it changes
  useEffect(() => {
    if (activeSession) {
      localStorage.setItem('activeSessionId', activeSession);
      console.log('[PERSIST] Saved active session to localStorage:', activeSession);
    } else {
      localStorage.removeItem('activeSessionId');
      console.log('[PERSIST] Removed active session from localStorage');
    }
  }, [activeSession]);

  // Poll for session status when active
  useEffect(() => {
    let interval;
    if (activeSession) {
      interval = setInterval(() => {
        fetchSessionStatus(activeSession);
      }, 3000); // Poll every 3 seconds
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [activeSession]);

  // Poll for live trades when in live mode
  useEffect(() => {
    let interval;
    if (activeSession && isLiveMode) {
      // Fetch immediately
      fetchLiveTrades(activeSession);
      
      // Then poll every 5 seconds
      interval = setInterval(() => {
        fetchLiveTrades(activeSession);
      }, 5000);
    } else {
      setLiveTrades(null);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [activeSession, isLiveMode]);

  const fetchAvailableStrategies = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/automated-trading/strategies`);
      const data = await response.json();
      setAvailableStrategies(data.strategies || []);
    } catch (err) {
      console.error("Failed to fetch strategies:", err);
    }
  };

  const fetchSessions = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/automated-trading/sessions`);
      const data = await response.json();
      setSessions(data.sessions || []);
    } catch (err) {
      console.error("Failed to fetch sessions:", err);
    }
  };

  const fetchSessionStatus = async (sessionId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/automated-trading/status/${sessionId}`);
      const data = await response.json();
      setSessionStatus(data);

      // If completed or error, stop loading and fetch results
      if (data.status === "completed") {
        setLoading(false);
        if (!results) {
          fetchResults(sessionId);
        }
        // Clear active session from localStorage after completion
        localStorage.removeItem('activeSessionId');
      } else if (data.status === "error") {
        setLoading(false);
        setError(data.error || "Trading session failed");
        // Clear active session from localStorage after error
        localStorage.removeItem('activeSessionId');
      } else if (data.status === "not_found") {
        // Session not found - might have been deleted or never existed
        setActiveSession(null);
        setSessionStatus(null);
        localStorage.removeItem('activeSessionId');
      }
    } catch (err) {
      console.error("Failed to fetch session status:", err);
    }
  };

  const fetchResults = async (sessionId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/automated-trading/results/${sessionId}`);
      const data = await response.json();
      setResults(data);
    } catch (err) {
      console.error("Failed to fetch results:", err);
    }
  };

  const fetchLiveTrades = async (sessionId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/automated-trading/live-trades/${sessionId}`);
      if (response.ok) {
        const data = await response.json();
        setLiveTrades(data);
      } else if (response.status === 404) {
        // Session not active anymore
        setIsLiveMode(false);
        setLiveTrades(null);
      }
    } catch (err) {
      console.error("Failed to fetch live trades:", err);
    }
  };

  const startTrading = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);
    setResults(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/automated-trading/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess(`Automated trading started! Session: ${data.session_id}`);
        setActiveSession(data.session_id);
        setIsLiveMode(config.mode === "LIVE");
        fetchSessions();
        // Don't set loading to false here - let the status polling handle it
      } else {
        setError(data.detail || "Failed to start automated trading");
        setLoading(false);
      }
    } catch (err) {
      setError(`Error: ${err.message}`);
      setLoading(false);
    }
  };

  const stopTrading = async (sessionId) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/automated-trading/stop/${sessionId}`, {
        method: "POST",
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess(`Trading stopped. Closed ${data.closed_positions?.length || 0} positions.`);
        setResults(data.final_results);
        setActiveSession(null);
        setIsLiveMode(false);
        setLiveTrades(null);
        setLoading(false);
        localStorage.removeItem('activeSessionId');
        fetchSessions();
      } else {
        setError(data.detail || "Failed to stop trading");
        setLoading(false);
      }
    } catch (err) {
      setError(`Error: ${err.message}`);
      setLoading(false);
    }
  };

  const deleteSession = async (sessionId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/automated-trading/session/${sessionId}`, {
        method: "DELETE",
      });

      if (response.ok) {
        setSuccess(`Session ${sessionId} deleted`);
        if (activeSession === sessionId) {
          setActiveSession(null);
          setSessionStatus(null);
          setResults(null);
          localStorage.removeItem('activeSessionId');
        }
        fetchSessions();
      }
    } catch (err) {
      setError(`Error: ${err.message}`);
    }
  };

  const handleSymbolToggle = (symbol) => {
    setConfig((prev) => {
      const symbols = prev.symbols.includes(symbol)
        ? prev.symbols.filter((s) => s !== symbol)
        : [...prev.symbols, symbol];
      return { ...prev, symbols };
    });
  };

  const handleStrategyToggle = (strategy) => {
    setConfig((prev) => {
      const strategies = prev.strategies.includes(strategy)
        ? prev.strategies.filter((s) => s !== strategy)
        : [...prev.strategies, strategy];
      return { ...prev, strategies };
    });
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (value) => {
    return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
  };

  return (
    <div className="automated-trading-container">
      {/* Initial Loading State */}
      {initialLoading && (
        <div className="initial-loading">
          <div className="loading-spinner">
            <svg className="spinner" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
            </svg>
          </div>
          <p>Loading your trading session...</p>
        </div>
      )}

      {/* Main Content - Show only after initial loading */}
      {!initialLoading && (
        <>
      <div className="page-header">
        <h1>
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
          Automated Trading
        </h1>
        <p className="subtitle">
          Run multiple strategies automatically with stop loss and profit targets
        </p>
      {/* Loading Indicator */}
      {loading && (
        <div style={{
          padding: "20px",
          backgroundColor: "#fff3cd",
          border: "1px solid #ffc107",
          borderRadius: "8px",
          marginBottom: "20px",
          display: "flex",
          alignItems: "center",
          gap: "15px"
        }}>
          <svg 
            width="24" 
            height="24" 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="#856404" 
            strokeWidth="2"
            style={{ animation: "spin 1s linear infinite" }}
          >
            <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
          </svg>
          <div style={{ color: "#856404" }}>
            <strong>Processing...</strong>
            <p style={{ margin: "5px 0 0 0", fontSize: "0.9em" }}>
              {config.mode === "HISTORICAL" 
                ? "Running backtest on historical data. This may take a moment depending on date range and number of symbols."
                : "Connecting to live market data and monitoring for trading signals..."}
            </p>
          </div>
        </div>
      )}

      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <div className="trading-grid">
        {/* Configuration Panel */}
        <div className="config-panel card">
          <h2>Trading Configuration</h2>
          <form onSubmit={startTrading}>
            {/* Trading Mode */}
            <div className="form-group">
              <label>Trading Mode</label>
              <div className="radio-group">
                <label className="radio-label">
                  <input
                    type="radio"
                    value="HISTORICAL"
                    checked={config.mode === "HISTORICAL"}
                    onChange={(e) => setConfig({ ...config, mode: e.target.value })}
                  />
                  Historical (Backtest)
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    value="LIVE"
                    checked={config.mode === "LIVE"}
                    onChange={(e) => setConfig({ ...config, mode: e.target.value })}
                  />
                  Live Trading
                </label>
              </div>
              <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "8px" }}>
                {config.mode === "HISTORICAL" 
                  ? "Backtest on historical data with specific date range" 
                  : "Trade in real-time using current market data (no date range needed)"}
              </p>
            </div>

            {/* Date Range - Only show for HISTORICAL mode */}
            {config.mode === "HISTORICAL" && (
              <div className="form-row">
                <div className="form-group">
                  <label>Start Date</label>
                  <input
                    type="date"
                    value={config.start_date}
                    onChange={(e) => setConfig({ ...config, start_date: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>End Date</label>
                  <input
                    type="date"
                    value={config.end_date}
                    onChange={(e) => setConfig({ ...config, end_date: e.target.value })}
                    required
                  />
                </div>
              </div>
            )}

            {/* Stock Symbol Selection */}
            <div className="form-group">
              <label>Select Stock</label>
              <StockSearchInput
                value={config.symbols[0] || ''}
                onChange={(newSymbol) => {
                  setSelectedSymbol(newSymbol);
                  setCustomSymbol("");
                  setConfig({ ...config, symbols: [newSymbol] });
                }}
                placeholder="Search by symbol or company name..."
                required
              />
              <p className="helper-text">Currently selected: {config.symbols[0] || 'None'}</p>
            </div>

            {/* Strategies */}
            <div className="form-group">
              <label>Select Strategies</label>
              <div className="checkbox-grid">
                {ALL_STRATEGIES.map((strat) => (
                  <label key={strat.value} className="checkbox-label" title={strat.description}>
                    <input
                      type="checkbox"
                      checked={config.strategies.includes(strat.value)}
                      onChange={() => handleStrategyToggle(strat.value)}
                    />
                    {strat.label}
                  </label>
                ))}
              </div>
            </div>

            {/* Risk Management */}
            <div className="form-row">
              <div className="form-group">
                <label>Stop Loss (%)</label>
                <input
                  type="number"
                  min="0.1"
                  max="10"
                  step="0.1"
                  value={config.stop_loss_percent}
                  onChange={(e) =>
                    setConfig({ ...config, stop_loss_percent: parseFloat(e.target.value) })
                  }
                  required
                />
              </div>
              <div className="form-group">
                <label>Profit Target (%)</label>
                <input
                  type="number"
                  min="0.5"
                  max="20"
                  step="0.1"
                  value={config.profit_target_percent}
                  onChange={(e) =>
                    setConfig({ ...config, profit_target_percent: parseFloat(e.target.value) })
                  }
                  required
                />
              </div>
            </div>

            {/* Capital Management */}
            <div className="form-row">
              <div className="form-group">
                <label>Initial Capital (₹)</label>
                <input
                  type="number"
                  min="10000"
                  step="1000"
                  value={config.initial_capital}
                  onChange={(e) =>
                    setConfig({ ...config, initial_capital: parseFloat(e.target.value) })
                  }
                  required
                />
              </div>
              <div className="form-group">
                <label>Max Positions</label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={config.max_positions}
                  onChange={(e) =>
                    setConfig({ ...config, max_positions: parseInt(e.target.value) })
                  }
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label>Position Size (% of capital)</label>
              <input
                type="number"
                min="5"
                max="50"
                step="0.1"
                value={config.position_size_percent}
                onChange={(e) =>
                  setConfig({ ...config, position_size_percent: parseFloat(e.target.value) })
                }
                required
              />
            </div>

            <button type="submit" className="btn btn-primary" disabled={loading || activeSession}>
              {loading ? (
                <>
                  <svg className="button-icon spin" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
                  </svg>
                  Starting...
                </>
              ) : (
                <>
                  <svg className="button-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polygon points="5 3 19 12 5 21 5 3"></polygon>
                  </svg>
                  Start Automated Trading
                </>
              )}
            </button>
          </form>
        </div>

        {/* Status Panel */}
        <div className="status-panel">
          {/* Current Session Status */}
          {sessionStatus && activeSession && (
            <div className="card">
              <h2>Current Session Status</h2>
              <div className="status-badge status-{sessionStatus.status}">
                {sessionStatus.status.toUpperCase()}
              </div>

              {/* Show error if status is error */}
              {sessionStatus.status === "error" && sessionStatus.error && (
                <div style={{
                  padding: "15px",
                  backgroundColor: "#fee",
                  border: "1px solid #fcc",
                  borderRadius: "8px",
                  marginTop: "15px"
                }}>
                  <strong>⚠️ Error:</strong>
                  <p style={{ margin: "8px 0" }}>{sessionStatus.error}</p>
                  {sessionStatus.error.includes("No historical data") && (
                    <div style={{ marginTop: "10px", fontSize: "0.9em" }}>
                      <strong>Suggestions:</strong>
                      <ul style={{ marginLeft: "20px", marginTop: "5px" }}>
                        <li>Ensure you're authenticated with Fyers (check for "Re-authenticate" button)</li>
                        <li>Use dates in the past (not today or future dates)</li>
                        <li>Verify symbol format (e.g., NSE:RELIANCE-EQ)</li>
                        <li>Check if market was open on selected dates</li>
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {sessionStatus.progress && (
                <div className="progress-stats">
                  <div className="stat-item">
                    <span className="stat-label">Portfolio Value</span>
                    <span className="stat-value">
                      {formatCurrency(sessionStatus.progress.portfolio_value)}
                    </span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Total P&L</span>
                    <span
                      className={`stat-value ${
                        sessionStatus.progress.total_pnl >= 0 ? "positive" : "negative"
                      }`}
                    >
                      {formatCurrency(sessionStatus.progress.total_pnl)}
                    </span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Open Positions</span>
                    <span className="stat-value">{sessionStatus.progress.open_positions}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Total Trades</span>
                    <span className="stat-value">{sessionStatus.progress.total_trades}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Signals Generated</span>
                    <span className="stat-value">{sessionStatus.progress.total_signals}</span>
                  </div>
                </div>
              )}

              {/* Only show stop button if trading is actually running (not completed) */}
              {sessionStatus.status === "running" && (
                <button
                  className="btn btn-danger"
                  onClick={() => stopTrading(activeSession)}
                  style={{ marginTop: "1rem" }}
                >
                  ⏹️ Stop Trading
                </button>
              )}
            </div>
          )}

          {/* Live Trades Display */}
          {liveTrades && isLiveMode && (
            <div className="card live-trades-card">
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "15px" }}>
                <h2>🔴 Live Trading</h2>
                <span className="live-badge">LIVE</span>
              </div>
              
              {/* Portfolio Stats */}
              <div className="portfolio-grid" style={{ marginBottom: "20px" }}>
                <div className="metric-card">
                  <span className="metric-label">Portfolio Value</span>
                  <span className="metric-value">
                    {formatCurrency(liveTrades.portfolio.portfolio_value)}
                  </span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Total P&L</span>
                  <span className={`metric-value ${liveTrades.portfolio.total_pnl >= 0 ? "positive" : "negative"}`}>
                    {formatCurrency(liveTrades.portfolio.total_pnl)}
                    {" "}({liveTrades.portfolio.total_pnl_percent.toFixed(2)}%)
                  </span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Cash Available</span>
                  <span className="metric-value">
                    {formatCurrency(liveTrades.portfolio.cash)}
                  </span>
                </div>
                <div className="metric-card">
                  <span className="metric-label">Win Rate</span>
                  <span className="metric-value">
                    {liveTrades.statistics.win_rate.toFixed(1)}%
                  </span>
                </div>
              </div>

              {/* Open Positions */}
              {liveTrades.positions.open_count > 0 && (
                <div className="results-section" style={{ marginBottom: "20px" }}>
                  <h3>🔵 Open Positions ({liveTrades.positions.open_count})</h3>
                  <div className="table-container">
                    <table>
                      <thead>
                        <tr>
                          <th>Symbol</th>
                          <th>Strategy</th>
                          <th>Entry Price</th>
                          <th>Current Price</th>
                          <th>Qty</th>
                          <th>P&L</th>
                          <th>%</th>
                          <th>Entry Time</th>
                        </tr>
                      </thead>
                      <tbody>
                        {liveTrades.positions.open.map((pos, idx) => (
                          <tr key={idx}>
                            <td><strong>{pos.symbol.replace("NSE:", "").replace("-EQ", "")}</strong></td>
                            <td><span className="strategy-badge">{pos.strategy}</span></td>
                            <td>{formatCurrency(pos.entry_price)}</td>
                            <td>{formatCurrency(pos.current_price)}</td>
                            <td>{pos.quantity}</td>
                            <td className={pos.unrealized_pnl >= 0 ? "positive" : "negative"}>
                              {formatCurrency(pos.unrealized_pnl)}
                            </td>
                            <td className={pos.pnl_percent >= 0 ? "positive" : "negative"}>
                              {pos.pnl_percent.toFixed(2)}%
                            </td>
                            <td>{new Date(pos.entry_time).toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Recent Closed Trades */}
              {liveTrades.positions.closed_count > 0 && (
                <div className="results-section">
                  <h3>✅ Recent Closed Trades (Last 20 / Total: {liveTrades.statistics.total_trades})</h3>
                  <div style={{ marginBottom: "10px", fontSize: "0.9em", color: "#666" }}>
                    <strong>Win/Loss:</strong> {liveTrades.statistics.winning_trades}W / {liveTrades.statistics.losing_trades}L
                  </div>
                  <div className="table-container">
                    <table>
                      <thead>
                        <tr>
                          <th>Symbol</th>
                          <th>Strategy</th>
                          <th>Entry</th>
                          <th>Exit</th>
                          <th>Qty</th>
                          <th>P&L</th>
                          <th>%</th>
                          <th>Exit Reason</th>
                          <th>Exit Time</th>
                        </tr>
                      </thead>
                      <tbody>
                        {liveTrades.positions.closed.reverse().map((trade, idx) => (
                          <tr key={idx}>
                            <td><strong>{trade.symbol.replace("NSE:", "").replace("-EQ", "")}</strong></td>
                            <td><span className="strategy-badge">{trade.strategy}</span></td>
                            <td>{formatCurrency(trade.entry_price)}</td>
                            <td>{formatCurrency(trade.exit_price)}</td>
                            <td>{trade.quantity}</td>
                            <td className={trade.realized_pnl >= 0 ? "positive" : "negative"}>
                              {formatCurrency(trade.realized_pnl)}
                            </td>
                            <td className={trade.pnl_percent >= 0 ? "positive" : "negative"}>
                              {trade.pnl_percent.toFixed(2)}%
                            </td>
                            <td>{trade.exit_reason}</td>
                            <td>{new Date(trade.exit_time).toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              <div style={{
                marginTop: "15px",
                padding: "10px",
                backgroundColor: "#f5f5f5",
                borderRadius: "6px",
                fontSize: "0.85em",
                color: "#666",
                textAlign: "center"
              }}>
                ⏱️ Auto-refreshing every 5 seconds | Last update: {new Date(liveTrades.timestamp).toLocaleTimeString()}
              </div>
            </div>
          )}

          {/* Results Panel */}
          {results && (
            <div className="card results-card">
              <h2>📊 Trading Results</h2>
              
              {/* Info Banner - Fixed styling */}
              <div style={{
                padding: "12px 15px",
                backgroundColor: "#e3f2fd",
                border: "1px solid #2196f3",
                borderRadius: "6px",
                marginBottom: "16px",
                fontSize: "0.9em",
                color: "#01579b"
              }}>
                <strong style={{ color: "#0d47a1" }}>💡 Understanding Results:</strong>
                <ul style={{margin: "8px 0 0 20px", padding: 0, color: "#01579b"}}>
                  <li><strong>Charges</strong> = Real brokerage fees (₹20 per trade) deducted from each trade</li>
                  <li><strong>Realized P&L</strong> = Profit/Loss from completed (closed) trades</li>
                  <li><strong>Unrealized P&L</strong> = Paper profit/loss from open positions (not yet realized)</li>
                  <li><strong>Total P&L</strong> = Realized + Unrealized - Charges (combined result from ALL strategies)</li>
                  <li><strong>Strategy Column</strong> = Which strategies triggered each trade (e.g., "RSI, MACD")</li>
                </ul>
              </div>

              {/* Portfolio Summary */}
              <div className="results-section">
                <h3>Portfolio Summary</h3>
                <div className="portfolio-grid">
                  <div className="metric-card">
                    <span className="metric-label">Initial Capital</span>
                    <span className="metric-value">
                      {formatCurrency(results.portfolio.initial_capital)}
                    </span>
                  </div>
                  <div className="metric-card">
                    <span className="metric-label" title="Initial + Realized + Unrealized - Charges">🎯 Final Value</span>
                    <span className="metric-value">
                      {formatCurrency(results.portfolio.final_value)}
                    </span>
                  </div>
                  <div className="metric-card">
                    <span className="metric-label" title="Profit/Loss from closed trades">💰 Realized P&L</span>
                    <span
                      className={`metric-value ${
                        results.portfolio.realized_pnl >= 0 ? "positive" : "negative"
                      }`}
                    >
                      {formatCurrency(results.portfolio.realized_pnl)}
                    </span>
                  </div>
                  <div className="metric-card">
                    <span className="metric-label" title="Paper gains/losses from open positions">📊 Unrealized P&L</span>
                    <span
                      className={`metric-value ${
                        results.portfolio.unrealized_pnl >= 0 ? "positive" : "negative"
                      }`}
                    >
                      {formatCurrency(results.portfolio.unrealized_pnl)}
                    </span>
                  </div>
                  <div className="metric-card">
                    <span className="metric-label" title="Real brokerage: ₹20 per trade (buy + sell)">💳 Charges</span>
                    <span className="metric-value negative">
                      {formatCurrency(results.portfolio.total_charges || 0)}
                    </span>
                  </div>
                  <div className="metric-card">
                    <span className="metric-label" title="Combined result from ALL strategies: Realized + Unrealized - Charges">Total P&L</span>
                    <span
                      className={`metric-value ${
                        results.portfolio.total_pnl >= 0 ? "positive" : "negative"
                      }`}
                    >
                      {formatCurrency(results.portfolio.total_pnl)}
                    </span>
                  </div>
                  <div className="metric-card">
                    <span className="metric-label" title="(Final Value - Initial) / Initial × 100">Returns %</span>
                    <span
                      className={`metric-value ${
                        results.portfolio.returns_percent >= 0 ? "positive" : "negative"
                      }`}
                    >
                      {formatPercent(results.portfolio.returns_percent)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Performance Metrics */}
              <div className="results-section">
                <h3>Performance Metrics</h3>
                <div className="metrics-grid">
                  <div className="metric-item">
                    <span className="metric-label">Total Trades</span>
                    <span className="metric-value">{results.performance.total_trades}</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Winning Trades</span>
                    <span className="metric-value positive">
                      {results.performance.winning_trades}
                    </span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Losing Trades</span>
                    <span className="metric-value negative">
                      {results.performance.losing_trades}
                    </span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Win Rate</span>
                    <span className="metric-value">{results.performance.win_rate}%</span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Avg Win</span>
                    <span className="metric-value positive">
                      {formatCurrency(results.performance.avg_win)}
                    </span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Avg Loss</span>
                    <span className="metric-value negative">
                      {formatCurrency(results.performance.avg_loss)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Strategy Breakdown */}
              {results.signals && results.signals.signal_breakdown && (
                <div className="results-section">
                  <h3>Strategy Signals (Total: {results.signals.total_signals_generated || 0})</h3>
                  <p className="signals-note">Note: Signals are NOT trades. Trades occur when signal aggregation triggers execution.</p>
                  <div className="strategy-breakdown">
                    {Object.entries(results.signals.signal_breakdown).map(([strategy, stats]) => (
                      <div key={strategy} className="strategy-stat">
                        <span className="strategy-name">{strategy}</span>
                        <span className="strategy-signals">
                          Buy: {stats.BUY || 0} | Sell: {stats.SELL || 0} | Total: {stats.total}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Executed Trades */}
              {results.executed_trades && results.executed_trades.length > 0 && (
                <div className="results-section">
                  <h3>Executed Trades ({results.executed_trades.length} completed round trips)</h3>
                  <div className="trades-table">
                    <table>
                      <thead>
                        <tr>
                          <th>Symbol</th>
                          <th>Side</th>
                          <th>Quantity</th>
                          <th>Entry Price</th>
                          <th>Exit Price</th>
                          <th>Net P&L</th>
                          <th>Strategy</th>
                          <th>Entry Time</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(showAllTrades ? results.executed_trades : results.executed_trades.slice(0, 10)).map((trade, idx) => (
                          <tr key={idx}>
                            <td>{trade.symbol}</td>
                            <td className={trade.entry_side === "LONG" ? "buy" : "sell"}>
                              {trade.entry_side}
                            </td>
                            <td>{trade.quantity}</td>
                            <td>{formatCurrency(trade.entry_price)}</td>
                            <td>{formatCurrency(trade.exit_price)}</td>
                            <td className={trade.net_pnl >= 0 ? "positive" : "negative"}>
                              {formatCurrency(trade.net_pnl)}
                            </td>
                            <td>{trade.strategy}</td>
                            <td>{trade.entry_timestamp ? new Date(trade.entry_timestamp).toLocaleString() : 'N/A'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  
                  {/* Show More/Less Button */}
                  {results.executed_trades.length > 10 && (
                    <div style={{ textAlign: "center", marginTop: "15px" }}>
                      <button
                        onClick={() => setShowAllTrades(!showAllTrades)}
                        className="btn btn-secondary"
                        style={{
                          padding: "10px 20px",
                          fontSize: "0.95rem",
                          backgroundColor: "#6c757d",
                          color: "white",
                          border: "none",
                          borderRadius: "6px",
                          cursor: "pointer",
                          transition: "all 0.2s ease"
                        }}
                        onMouseOver={(e) => e.target.style.backgroundColor = "#5a6268"}
                        onMouseOut={(e) => e.target.style.backgroundColor = "#6c757d"}
                      >
                        {showAllTrades 
                          ? `Show Less (showing all ${results.executed_trades.length} trades)` 
                          : `Show More (showing 10 of ${results.executed_trades.length} trades)`
                        }
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      </>
      )}
    </div>
  );
}
