import { useState, useEffect } from "react";
import { getPositions, getHoldings } from "../api/fyersApi";
import "./PositionsHoldings.css";

export default function PositionsHoldings() {
  const [activeTab, setActiveTab] = useState("positions");
  const [positions, setPositions] = useState([]);
  const [holdings, setHoldings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchPositions = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getPositions();
      setPositions(response.positions || []);
    } catch (err) {
      setError(err.message || "Failed to fetch positions");
      setPositions([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchHoldings = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getHoldings();
      setHoldings(response.holdings || []);
    } catch (err) {
      setError(err.message || "Failed to fetch holdings");
      setHoldings([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "positions") {
      fetchPositions();
      const interval = setInterval(fetchPositions, 10000);
      return () => clearInterval(interval);
    } else {
      fetchHoldings();
      const interval = setInterval(fetchHoldings, 10000);
      return () => clearInterval(interval);
    }
  }, [activeTab]);

  const totalPnl = positions.reduce((sum, pos) => sum + (pos.pnl || 0), 0);
  const totalHoldingsPnl = holdings.reduce((sum, h) => sum + (h.pnl || 0), 0);

  return (
    <div className="positions-holdings">
      <div className="tabs">
        <button
          className={`tab ${activeTab === "positions" ? "active" : ""}`}
          onClick={() => setActiveTab("positions")}
        >
          Positions ({positions.length})
        </button>
        <button
          className={`tab ${activeTab === "holdings" ? "active" : ""}`}
          onClick={() => setActiveTab("holdings")}
        >
          Holdings ({holdings.length})
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {activeTab === "positions" && (
        <div className="tab-content">
          <div className="summary">
            <div className="summary-item">
              <span className="label">Total P&L:</span>
              <span className={`value ${totalPnl >= 0 ? "positive" : "negative"}`}>
                ₹{totalPnl.toFixed(2)}
              </span>
            </div>
          </div>

          {loading && positions.length === 0 ? (
            <div className="loading">Loading positions...</div>
          ) : positions.length === 0 ? (
            <div className="empty-state">No open positions</div>
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>Side</th>
                    <th>Qty</th>
                    <th>Avg Price</th>
                    <th>LTP</th>
                    <th>P&L</th>
                    <th>Product</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.map((pos, idx) => (
                    <tr key={idx}>
                      <td>{pos.symbol}</td>
                      <td className={pos.side === 1 ? "buy" : "sell"}>
                        {pos.side === 1 ? "LONG" : "SHORT"}
                      </td>
                      <td>{pos.qty}</td>
                      <td>₹{pos.avgPrice?.toFixed(2) || "0.00"}</td>
                      <td>₹{pos.ltp?.toFixed(2) || "0.00"}</td>
                      <td className={pos.pnl >= 0 ? "positive" : "negative"}>
                        ₹{pos.pnl?.toFixed(2) || "0.00"}
                      </td>
                      <td>{pos.productType}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeTab === "holdings" && (
        <div className="tab-content">
          <div className="summary">
            <div className="summary-item">
              <span className="label">Total P&L:</span>
              <span className={`value ${totalHoldingsPnl >= 0 ? "positive" : "negative"}`}>
                ₹{totalHoldingsPnl.toFixed(2)}
              </span>
            </div>
          </div>

          {loading && holdings.length === 0 ? (
            <div className="loading">Loading holdings...</div>
          ) : holdings.length === 0 ? (
            <div className="empty-state">No holdings</div>
          ) : (
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Symbol</th>
                    <th>Quantity</th>
                    <th>Avg Price</th>
                    <th>LTP</th>
                    <th>Invested</th>
                    <th>Current Value</th>
                    <th>P&L</th>
                    <th>P&L %</th>
                  </tr>
                </thead>
                <tbody>
                  {holdings.map((holding, idx) => (
                    <tr key={idx}>
                      <td>{holding.symbol}</td>
                      <td>{holding.quantity}</td>
                      <td>₹{holding.avgPrice?.toFixed(2) || "0.00"}</td>
                      <td>₹{holding.ltp?.toFixed(2) || "0.00"}</td>
                      <td>₹{holding.investedValue?.toFixed(2) || "0.00"}</td>
                      <td>₹{holding.currentValue?.toFixed(2) || "0.00"}</td>
                      <td className={holding.pnl >= 0 ? "positive" : "negative"}>
                        ₹{holding.pnl?.toFixed(2) || "0.00"}
                      </td>
                      <td className={holding.pnlPercent >= 0 ? "positive" : "negative"}>
                        {holding.pnlPercent?.toFixed(2) || "0.00"}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}


