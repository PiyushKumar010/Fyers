import { useState, useEffect } from "react";
import { MdHistory, MdRefresh, MdAccountBalance, MdTrendingUp, MdMonetizationOn, MdShowChart, MdCreditCard, MdAttachMoney, MdPercent } from "react-icons/md";
import "./TradingHistory.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function TradingHistory() {
  const [history, setHistory] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [sessionDetails, setSessionDetails] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState("list"); // 'list' or 'details'

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/automated-trading/history?limit=100`);
      const data = await response.json();
      setHistory(data.history || []);
    } catch (err) {
      setError("Failed to fetch trading history");
      console.error("Error fetching history:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSessionDetails = async (sessionId) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/automated-trading/history/${sessionId}`);
      const data = await response.json();
      setSessionDetails(data);
      setSelectedSession(sessionId);
      setViewMode("details");
    } catch (err) {
      setError("Failed to fetch session details");
      console.error("Error fetching session details:", err);
    } finally {
      setLoading(false);
    }
  };

  const backToList = () => {
    setViewMode("list");
    setSelectedSession(null);
    setSessionDetails(null);
  };

  const formatCurrency = (value) => {
    if (value === null || value === undefined) return "₹0";
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (value) => {
    if (value === null || value === undefined) return "0%";
    return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    
    // Format with proper zero-padding for minutes
    const day = date.getDate();
    const month = date.toLocaleString("en-IN", { month: "short" });
    const year = date.getFullYear();
    let hours = date.getHours();
    const minutes = date.getMinutes();
    const ampm = hours >= 12 ? "PM" : "AM";
    
    // Convert to 12-hour format
    hours = hours % 12;
    hours = hours ? hours : 12; // 0 should be 12
    
    // Zero-pad minutes
    const minutesStr = minutes < 10 ? `0${minutes}` : minutes;
    
    return `${month} ${day}, ${year}, ${hours}:${minutesStr} ${ampm}`;
  };

  const deleteSession = async (sessionId) => {
    if (!confirm("Are you sure you want to delete this trading session? This action cannot be undone.")) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/automated-trading/session/${sessionId}`, {
        method: "DELETE",
      });

      if (response.ok) {
        // Remove from local state
        setHistory(history.filter(s => s.session_id !== sessionId));
        // Show success message
        setError(null);
      } else {
        setError("Failed to delete session");
      }
    } catch (err) {
      setError("Failed to delete session");
      console.error("Error deleting session:", err);
    }
  };

  const getStatusBadgeClass = (status) => {
    switch (status?.toUpperCase()) {
      case "COMPLETED":
        return "status-badge status-completed";
      case "RUNNING":
        return "status-badge status-running";
      case "ERROR":
        return "status-badge status-error";
      case "STOPPED":
        return "status-badge status-stopped";
      default:
        return "status-badge";
    }
  };

  return (
    <div className="trading-history-container">
      <div className="page-header">
        <h1>
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 20h9"></path>
            <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
          </svg>
          Trading History
        </h1>
        <p className="subtitle">View all your automated trading sessions and results</p>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {viewMode === "list" ? (
        <div className="history-content">
          <div className="history-header">
            <h2>All Sessions ({history.length})</h2>
            <button onClick={fetchHistory} className="refresh-button" disabled={loading}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"></path>
              </svg>
              {loading ? "Loading..." : "Refresh"}
            </button>
          </div>

          {loading && history.length === 0 ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Loading trading history...</p>
            </div>
          ) : history.length === 0 ? (
            <div className="empty-state">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="16" y1="2" x2="16" y2="6"></line>
                <line x1="8" y1="2" x2="8" y2="6"></line>
                <line x1="3" y1="10" x2="21" y2="10"></line>
              </svg>
              <h3>No Trading History</h3>
              <p>Start your first automated trading session to see results here</p>
            </div>
          ) : (
            <div className="history-grid">
              {history.map((session) => (
                <div key={session.session_id} className="session-card">
                  <div className="session-card-header">
                    <div className="session-info">
                      <h3>{session.symbols?.join(", ") || "N/A"}</h3>
                      <span className={getStatusBadgeClass(session.status)}>
                        {session.status || "UNKNOWN"}
                      </span>
                    </div>
                    <div className="session-actions">
                      <button
                        onClick={() => fetchSessionDetails(session.session_id)}
                        className="view-details-btn"
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                          <circle cx="12" cy="12" r="3"></circle>
                        </svg>
                        View Details
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteSession(session.session_id);
                        }}
                        className="delete-btn"
                        title="Delete this session"
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <polyline points="3 6 5 6 21 6"></polyline>
                          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                          <line x1="10" y1="11" x2="10" y2="17"></line>
                          <line x1="14" y1="11" x2="14" y2="17"></line>
                        </svg>
                      </button>
                    </div>
                  </div>

                  <div className="session-meta">
                    <div className="meta-item">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                        <line x1="16" y1="2" x2="16" y2="6"></line>
                        <line x1="8" y1="2" x2="8" y2="6"></line>
                        <line x1="3" y1="10" x2="21" y2="10"></line>
                      </svg>
                      <span>{formatDate(session.created_at)}</span>
                    </div>
                    <div className="meta-item">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <polyline points="12 6 12 12 16 14"></polyline>
                      </svg>
                      <span>{session.mode || "N/A"}</span>
                    </div>
                  </div>

                  <div className="strategies-tags">
                    {session.strategies?.map((strategy) => (
                      <span key={strategy} className="strategy-tag">
                        {strategy}
                      </span>
                    ))}
                  </div>

                  <div className="session-stats">
                    <div className="stat-item">
                      <span className="stat-label"><MdAccountBalance className="stat-icon" /> Initial Capital</span>
                      <span className="stat-value">{formatCurrency(session.initial_capital)}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label" title="SINGLE SOURCE OF TRUTH: Initial + Realized + Unrealized - Charges"><MdTrendingUp className="stat-icon" /> Final Value</span>
                      <span className="stat-value">{formatCurrency(session.final_value || session.final_capital)}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label" title="Money locked in from closed trades"><MdMonetizationOn className="stat-icon" /> Realized P&L</span>
                      <span className={`stat-value ${(session.realized_pnl || 0) >= 0 ? "positive" : "negative"}`}>
                        {formatCurrency(session.realized_pnl || 0)}
                      </span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label" title="Paper gains/losses from open positions"><MdShowChart className="stat-icon" /> Unrealized P&L</span>
                      <span className={`stat-value ${(session.unrealized_pnl || 0) >= 0 ? "positive" : "negative"}`}>
                        {formatCurrency(session.unrealized_pnl || 0)}
                      </span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label" title="Brokerage + fees + slippage"><MdCreditCard className="stat-icon" /> Charges</span>
                      <span className="stat-value negative">{formatCurrency(session.total_charges || 0)}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label" title="DERIVED: Final Value - Initial Capital"><MdAttachMoney className="stat-icon" /> Total P&L</span>
                      <span className={`stat-value ${session.total_pnl >= 0 ? "positive" : "negative"}`}>
                        {formatCurrency(session.total_pnl)}
                      </span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label" title="DERIVED: (Final Value - Initial) / Initial × 100"><MdPercent className="stat-icon" /> Returns %</span>
                      <span className={`stat-value ${session.returns_percent >= 0 ? "positive" : "negative"}`}>
                        {formatPercent(session.returns_percent)}
                      </span>
                    </div>
                  </div>

                  {session.total_trades !== undefined && (
                    <div className="session-footer">
                      <span title="Completed round-trip trades (BUY→SELL)">Trades Executed: {session.total_trades || 0}</span>
                      <span>Win Rate: {session.win_rate?.toFixed(1) || 0}%</span>
                      <span title="Strategy signals generated (not all become trades)">Signals Generated: {session.total_signals_generated || session.total_signals || 0}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="details-content">
          <div className="details-header">
            <button onClick={backToList} className="back-button">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="19" y1="12" x2="5" y2="12"></line>
                <polyline points="12 19 5 12 12 5"></polyline>
              </svg>
              Back to List
            </button>
            <h2>Session Details</h2>
          </div>

          {loading ? (
            <div className="loading-state">
              <div className="spinner"></div>
              <p>Loading session details...</p>
            </div>
          ) : sessionDetails ? (
            <>
              <div className="details-grid">
                {/* Session Configuration */}
                <div className="detail-card">
                  <h3>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="3"></circle>
                      <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"></path>
                    </svg>
                    Configuration
                  </h3>
                  <div className="config-details">
                    <div className="config-row">
                      <span className="label">Session ID:</span>
                      <span className="value">{sessionDetails.session?.session_id || selectedSession}</span>
                    </div>
                    <div className="config-row">
                      <span className="label">Symbols:</span>
                      <span className="value">{sessionDetails.results?.symbols?.join(", ") || sessionDetails.session?.symbols?.join(", ") || "N/A"}</span>
                    </div>
                    <div className="config-row">
                      <span className="label">Strategies:</span>
                      <div className="strategies-list">
                        {(sessionDetails.results?.strategies || sessionDetails.session?.strategies || []).map((s) => (
                          <span key={s} className="strategy-badge">{s}</span>
                        ))}
                      </div>
                    </div>
                    <div className="config-row">
                      <span className="label">Mode:</span>
                      <span className="value">{sessionDetails.results?.mode || sessionDetails.session?.mode || "N/A"}</span>
                    </div>
                    <div className="config-row">
                      <span className="label">Date Range:</span>
                      <span className="value">
                        {sessionDetails.results?.start_date || sessionDetails.session?.start_date || "N/A"} to {sessionDetails.results?.end_date || sessionDetails.session?.end_date || "N/A"}
                      </span>
                    </div>
                    <div className="config-row">
                      <span className="label">Stop Loss:</span>
                      <span className="value">{sessionDetails.results?.stop_loss_percent || sessionDetails.session?.stop_loss_percent || "N/A"}%</span>
                    </div>
                    <div className="config-row">
                      <span className="label">Profit Target:</span>
                      <span className="value">{sessionDetails.results?.profit_target_percent || sessionDetails.session?.profit_target_percent || "N/A"}%</span>
                    </div>
                    <div className="config-row">
                      <span className="label">Initial Capital:</span>
                      <span className="value">{formatCurrency(sessionDetails.results?.initial_capital || sessionDetails.session?.initial_capital || 0)}</span>
                    </div>
                    <div className="config-row">
                      <span className="label">Max Positions:</span>
                      <span className="value">{sessionDetails.results?.max_positions || sessionDetails.session?.max_positions || "N/A"}</span>
                    </div>
                    <div className="config-row">
                      <span className="label">Position Size:</span>
                      <span className="value">{sessionDetails.results?.position_size_percent || sessionDetails.session?.position_size_percent || "N/A"}%</span>
                    </div>
                    <div className="config-row">
                      <span className="label">Timeframe:</span>
                      <span className="value">{sessionDetails.results?.timeframe || sessionDetails.session?.timeframe || "N/A"}</span>
                    </div>
                    <div className="config-row">
                      <span className="label">Status:</span>
                      <span className={getStatusBadgeClass(sessionDetails.session?.status || "COMPLETED")}>
                        {sessionDetails.session?.status || "COMPLETED"}
                      </span>
                    </div>
                    <div className="config-row">
                      <span className="label">Created:</span>
                      <span className="value">{formatDate(sessionDetails.results?.created_at || sessionDetails.session?.created_at)}</span>
                    </div>
                    {(sessionDetails.results?.completed_at || sessionDetails.session?.completed_at) && (
                      <div className="config-row">
                        <span className="label">Completed:</span>
                        <span className="value">{formatDate(sessionDetails.results?.completed_at || sessionDetails.session?.completed_at)}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Results Summary */}
                {sessionDetails.results && (
                  <div className="detail-card">
                    <h3>
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="12" y1="1" x2="12" y2="23"></line>
                        <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path>
                      </svg>
                      Performance Summary
                    </h3>
                    <div className="results-summary">
                      {/* Accounting Identity Banner */}
                      <div className="accounting-identity">
                        <div className="identity-formula">
                          Final Value = Initial Capital + Realized P&L + Unrealized P&L - Charges
                        </div>
                        <div className="identity-note">
                          All values below are derived from this single source of truth
                        </div>
                      </div>
                      
                      {/* Capital Breakdown */}
                      <div className="section-divider">CAPITAL BREAKDOWN</div>
                      <div className="results-row">
                        <div className="result-metric">
                          <span className="metric-label">Initial Capital</span>
                          <span className="metric-value">{formatCurrency(sessionDetails.session.initial_capital)}</span>
                        </div>
                        <div className="result-metric">
                          <span className="metric-label">Current Cash<br/>(Reference)</span>
                          <span className="metric-value">{formatCurrency(sessionDetails.results.current_capital)}</span>
                        </div>
                      </div>
                      <div className="results-row">
                        <div className="result-metric">
                          <span className="metric-label">Invested Capital<br/>(Reference)</span>
                          <span className="metric-value">{formatCurrency(sessionDetails.results.invested_capital)}</span>
                        </div>
                        <div className="result-metric highlight">
                          <span className="metric-label" title="SINGLE SOURCE OF TRUTH: Initial + Realized + Unrealized - Charges"><MdTrendingUp className="stat-icon" /> Final Portfolio Value</span>
                          <span className="metric-value">{formatCurrency(sessionDetails.results.final_value)}</span>
                        </div>
                      </div>
                      
                      {/* P&L Components */}
                      <div className="section-divider">P&L COMPONENTS</div>
                      <div className="results-row">
                        <div className="result-metric">
                          <span className="metric-label" title="Money locked in from closed trades"><MdMonetizationOn className="stat-icon" /> Realized P&L</span>
                          <span className={`metric-value ${sessionDetails.results.realized_pnl >= 0 ? "positive" : "negative"}`}>
                            {formatCurrency(sessionDetails.results.realized_pnl)}
                          </span>
                        </div>
                        <div className="result-metric">
                          <span className="metric-label" title="Paper gains/losses from open positions"><MdShowChart className="stat-icon" /> Unrealized P&L</span>
                          <span className={`metric-value ${sessionDetails.results.unrealized_pnl >= 0 ? "positive" : "negative"}`}>
                            {formatCurrency(sessionDetails.results.unrealized_pnl)}
                          </span>
                        </div>
                      </div>
                      <div className="results-row">
                        <div className="result-metric">
                          <span className="metric-label" title="Brokerage + fees + slippage"><MdCreditCard className="stat-icon" /> Total Charges</span>
                          <span className="metric-value negative">
                            {formatCurrency(sessionDetails.results.total_charges || 0)}
                          </span>
                        </div>
                        <div className="result-metric highlight">
                          <span className="metric-label" title="DERIVED: Final Value - Initial Capital">Total P&L</span>
                          <span className={`metric-value ${sessionDetails.results.total_pnl >= 0 ? "positive" : "negative"}`}>
                            {formatCurrency(sessionDetails.results.total_pnl)}
                          </span>
                        </div>
                      </div>
                      
                      {/* Returns */}
                      <div className="results-row">
                        <div className="result-metric highlight">
                          <span className="metric-label" title="DERIVED: (Final Value - Initial) / Initial × 100">Returns %</span>
                          <span className={`metric-value ${sessionDetails.results.returns_percent >= 0 ? "positive" : "negative"}`}>
                            {formatPercent(sessionDetails.results.returns_percent)}
                          </span>
                        </div>
                      </div>
                      
                      {/* Trade Statistics */}
                      <div className="section-divider">TRADE STATISTICS</div>
                      <div className="results-row">
                        <div className="result-metric">
                          <span className="metric-label">Winning Trades</span>
                          <span className="metric-value positive">{sessionDetails.results.winning_trades}</span>
                        </div>
                        <div className="result-metric">
                          <span className="metric-label">Losing Trades</span>
                          <span className="metric-value negative">{sessionDetails.results.losing_trades}</span>
                        </div>
                      </div>
                      <div className="results-row">
                        <div className="result-metric">
                          <span className="metric-label">Win Rate</span>
                          <span className="metric-value">{sessionDetails.results.win_rate?.toFixed(2)}%</span>
                        </div>
                        <div className="result-metric">
                          <span className="metric-label">Profit Factor</span>
                          <span className="metric-value">{sessionDetails.results.profit_factor?.toFixed(2) || "0.00"}</span>
                        </div>
                      </div>
                      <div className="results-row">
                        <div className="result-metric">
                          <span className="metric-label">Average Win</span>
                          <span className="metric-value positive">{formatCurrency(sessionDetails.results.avg_win || 0)}</span>
                        </div>
                        <div className="result-metric">
                          <span className="metric-label">Average Loss</span>
                          <span className="metric-value negative">{formatCurrency(sessionDetails.results.avg_loss || 0)}</span>
                        </div>
                      </div>
                      
                      {/* Other Metrics */}
                      <div className="section-divider">OTHER METRICS</div>
                      <div className="results-row">
                        <div className="result-metric">
                          <span className="metric-label" title="Strategy signals generated - NOT all become trades">Signals Generated</span>
                          <span className="metric-value">{sessionDetails.results.total_signals_generated || sessionDetails.results.total_signals || 0}</span>
                        </div>
                        <div className="result-metric">
                          <span className="metric-label">Open Positions</span>
                          <span className="metric-value">{sessionDetails.results.open_positions_count || 0}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Trades Table */}
              {sessionDetails.trades && sessionDetails.trades.length > 0 && (
                <div className="detail-card trades-card">
                  <h3>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="8" y1="6" x2="21" y2="6"></line>
                      <line x1="8" y1="12" x2="21" y2="12"></line>
                      <line x1="8" y1="18" x2="21" y2="18"></line>
                      <line x1="3" y1="6" x2="3.01" y2="6"></line>
                      <line x1="3" y1="12" x2="3.01" y2="12"></line>
                      <line x1="3" y1="18" x2="3.01" y2="18"></line>
                    </svg>
                    Executed Trades ({sessionDetails.total_trades})
                  </h3>
                  <div className="trades-table-wrapper">
                    <table className="trades-table">
                      <thead>
                        <tr>
                          <th>Symbol</th>
                          <th>Strategy</th>
                          <th>Side</th>
                          <th>Quantity</th>
                          <th>Entry Price</th>
                          <th>Exit Price</th>
                          <th>P&L</th>
                          <th>Timestamp</th>
                        </tr>
                      </thead>
                      <tbody>
                        {sessionDetails.trades.map((trade, idx) => (
                          <tr key={idx}>
                            <td className="symbol-cell">{trade.symbol}</td>
                            <td>{trade.strategy}</td>
                            <td className={trade.entry_side === "LONG" ? "buy" : "sell"}>{trade.entry_side}</td>
                            <td>{trade.quantity}</td>
                            <td>{formatCurrency(trade.entry_price)}</td>
                            <td>{trade.exit_price ? formatCurrency(trade.exit_price) : "-"}</td>
                            <td className={trade.net_pnl >= 0 ? "positive" : "negative"}>
                              {trade.net_pnl !== null && trade.net_pnl !== undefined ? formatCurrency(trade.net_pnl) : "-"}
                            </td>
                            <td className="timestamp-cell">{formatDate(trade.entry_timestamp)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="empty-state">
              <p>No details available</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
