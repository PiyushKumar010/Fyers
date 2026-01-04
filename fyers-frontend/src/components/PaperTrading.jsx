import { useState, useEffect } from "react";
import "./PaperTrading.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const POPULAR_SYMBOLS = [
  { value: "NSE:RELIANCE-EQ", label: "RELIANCE" },
  { value: "NSE:TCS-EQ", label: "TCS" },
  { value: "NSE:SBIN-EQ", label: "SBIN" },
  { value: "NSE:INFY-EQ", label: "INFY" },
  { value: "NSE:HDFCBANK-EQ", label: "HDFC Bank" },
  { value: "NSE:ICICIBANK-EQ", label: "ICICI Bank" },
  { value: "NSE:TATAMOTORS-EQ", label: "Tata Motors" },
  { value: "NSE:ITC-EQ", label: "ITC" },
];

export default function PaperTrading() {
  const [portfolio, setPortfolio] = useState(null);
  const [positions, setPositions] = useState([]);
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [showAddCapital, setShowAddCapital] = useState(false);
  const [capitalAmount, setCapitalAmount] = useState("");

  // Order form state
  const [orderForm, setOrderForm] = useState({
    symbol: "NSE:RELIANCE-EQ",
    side: "BUY",
    quantity: 1,
    price: "",
    stopLoss: "",
    target: "",
  });

  // Fetch portfolio data
  const fetchPortfolio = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/paper-trading/portfolio`);
      const data = await response.json();
      setPortfolio(data);
    } catch (err) {
      console.error("Failed to fetch portfolio:", err);
    }
  };

  // Fetch positions
  const fetchPositions = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/paper-trading/positions`);
      const data = await response.json();
      setPositions(data.positions || []);
    } catch (err) {
      console.error("Failed to fetch positions:", err);
    }
  };

  // Fetch trade history
  const fetchTrades = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/paper-trading/trades`);
      const data = await response.json();
      setTrades(data.trades || []);
    } catch (err) {
      console.error("Failed to fetch trades:", err);
    }
  };

  // Place order
  const placeOrder = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const orderData = {
        symbol: orderForm.symbol,
        side: orderForm.side,
        quantity: parseInt(orderForm.quantity),
        price: parseFloat(orderForm.price),
      };

      if (orderForm.stopLoss) {
        orderData.stop_loss = parseFloat(orderForm.stopLoss);
      }
      if (orderForm.target) {
        orderData.target = parseFloat(orderForm.target);
      }

      const response = await fetch(`${API_BASE_URL}/api/paper-trading/order`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(orderData),
      });

      const result = await response.json();

      if (response.ok && result.status === "EXECUTED") {
        setSuccess(`✅ Order ${result.side} executed successfully! Trade ID: ${result.trade_id}`);
        // Reset form
        setOrderForm({
          ...orderForm,
          price: "",
          stopLoss: "",
          target: "",
        });
        // Refresh data
        fetchPortfolio();
        fetchPositions();
        fetchTrades();
      } else {
        setError(`❌ Order rejected: ${result.message || "Unknown error"}`);
      }
    } catch (err) {
      setError(`❌ Failed to place order: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Add capital
  const addCapital = async (e) => {
    e.preventDefault();
    const amount = parseFloat(capitalAmount);
    
    if (!amount || amount <= 0) {
      setError("❌ Please enter a valid positive amount");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/paper-trading/add-capital?amount=${amount}`,
        { method: "POST" }
      );

      const result = await response.json();

      if (response.ok) {
        setSuccess(`✅ Added ${formatCurrency(amount)} to your capital!`);
        setCapitalAmount("");
        setShowAddCapital(false);
        fetchPortfolio();
      } else {
        setError(`❌ Failed to add capital: ${result.detail || "Unknown error"}`);
      }
    } catch (err) {
      setError(`❌ Failed to add capital: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Reset portfolio
  const resetPortfolio = async () => {
    if (!confirm("Are you sure you want to reset the portfolio? This will clear all positions and trades and reset to ₹1,00,000.")) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/paper-trading/reset`, {
        method: "POST",
      });

      if (response.ok) {
        setSuccess("✅ Portfolio reset successfully!");
        fetchPortfolio();
        fetchPositions();
        fetchTrades();
      } else {
        setError("❌ Failed to reset portfolio");
      }
    } catch (err) {
      setError(`❌ Failed to reset portfolio: ${err.message}`);
    }
  };

  useEffect(() => {
    fetchPortfolio();
    fetchPositions();
    fetchTrades();

    // Auto-refresh every 10 seconds
    const interval = setInterval(() => {
      fetchPortfolio();
      fetchPositions();
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 2,
    }).format(value);
  };

  const formatPercent = (value) => {
    return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
  };

  return (
    <div className="paper-trading">
      <div className="paper-trading-header">
        <div className="header-content">
          <h1>💼 Paper Trading Dashboard</h1>
          <p className="subtitle">Practice trading without real money</p>
        </div>
        <div className="header-actions">
          <button onClick={() => setShowAddCapital(!showAddCapital)} className="add-capital-button">
            💰 Add Capital
          </button>
          <button onClick={resetPortfolio} className="reset-button">
            🔄 Reset Portfolio
          </button>
        </div>
      </div>

      {/* Add Capital Modal */}
      {showAddCapital && (
        <div className="add-capital-modal">
          <div className="modal-content">
            <div className="modal-header">
              <h3>💰 Add Capital</h3>
              <button onClick={() => setShowAddCapital(false)} className="close-button">✕</button>
            </div>
            <form onSubmit={addCapital} className="capital-form">
              <p className="modal-description">
                Add more funds to your paper trading account. Current balance: <strong>{portfolio ? formatCurrency(portfolio.available_capital) : "Loading..."}</strong>
              </p>
              <div className="quick-amounts">
                <button type="button" onClick={() => setCapitalAmount("10000")} className="quick-amount">
                  +₹10,000
                </button>
                <button type="button" onClick={() => setCapitalAmount("50000")} className="quick-amount">
                  +₹50,000
                </button>
                <button type="button" onClick={() => setCapitalAmount("100000")} className="quick-amount">
                  +₹1,00,000
                </button>
              </div>
              <div className="form-group">
                <label>Custom Amount (₹)</label>
                <input
                  type="number"
                  step="100"
                  min="100"
                  value={capitalAmount}
                  onChange={(e) => setCapitalAmount(e.target.value)}
                  className="form-control"
                  placeholder="Enter amount"
                  required
                />
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowAddCapital(false)} className="cancel-button">
                  Cancel
                </button>
                <button type="submit" className="submit-capital-button" disabled={loading}>
                  {loading ? "Adding..." : "Add Capital"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Portfolio Summary */}
      {portfolio && (
        <div className="portfolio-summary">
          <div className="summary-card">
            <div className="card-icon">💰</div>
            <div className="card-content">
              <div className="card-label">Available Capital</div>
              <div className="card-value">{formatCurrency(portfolio.available_capital)}</div>
            </div>
          </div>
          <div className="summary-card">
            <div className="card-icon">📊</div>
            <div className="card-content">
              <div className="card-label">Portfolio Value</div>
              <div className="card-value">{formatCurrency(portfolio.portfolio_value)}</div>
            </div>
          </div>
          <div className="summary-card">
            <div className="card-icon">💼</div>
            <div className="card-content">
              <div className="card-label">Open Positions</div>
              <div className="card-value">{portfolio.open_positions}</div>
            </div>
          </div>
          <div className="summary-card">
            <div className={`card-icon ${portfolio.total_pnl >= 0 ? "profit" : "loss"}`}>
              {portfolio.total_pnl >= 0 ? "📈" : "📉"}
            </div>
            <div className="card-content">
              <div className="card-label">Total P&L</div>
              <div className={`card-value ${portfolio.total_pnl >= 0 ? "profit" : "loss"}`}>
                {formatCurrency(portfolio.total_pnl)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Alerts */}
      {error && (
        <div className="alert alert-error">
          {error}
          <button onClick={() => setError(null)}>✕</button>
        </div>
      )}
      {success && (
        <div className="alert alert-success">
          {success}
          <button onClick={() => setSuccess(null)}>✕</button>
        </div>
      )}

      <div className="trading-content">
        {/* Order Form */}
        <div className="order-section">
          <h2>📝 Place Order</h2>
          <form onSubmit={placeOrder} className="order-form">
            <div className="form-group">
              <label>Symbol</label>
              <select
                value={orderForm.symbol}
                onChange={(e) => setOrderForm({ ...orderForm, symbol: e.target.value })}
                className="form-control"
                required
              >
                {POPULAR_SYMBOLS.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Side</label>
                <select
                  value={orderForm.side}
                  onChange={(e) => setOrderForm({ ...orderForm, side: e.target.value })}
                  className="form-control"
                  required
                >
                  <option value="BUY">BUY</option>
                  <option value="SELL">SELL</option>
                </select>
              </div>

              <div className="form-group">
                <label>Quantity</label>
                <input
                  type="number"
                  min="1"
                  value={orderForm.quantity}
                  onChange={(e) => setOrderForm({ ...orderForm, quantity: e.target.value })}
                  className="form-control"
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label>Price (₹)</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={orderForm.price}
                onChange={(e) => setOrderForm({ ...orderForm, price: e.target.value })}
                className="form-control"
                placeholder="Enter execution price"
                required
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Stop Loss (₹) - Optional</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={orderForm.stopLoss}
                  onChange={(e) => setOrderForm({ ...orderForm, stopLoss: e.target.value })}
                  className="form-control"
                  placeholder="Auto-exit price"
                />
              </div>

              <div className="form-group">
                <label>Target (₹) - Optional</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={orderForm.target}
                  onChange={(e) => setOrderForm({ ...orderForm, target: e.target.value })}
                  className="form-control"
                  placeholder="Target price"
                />
              </div>
            </div>

            <button
              type="submit"
              className={`submit-button ${orderForm.side.toLowerCase()}`}
              disabled={loading}
            >
              {loading ? "Placing Order..." : `${orderForm.side} ${orderForm.symbol.split(":")[1]}`}
            </button>
          </form>
        </div>

        {/* Open Positions */}
        <div className="positions-section">
          <h2>📍 Open Positions</h2>
          {positions.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📭</div>
              <p>No open positions</p>
              <p className="empty-hint">Place a BUY order to open a position</p>
            </div>
          ) : (
            <div className="positions-list">
              {positions.map((position) => (
                <div key={position.symbol} className="position-card">
                  <div className="position-header">
                    <h3>{position.symbol.split(":")[1].replace("-EQ", "")}</h3>
                    <span className={`badge ${position.unrealized_pnl >= 0 ? "profit" : "loss"}`}>
                      {formatCurrency(position.unrealized_pnl)}
                    </span>
                  </div>
                  <div className="position-details">
                    <div className="detail-row">
                      <span className="label">Quantity:</span>
                      <span className="value">{position.quantity}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">Entry Price:</span>
                      <span className="value">{formatCurrency(position.entry_price)}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">Current Price:</span>
                      <span className="value">{formatCurrency(position.current_price)}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">Return:</span>
                      <span className={`value ${position.return_pct >= 0 ? "profit" : "loss"}`}>
                        {formatPercent(position.return_pct)}
                      </span>
                    </div>
                    {position.stop_loss && (
                      <div className="detail-row">
                        <span className="label">Stop Loss:</span>
                        <span className="value stop-loss">{formatCurrency(position.stop_loss)}</span>
                      </div>
                    )}
                    {position.target && (
                      <div className="detail-row">
                        <span className="label">Target:</span>
                        <span className="value target">{formatCurrency(position.target)}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Trade History */}
      <div className="trades-section">
        <h2>📜 Trade History</h2>
        {trades.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📋</div>
            <p>No trades yet</p>
            <p className="empty-hint">Your executed trades will appear here</p>
          </div>
        ) : (
          <div className="trades-table-wrapper">
            <table className="trades-table">
              <thead>
                <tr>
                  <th>Trade ID</th>
                  <th>Symbol</th>
                  <th>Side</th>
                  <th>Quantity</th>
                  <th>Price</th>
                  <th>P&L</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {trades.slice().reverse().map((trade) => (
                  <tr key={trade.trade_id}>
                    <td>
                      <code>{trade.trade_id.slice(0, 8)}</code>
                    </td>
                    <td>
                      <strong>{trade.symbol.split(":")[1].replace("-EQ", "")}</strong>
                    </td>
                    <td>
                      <span className={`badge ${trade.side.toLowerCase()}`}>{trade.side}</span>
                    </td>
                    <td>{trade.quantity}</td>
                    <td>{formatCurrency(trade.price)}</td>
                    <td
                      className={
                        trade.realized_pnl
                          ? trade.realized_pnl >= 0
                            ? "profit"
                            : "loss"
                          : ""
                      }
                    >
                      {trade.realized_pnl ? formatCurrency(trade.realized_pnl) : "-"}
                    </td>
                    <td>{new Date(trade.timestamp).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
