import { useState, useEffect } from "react";
import { MdTrendingUp, MdAttachMoney, MdShowChart, MdAccessTime, MdPlayArrow, MdError, MdTimeline, MdSpeed, MdTrendingDown, MdHistory, MdClose, MdDelete } from "react-icons/md";
import { ALL_SYMBOLS, normalizeSymbol } from "../constants/stocks";
import "./StrategyExecutor.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const TIMEFRAMES = [
  { value: "1", label: "1 Minute" },
  { value: "5", label: "5 Minutes" },
  { value: "15", label: "15 Minutes" },
  { value: "60", label: "1 Hour" },
  { value: "D", label: "1 Day" },
];

export default function StrategyExecutor() {
  const [strategies, setStrategies] = useState([]);
  const [selectedStrategy, setSelectedStrategy] = useState("");
  const [strategyParams, setStrategyParams] = useState({});
  const [symbol, setSymbol] = useState("NSE:RELIANCE-EQ");
  const [customSymbol, setCustomSymbol] = useState("");
  const [timeframe, setTimeframe] = useState("5");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [executionHistory, setExecutionHistory] = useState(() => {
    const saved = localStorage.getItem('strategyHistory');
    return saved ? JSON.parse(saved) : [];
  });

  // Fetch available strategies
  useEffect(() => {
    fetchStrategies();
  }, []);

  // Save history to localStorage
  useEffect(() => {
    localStorage.setItem('strategyHistory', JSON.stringify(executionHistory));
  }, [executionHistory]);

  const fetchStrategies = async () => {
    try {
      const response = await fetch(`${API_BASE}/strategies`);
      const data = await response.json();
      setStrategies(data.strategies || []);
      
      // Set default params for first strategy
      if (data.strategies && data.strategies.length > 0 && !selectedStrategy) {
        const firstStrategy = data.strategies[0];
        const defaultParams = data.details[firstStrategy]?.params || {};
        setSelectedStrategy(firstStrategy);
        setStrategyParams(defaultParams);
      }
    } catch (err) {
      console.error("Failed to fetch strategies:", err);
      setError("Failed to load strategies");
    }
  };

  const handleStrategyChange = (e) => {
    const strategy = e.target.value;
    setSelectedStrategy(strategy);
    
    // Fetch default params for selected strategy
    fetch(`${API_BASE}/strategies`)
      .then(res => res.json())
      .then(data => {
        const defaultParams = data.details[strategy]?.params || {};
        setStrategyParams(defaultParams);
      });
    
    setResult(null);
  };

  const handleParamChange = (paramName, value) => {
    setStrategyParams({
      ...strategyParams,
      [paramName]: value === "" ? null : (isNaN(value) ? value : parseFloat(value))
    });
  };

  const executeStrategy = async () => {
    const activeSymbol = customSymbol ? normalizeSymbol(customSymbol) : symbol;
    
    if (!selectedStrategy || !activeSymbol) {
      setError("Please select a strategy and enter a symbol");
      return;
    }

    if (!startDate || !endDate) {
      setError("Please select both start date and end date");
      return;
    }

    if (new Date(startDate) > new Date(endDate)) {
      setError("Start date must be before end date");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${API_BASE}/strategies/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          strategy: selectedStrategy,
          symbol: activeSymbol,  // Send full symbol format
          timeframe: timeframe,
          start_date: startDate,
          end_date: endDate,
          params: strategyParams
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Strategy execution failed");
      }

      const data = await response.json();
      setResult(data);

      // Add to history
      const historyEntry = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        strategy: selectedStrategy,
        symbol: activeSymbol,
        timeframe: timeframe,
        startDate: startDate,
        endDate: endDate,
        signal: data.signal,
        params: strategyParams,
        result: data
      };
      setExecutionHistory(prev => [historyEntry, ...prev].slice(0, 50)); // Keep last 50
    } catch (err) {
      setError(err.message || "Failed to execute strategy");
    } finally {
      setLoading(false);
    }
  };

  const getSignalColor = (signal) => {
    if (!signal) return "#666";
    const signalUpper = signal.toUpperCase();
    if (signalUpper.includes("BUY") || signalUpper.includes("BULLISH") || signalUpper.includes("STRONG")) {
      return "#059669";
    } else if (signalUpper.includes("SELL") || signalUpper.includes("BEARISH") || signalUpper.includes("WEAK")) {
      return "#dc2626";
    } else if (signalUpper.includes("OVERSOLD")) {
      return "#059669";
    } else if (signalUpper.includes("OVERBOUGHT")) {
      return "#dc2626";
    }
    return "#666";
  };

  const getStrategyParamFields = () => {
    if (!selectedStrategy) return null;

    const paramFields = {
      ADX: [
        { name: "period", label: "ADX Period", type: "number", default: 14, min: 5, max: 50 },
        { name: "threshold", label: "Trend Strength Threshold", type: "number", default: 25, min: 15, max: 40, step: 1 }
      ],
      ATR: [
        { name: "period", label: "ATR Period", type: "number", default: 14, min: 5, max: 50 },
        { name: "multiplier", label: "Volatility Multiplier", type: "number", default: 2.0, min: 1.0, max: 5.0, step: 0.5 }
      ],
      BOLLINGER: [
        { name: "period", label: "Period (SMA)", type: "number", default: 20, min: 10, max: 50 },
        { name: "std_dev", label: "Standard Deviation", type: "number", default: 2.0, min: 1.0, max: 3.0, step: 0.1 },
        { name: "band_width_threshold", label: "Band Width Threshold (%)", type: "number", default: 4.0, min: 2.0, max: 10.0, step: 0.5 }
      ],
      MACD: [
        { name: "fast_period", label: "Fast EMA Period", type: "number", default: 12, min: 5, max: 26 },
        { name: "slow_period", label: "Slow EMA Period", type: "number", default: 26, min: 12, max: 50 },
        { name: "signal_period", label: "Signal EMA Period", type: "number", default: 9, min: 5, max: 20 },
        { name: "histogram_threshold", label: "Histogram Threshold", type: "number", default: 0.0, min: 0.0, max: 5.0, step: 0.1 }
      ],
      RSI: [
        { name: "period", label: "RSI Period", type: "number", default: 14, min: 5, max: 30 },
        { name: "oversold", label: "Oversold Level", type: "number", default: 30, min: 20, max: 40 },
        { name: "overbought", label: "Overbought Level", type: "number", default: 70, min: 60, max: 80 },
        { name: "divergence_lookback", label: "Divergence Lookback", type: "number", default: 5, min: 3, max: 10 }
      ],
      SUPERTREND: [
        { name: "atr_period", label: "ATR Period", type: "number", default: 7, min: 5, max: 20 },
        { name: "multiplier", label: "ATR Multiplier", type: "number", default: 3.0, min: 1.0, max: 5.0, step: 0.1 },
        { name: "confirmation_candles", label: "Confirmation Candles", type: "number", default: 1, min: 1, max: 3 }
      ],
      RENKO: [
        { name: "brick_size", label: "Fixed Brick Size (optional)", type: "number", default: null, min: 0.1, step: 0.1 },
        { name: "atr_period", label: "ATR Period (for dynamic)", type: "number", default: 14, min: 5, max: 30 },
        { name: "atr_multiplier", label: "ATR Multiplier", type: "number", default: 1.0, min: 0.5, max: 3.0, step: 0.1 },
        { name: "lookback", label: "Lookback Bricks", type: "number", default: 3, min: 2, max: 10 }
      ],
      EMA: [
        { name: "fast_period", label: "Fast EMA Period", type: "number", default: 9, min: 5, max: 21 },
        { name: "slow_period", label: "Slow EMA Period", type: "number", default: 21, min: 20, max: 100 },
        { name: "trend_filter_period", label: "Trend Filter Period", type: "number", default: 50, min: 30, max: 200 }
      ],
      SMA: [
        { name: "fast_period", label: "Fast SMA Period", type: "number", default: 10, min: 5, max: 30 },
        { name: "slow_period", label: "Slow SMA Period", type: "number", default: 20, min: 15, max: 100 },
        { name: "long_period", label: "Long-term SMA", type: "number", default: 50, min: 40, max: 200 }
      ],
      STOCHASTIC: [
        { name: "k_period", label: "%K Period", type: "number", default: 14, min: 5, max: 30 },
        { name: "d_period", label: "%D Period (Signal)", type: "number", default: 3, min: 2, max: 10 },
        { name: "smooth_k", label: "Smooth %K", type: "number", default: 3, min: 1, max: 5 },
        { name: "oversold", label: "Oversold Level", type: "number", default: 20, min: 10, max: 30 },
        { name: "overbought", label: "Overbought Level", type: "number", default: 80, min: 70, max: 90 }
      ]
    };

    return paramFields[selectedStrategy] || [];
  };

  return (
    <div className="strategy-executor">
      <div className="executor-header">
        <div>
          <h2>
            <MdTrendingUp />
            Strategy Executor
          </h2>
          <p>Execute technical analysis strategies on stock data</p>
        </div>
        <button 
          className="history-toggle-btn"
          onClick={() => setShowHistory(!showHistory)}
          title="View Execution History"
        >
          <MdHistory size={24} />
          History ({executionHistory.length})
        </button>
      </div>

      {/* History Panel */}
      {showHistory && (
        <div className="history-panel">
          <div className="history-header">
            <h3>
              <MdHistory />
              Execution History
            </h3>
            <div className="history-actions">
              {executionHistory.length > 0 && (
                <button 
                  className="clear-history-btn"
                  onClick={() => {
                    if (window.confirm('Clear all execution history?')) {
                      setExecutionHistory([]);
                    }
                  }}
                  title="Clear All History"
                >
                  <MdDelete size={20} />
                  Clear All
                </button>
              )}
              <button 
                className="close-history-btn"
                onClick={() => setShowHistory(false)}
                title="Close"
              >
                <MdClose size={24} />
              </button>
            </div>
          </div>
          
          <div className="history-content">
            {executionHistory.length === 0 ? (
              <div className="history-empty">
                <MdHistory size={48} />
                <p>No execution history yet</p>
                <span>Run a strategy to see it here</span>
              </div>
            ) : (
              <div className="history-list">
                {executionHistory.map((entry) => (
                  <div key={entry.id} className="history-item">
                    <div className="history-item-header">
                      <div className="history-item-title">
                        <strong>{entry.strategy}</strong>
                        <span className="history-symbol">{entry.symbol}</span>
                      </div>
                      <div className="history-item-actions">
                        <button
                          className="load-history-btn"
                          onClick={() => {
                            setSelectedStrategy(entry.strategy);
                            setSymbol(entry.symbol);
                            setCustomSymbol('');
                            setTimeframe(entry.timeframe);
                            setStartDate(entry.startDate);
                            setEndDate(entry.endDate);
                            setStrategyParams(entry.params);
                            setResult(entry.result);
                            setShowHistory(false);
                          }}
                          title="Load this execution"
                        >
                          Load
                        </button>
                        <button
                          className="delete-history-btn"
                          onClick={() => {
                            setExecutionHistory(prev => prev.filter(h => h.id !== entry.id));
                          }}
                          title="Delete"
                        >
                          <MdDelete size={16} />
                        </button>
                      </div>
                    </div>
                    
                    <div className="history-item-details">
                      <div className="history-detail">
                        <span className="detail-label">Signal:</span>
                        <span 
                          className="signal-badge-small"
                          style={{ backgroundColor: getSignalColor(entry.signal) }}
                        >
                          {entry.signal}
                        </span>
                      </div>
                      <div className="history-detail">
                        <span className="detail-label">Timeframe:</span>
                        <span>{TIMEFRAMES.find(tf => tf.value === entry.timeframe)?.label || entry.timeframe}</span>
                      </div>
                      <div className="history-detail">
                        <span className="detail-label">Date Range:</span>
                        <span>{new Date(entry.startDate).toLocaleDateString()} - {new Date(entry.endDate).toLocaleDateString()}</span>
                      </div>
                      <div className="history-detail">
                        <span className="detail-label">Executed:</span>
                        <span>{new Date(entry.timestamp).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      <div className="executor-controls">
        <div className="control-group">
          <label>Strategy</label>
          <select
            value={selectedStrategy}
            onChange={handleStrategyChange}
            className="select-input"
          >
            <option value="">Select Strategy...</option>
            {strategies.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Symbol</label>
          <div className="symbol-input-group">
            <select
              value={symbol}
              onChange={(e) => {
                setSymbol(e.target.value);
                setCustomSymbol("");
              }}
              className="select-input"
              disabled={!!customSymbol}
            >
              <option value="">Select or enter custom...</option>
              {ALL_SYMBOLS.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
            <span className="or-divider">OR</span>
            <input
              type="text"
              value={customSymbol}
              onChange={(e) => {
                setCustomSymbol(e.target.value);
                setSymbol("");
              }}
              placeholder="Enter symbol (e.g., RELIANCE)"
              className="text-input"
              disabled={!!symbol}
            />
          </div>
        </div>

        <div className="control-group">
          <label>Timeframe</label>
          <select
            value={timeframe}
            onChange={(e) => setTimeframe(e.target.value)}
            className="select-input"
          >
            {TIMEFRAMES.map((tf) => (
              <option key={tf.value} value={tf.value}>
                {tf.label}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Start Date</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="date-input"
            max={endDate || new Date().toISOString().split('T')[0]}
          />
        </div>

        <div className="control-group">
          <label>End Date</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="date-input"
            min={startDate}
            max={new Date().toISOString().split('T')[0]}
          />
        </div>
      </div>

      {selectedStrategy && (
        <div className="params-section">
          <h3>Strategy Parameters</h3>
          <div className="params-grid">
            {getStrategyParamFields().map((field) => (
              <div key={field.name} className="param-field">
                <label>
                  {field.label}
                  {field.min !== undefined && field.max !== undefined && (
                    <span className="param-range"> ({field.min} - {field.max})</span>
                  )}
                </label>
                <input
                  type={field.type || "number"}
                  value={strategyParams[field.name] ?? field.default ?? ""}
                  onChange={(e) => handleParamChange(field.name, e.target.value)}
                  step={field.step || 1}
                  min={field.min}
                  max={field.max}
                  className="param-input"
                  placeholder={field.default !== null ? `Default: ${field.default}` : "Optional"}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      <button
        onClick={executeStrategy}
        disabled={loading || !selectedStrategy || (!symbol && !customSymbol) || !startDate || !endDate}
        className="execute-button"
      >
        {loading ? (
          <>
            <div className="spinner-icon"></div>
            Executing...
          </>
        ) : (
          <>
            <MdPlayArrow />
            Execute Strategy
          </>
        )}
      </button>

      {error && (
        <div className="error-message">
          <MdError />
          <span><strong>Error:</strong> {error}</span>
        </div>
      )}

      {result && (
        <div className="result-section">
          <h3>Strategy Results</h3>
          <div className="result-card">
            {/* Top Summary Cards */}
            <div className="result-summary-grid">
              <div className="summary-item">
                <span className="summary-label">Strategy</span>
                <span className="summary-value">{result.strategy || result.indicator}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Symbol</span>
                <span className="summary-value">{result.symbol}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Signal</span>
                <span
                  className="summary-value signal-badge"
                  style={{ backgroundColor: getSignalColor(result.signal) }}
                >
                  {result.signal}
                </span>
              </div>
              {result.value !== null && result.value !== undefined && (
                <div className="summary-item">
                  <span className="summary-label">Indicator Value</span>
                  <span className="summary-value">{result.value.toFixed(4)}</span>
                </div>
              )}
            </div>

            {/* Market Info Grid */}
            <div className="market-info-grid">
              <div className="info-card">
                <div className="info-icon price">
                  <MdAttachMoney />
                </div>
                <div className="info-content">
                  <span className="info-label">Latest Price</span>
                  <span className="info-value">₹{result.latest_price?.toFixed(2)}</span>
                </div>
              </div>
              <div className="info-card">
                <div className="info-icon data">
                  <MdShowChart />
                </div>
                <div className="info-content">
                  <span className="info-label">Data Points</span>
                  <span className="info-value">{result.data_points}</span>
                </div>
              </div>
              <div className="info-card">
                <div className="info-icon time">
                  <MdAccessTime />
                </div>
                <div className="info-content">
                  <span className="info-label">Timestamp</span>
                  <span className="info-value">{new Date(result.timestamp).toLocaleString()}</span>
                </div>
              </div>
            </div>

            {/* Execution Configuration */}
            <div className="config-info-section">
              <h4>Execution Configuration</h4>
              <div className="config-info-grid">
                <div className="config-item">
                  <span className="config-label">Timeframe</span>
                  <span className="config-value">
                    {TIMEFRAMES.find(tf => tf.value === timeframe)?.label || timeframe}
                  </span>
                </div>
                {startDate && (
                  <div className="config-item">
                    <span className="config-label">Start Date</span>
                    <span className="config-value">{new Date(startDate).toLocaleDateString()}</span>
                  </div>
                )}
                {endDate && (
                  <div className="config-item">
                    <span className="config-label">End Date</span>
                    <span className="config-value">{new Date(endDate).toLocaleDateString()}</span>
                  </div>
                )}
                {startDate && endDate && (
                  <div className="config-item">
                    <span className="config-label">Duration</span>
                    <span className="config-value">
                      {Math.ceil((new Date(endDate) - new Date(startDate)) / (1000 * 60 * 60 * 24))} days
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Strategy-Specific Details */}
            {result.data && Object.keys(result.data).length > 0 && (
              <div className="strategy-details-section">
                <h4>Technical Details</h4>
                <div className="details-grid">
                  {/* Current Price */}
                  {result.data.current_price && (
                    <div className="detail-card">
                      <div className="detail-icon"><MdAttachMoney size={18} /></div>
                      <div className="detail-content">
                        <span className="detail-label">Current Price</span>
                        <span className="detail-value">₹{result.data.current_price.toFixed(2)}</span>
                      </div>
                    </div>
                  )}
                  
                  {/* Supertrend specific */}
                  {result.data.supertrend && (
                    <>
                      <div className="detail-card">
                        <div className="detail-icon"><MdTimeline size={18} /></div>
                        <div className="detail-content">
                          <span className="detail-label">Supertrend Line</span>
                          <span className="detail-value">₹{result.data.supertrend.toFixed(2)}</span>
                        </div>
                      </div>
                      <div className="detail-card">
                        <div className="detail-icon"><MdTrendingUp size={18} /></div>
                        <div className="detail-content">
                          <span className="detail-label">Direction</span>
                          <span className="detail-value">{result.data.direction === 1 ? 'Uptrend' : 'Downtrend'}</span>
                        </div>
                      </div>
                    </>
                  )}

                  {/* Bollinger Bands specific */}
                  {result.data.upper_band && (
                    <>
                      <div className="detail-card">
                        <div className="detail-icon"><MdTrendingUp size={18} /></div>
                        <div className="detail-content">
                          <span className="detail-label">Upper Band</span>
                          <span className="detail-value">₹{result.data.upper_band.toFixed(2)}</span>
                        </div>
                      </div>
                      <div className="detail-card">
                        <div className="detail-icon"><MdShowChart size={18} /></div>
                        <div className="detail-content">
                          <span className="detail-label">Middle Band</span>
                          <span className="detail-value">₹{result.data.middle_band.toFixed(2)}</span>
                        </div>
                      </div>
                      <div className="detail-card">
                        <div className="detail-icon"><MdTrendingDown size={18} /></div>
                        <div className="detail-content">
                          <span className="detail-label">Lower Band</span>
                          <span className="detail-value">₹{result.data.lower_band.toFixed(2)}</span>
                        </div>
                      </div>
                    </>
                  )}

                  {/* MACD specific */}
                  {result.data.macd !== undefined && (
                    <>
                      <div className="detail-card">
                        <div className="detail-icon"><MdTimeline size={18} /></div>
                        <div className="detail-content">
                          <span className="detail-label">MACD Line</span>
                          <span className="detail-value">{result.data.macd.toFixed(4)}</span>
                        </div>
                      </div>
                      <div className="detail-card">
                        <div className="detail-icon"><MdShowChart size={18} /></div>
                        <div className="detail-content">
                          <span className="detail-label">Signal Line</span>
                          <span className="detail-value">{result.data.signal.toFixed(4)}</span>
                        </div>
                      </div>
                      <div className="detail-card">
                        <div className="detail-icon"><MdSpeed size={18} /></div>
                        <div className="detail-content">
                          <span className="detail-label">Histogram</span>
                          <span className="detail-value">{result.data.histogram.toFixed(4)}</span>
                        </div>
                      </div>
                    </>
                  )}

                  {/* Strategy parameters */}
                  {result.period && (
                    <div className="detail-card">
                      <div className="detail-icon"><MdAccessTime size={18} /></div>
                      <div className="detail-content">
                        <span className="detail-label">Period</span>
                        <span className="detail-value">{result.period}</span>
                      </div>
                    </div>
                  )}
                  
                  {result.atr_period && (
                    <div className="detail-card">
                      <div className="detail-icon"><MdAccessTime size={18} /></div>
                      <div className="detail-content">
                        <span className="detail-label">ATR Period</span>
                        <span className="detail-value">{result.atr_period}</span>
                      </div>
                    </div>
                  )}
                  
                  {result.multiplier && (
                    <div className="detail-card">
                      <div className="detail-icon"><MdSpeed size={18} /></div>
                      <div className="detail-content">
                        <span className="detail-label">Multiplier</span>
                        <span className="detail-value">{result.multiplier}</span>
                      </div>
                    </div>
                  )}

                  {result.std_dev && (
                    <div className="detail-card">
                      <div className="detail-icon"><MdSpeed size={18} /></div>
                      <div className="detail-content">
                        <span className="detail-label">Std Deviation</span>
                        <span className="detail-value">{result.std_dev}</span>
                      </div>
                    </div>
                  )}

                  {/* New parameters */}
                  {result.threshold && (
                    <div className="detail-card">
                      <div className="detail-icon"><MdSpeed size={18} /></div>
                      <div className="detail-content">
                        <span className="detail-label">Threshold</span>
                        <span className="detail-value">{result.threshold}</span>
                      </div>
                    </div>
                  )}

                  {result.band_width_threshold && (
                    <div className="detail-card">
                      <div className="detail-icon"><MdSpeed size={18} /></div>
                      <div className="detail-content">
                        <span className="detail-label">Band Width Threshold</span>
                        <span className="detail-value">{result.band_width_threshold}</span>
                      </div>
                    </div>
                  )}

                  {result.histogram_threshold && (
                    <div className="detail-card">
                      <div className="detail-icon"><MdSpeed size={18} /></div>
                      <div className="detail-content">
                        <span className="detail-label">Histogram Threshold</span>
                        <span className="detail-value">{result.histogram_threshold}</span>
                      </div>
                    </div>
                  )}

                  {result.oversold && (
                    <div className="detail-card">
                      <div className="detail-icon"><MdTrendingDown size={18} /></div>
                      <div className="detail-content">
                        <span className="detail-label">Oversold Level</span>
                        <span className="detail-value">{result.oversold}</span>
                      </div>
                    </div>
                  )}

                  {result.overbought && (
                    <div className="detail-card">
                      <div className="detail-icon"><MdTrendingUp size={18} /></div>
                      <div className="detail-content">
                        <span className="detail-label">Overbought Level</span>
                        <span className="detail-value">{result.overbought}</span>
                      </div>
                    </div>
                  )}

                  {result.divergence_lookback && (
                    <div className="detail-card">
                      <div className="detail-icon"><MdAccessTime size={18} /></div>
                      <div className="detail-content">
                        <span className="detail-label">Divergence Lookback</span>
                        <span className="detail-value">{result.divergence_lookback}</span>
                      </div>
                    </div>
                  )}

                  {result.confirmation_candles && (
                    <div className="detail-card">
                      <div className="detail-icon"><MdAccessTime size={18} /></div>
                      <div className="detail-content">
                        <span className="detail-label">Confirmation Candles</span>
                        <span className="detail-value">{result.confirmation_candles}</span>
                      </div>
                    </div>
                  )}

                  {result.fast_period && (
                    <div className="detail-card">
                      <div className="detail-icon"><MdSpeed size={18} /></div>
                      <div className="detail-content">
                        <span className="detail-label">Fast Period</span>
                        <span className="detail-value">{result.fast_period}</span>
                      </div>
                    </div>
                  )}

                  {result.slow_period && (
                    <div className="detail-card">
                      <div className="detail-icon"><MdAccessTime size={18} /></div>
                      <div className="detail-content">
                        <span className="detail-label">Slow Period</span>
                        <span className="detail-value">{result.slow_period}</span>
                      </div>
                    </div>
                  )}

                  {result.signal_period && (
                    <div className="detail-card">
                      <div className="detail-icon"><MdTimeline size={18} /></div>
                      <div className="detail-content">
                        <span className="detail-label">Signal Period</span>
                        <span className="detail-value">{result.signal_period}</span>
                      </div>
                    </div>
                  )}

                  {result.long_period && (
                    <div className="detail-card">
                      <div className="detail-icon"><MdAccessTime size={18} /></div>
                      <div className="detail-content">
                        <span className="detail-label">Long Period</span>
                        <span className="detail-value">{result.long_period}</span>
                      </div>
                    </div>
                  )}

                  {result.trend_filter && (
                    <div className="detail-card">
                      <div className="detail-icon"><MdTrendingUp size={18} /></div>
                      <div className="detail-content">
                        <span className="detail-label">Trend Filter</span>
                        <span className="detail-value">{result.trend_filter}</span>
                      </div>
                    </div>
                  )}

                  {result.k_period && (
                    <div className="detail-card">
                      <div className="detail-icon"><MdAccessTime size={18} /></div>
                      <div className="detail-content">
                        <span className="detail-label">%K Period</span>
                        <span className="detail-value">{result.k_period}</span>
                      </div>
                    </div>
                  )}

                  {result.d_period && (
                    <div className="detail-card">
                      <div className="detail-icon"><MdAccessTime size={18} /></div>
                      <div className="detail-content">
                        <span className="detail-label">%D Period</span>
                        <span className="detail-value">{result.d_period}</span>
                      </div>
                    </div>
                  )}

                  {result.smooth_k && (
                    <div className="detail-card">
                      <div className="detail-icon"><MdSpeed size={18} /></div>
                      <div className="detail-content">
                        <span className="detail-label">Smooth %K</span>
                        <span className="detail-value">{result.smooth_k}</span>
                      </div>
                    </div>
                  )}

                  {result.brick_size && (
                    <div className="detail-card">
                      <div className="detail-icon"><MdSpeed size={18} /></div>
                      <div className="detail-content">
                        <span className="detail-label">Brick Size</span>
                        <span className="detail-value">{result.brick_size}</span>
                      </div>
                    </div>
                  )}

                  {result.use_atr !== undefined && (
                    <div className="detail-card">
                      <div className="detail-icon"><MdSpeed size={18} /></div>
                      <div className="detail-content">
                        <span className="detail-label">Use ATR</span>
                        <span className="detail-value">{result.use_atr ? 'Yes' : 'No'}</span>
                      </div>
                    </div>
                  )}

                  {result.reversal_bricks && (
                    <div className="detail-card">
                      <div className="detail-icon"><MdSpeed size={18} /></div>
                      <div className="detail-content">
                        <span className="detail-label">Reversal Bricks</span>
                        <span className="detail-value">{result.reversal_bricks}</span>
                      </div>
                    </div>
                  )}

                  {result.lookback && (
                    <div className="detail-card">
                      <div className="detail-icon"><MdAccessTime size={18} /></div>
                      <div className="detail-content">
                        <span className="detail-label">Lookback</span>
                        <span className="detail-value">{result.lookback}</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Data Table */}
            {result.data && (
              <div className="data-section">
                <h4>Indicator Data Values</h4>
                <div className="data-table-container">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Value</th>
                        <th>Index</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(result.data).map(([key, values]) => {
                        const dataArray = Array.isArray(values) ? values : [values];
                        return dataArray.slice(0, 20).map((value, idx) => (
                          <tr key={`${key}-${idx}`}>
                            <td>{idx + 1}</td>
                            <td className="value-cell">
                              {typeof value === 'number' ? value.toFixed(6) : value}
                            </td>
                            <td>{key}</td>
                          </tr>
                        ));
                      }).flat()}
                    </tbody>
                  </table>
                  {Object.values(result.data).some(arr => Array.isArray(arr) && arr.length > 20) && (
                    <div className="table-info">
                      Showing first 20 values. Total data points: {result.data_points}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}


