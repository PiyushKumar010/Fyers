import { useState, useEffect, useRef } from "react";
import { getQuote, getLtp, getOhlc } from "../api/fyersApi";
import CandlestickChart from "./CandlestickChart";
import OrderPlacement from "./OrderPlacement";
import OrdersList from "./OrdersList";
import PositionsHoldings from "./PositionsHoldings";
import MarketStatus from "./MarketStatus";
import AuthButton from "./AuthButton";
import "./TradingDashboard.css";

const POPULAR_SYMBOLS = [
  { value: "NSE:RELIANCE-EQ", label: "RELIANCE" },
  { value: "NSE:TCS-EQ", label: "TCS" },
  { value: "NSE:SBIN-EQ", label: "SBIN" },
  { value: "NSE:INFY-EQ", label: "INFY" },
  { value: "NSE:HDFCBANK-EQ", label: "HDFC Bank" },
  { value: "NSE:ICICIBANK-EQ", label: "ICICI Bank" },
];

const RESOLUTIONS = [
  { value: "1", label: "1 Minute" },
  { value: "5", label: "5 Minutes" },
  { value: "15", label: "15 Minutes" },
  { value: "60", label: "1 Hour" },
];

export default function TradingDashboard() {
  const [symbol, setSymbol] = useState("NSE:RELIANCE-EQ");
  const [resolution, setResolution] = useState("5");
  const [quote, setQuote] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);

  const normalizeSymbol = (sym) => {
    if (!sym) return "";
    const trimmed = sym.trim().toUpperCase();
    if (trimmed.includes(":")) return trimmed;
    return `NSE:${trimmed}-EQ`;
  };

  const fetchQuote = async () => {
    try {
      const data = await getQuote(symbol);
      setQuote(data);
    } catch (err) {
      console.error("Failed to fetch quote:", err);
    }
  };

  const fetchChartData = async () => {
    try {
      const today = new Date().toISOString().split("T")[0];
      const response = await getOhlc(symbol, today, today, resolution);
      if (response.data && Array.isArray(response.data)) {
        setChartData(response.data);
      }
    } catch (err) {
      console.error("Failed to fetch chart data:", err);
    }
  };

  useEffect(() => {
    fetchQuote();
    fetchChartData();
    const interval = setInterval(() => {
      fetchQuote();
      fetchChartData();
    }, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, [symbol, resolution]);

  // WebSocket connection for live ticks
  useEffect(() => {
    const base = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
    const wsBase = base.replace(/^http/, "ws");
    const url = `${wsBase}/ws/market?symbols=${encodeURIComponent(symbol)}`;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.info("WebSocket connected");
        setWsConnected(true);
      };

      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          if (msg.type === "tick" && msg.data) {
            // Update quote with live data
            setQuote((prev) => ({
              ...prev,
              ltp: msg.data.ltp || prev?.ltp,
              volume: msg.data.volume || prev?.volume,
              change: msg.data.change || prev?.change,
              change_percent: msg.data.change_percent || prev?.change_percent,
            }));
          }
        } catch (e) {
          console.error("WS message parse error", e);
        }
      };

      ws.onerror = (e) => {
        console.error("WebSocket error", e);
        setWsConnected(false);
      };

      ws.onclose = () => {
        console.info("WebSocket closed");
        setWsConnected(false);
      };
    } catch (err) {
      console.error("Failed to open WebSocket", err);
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [symbol]);

  const handleOrderPlaced = () => {
    // Refresh orders list if needed
    console.log("Order placed successfully");
  };

  return (
    <div className="trading-dashboard">
      <div className="dashboard-header">
        <h1>
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
          </svg>
          Trading Dashboard
        </h1>
        <p className="subtitle">Real-time trading with Fyers API</p>
      </div>

      <AuthButton />
      <MarketStatus />

      <div className="dashboard-controls">
        <div className="control-group">
          <label>Symbol</label>
          <select
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            className="select-input"
          >
            {POPULAR_SYMBOLS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Timeframe</label>
          <select
            value={resolution}
            onChange={(e) => setResolution(e.target.value)}
            className="select-input"
          >
            {RESOLUTIONS.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Connection Status</label>
          <div className="connection-status">
            <svg className="status-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {wsConnected ? (
                <>
                  <path d="M5 12.55a11 11 0 0 1 14.08 0"></path>
                  <path d="M1.42 9a16 16 0 0 1 21.16 0"></path>
                  <path d="M8.53 16.11a6 6 0 0 1 6.95 0"></path>
                  <line x1="12" y1="20" x2="12.01" y2="20"></line>
                </>
              ) : (
                <>
                  <line x1="1" y1="1" x2="23" y2="23"></line>
                  <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55"></path>
                  <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39"></path>
                  <path d="M10.71 5.05A16 16 0 0 1 22.58 9"></path>
                  <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88"></path>
                  <path d="M8.53 16.11a6 6 0 0 1 6.95 0"></path>
                </>
              )}
            </svg>
            <span className={wsConnected ? "connected-text" : "disconnected-text"}>
              {wsConnected ? "Live" : "Disconnected"}
            </span>
          </div>
        </div>
      </div>

      {quote && (
        <div className="quote-card">
          <div className="quote-header">
            <h3>{symbol}</h3>
            <span className={`change ${quote.change >= 0 ? "positive" : "negative"}`}>
              {quote.change >= 0 ? "+" : ""}₹{quote.change?.toFixed(2)} ({quote.change_percent?.toFixed(2)}%)
            </span>
          </div>
          <div className="quote-details">
            <div className="quote-item">
              <span className="label">LTP</span>
              <span className="value">₹{quote.ltp?.toFixed(2) || "0.00"}</span>
            </div>
            <div className="quote-item">
              <span className="label">Open</span>
              <span className="value">₹{quote.open?.toFixed(2) || "0.00"}</span>
            </div>
            <div className="quote-item">
              <span className="label">High</span>
              <span className="value positive">₹{quote.high?.toFixed(2) || "0.00"}</span>
            </div>
            <div className="quote-item">
              <span className="label">Low</span>
              <span className="value negative">₹{quote.low?.toFixed(2) || "0.00"}</span>
            </div>
            <div className="quote-item">
              <span className="label">Volume</span>
              <span className="value">{quote.volume?.toLocaleString() || "0"}</span>
            </div>
          </div>
        </div>
      )}

      <div className="dashboard-grid">
        <div className="grid-item chart-section">
          <h2>Chart - {symbol}</h2>
          <CandlestickChart data={chartData} />
        </div>

        <div className="grid-item order-section">
          <OrderPlacement symbol={symbol} onOrderPlaced={handleOrderPlaced} />
        </div>
      </div>

      <OrdersList />
      <PositionsHoldings />
    </div>
  );
}

