import { useState, useEffect, useRef } from "react";
import { MdTrendingUp, MdShowChart, MdArrowUpward, MdArrowDownward, MdCancel, MdCheckCircle } from "react-icons/md";
import { getOhlc, getLoginUrl, getAuthStatus, getMarketStatus, getQuotes } from "../api/fyersApi";
import CandlestickChart from "./CandlestickChart";
import MarketStatus from "./MarketStatus";
import TrendSignal from "./TrendSignal";
import MiniChart from "./MiniChart";
import { POPULAR_SYMBOLS, ALL_SYMBOLS, normalizeSymbol } from "../constants/stocks";
import "./OhlcDashboard.css";

const RESOLUTIONS = [
  { value: "1", label: "1 Minute" },
  { value: "5", label: "5 Minutes" },
  { value: "15", label: "15 Minutes" },
  { value: "60", label: "1 Hour" },
];

export default function OhlcDashboard() {
  const [symbol, setSymbol] = useState("NSE:RELIANCE-EQ");
  const [customSymbol, setCustomSymbol] = useState("");
  const [resolution, setResolution] = useState("5");
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [authRequired, setAuthRequired] = useState(false);
  const [authMessage, setAuthMessage] = useState(null);
  const authPollRef = useRef(null);
  const [source, setSource] = useState(null);
  const [live, setLive] = useState(true);
  const intervalRef = useRef(null);
  const wsRef = useRef(null);
  const [showAll, setShowAll] = useState(false);
  const [topStocksData, setTopStocksData] = useState([]);
  const [marketStatus, setMarketStatus] = useState(null);
  const [dataInfo, setDataInfo] = useState(null); // Store market_closed info from API
  const [indicesData, setIndicesData] = useState([]);

  const getTodayDate = () => {
    const today = new Date();
    return today.toISOString().split("T")[0];
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    if (Number.isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
  };

  const fetchTodayOHLC = async () => {
    const activeSymbol = customSymbol ? normalizeSymbol(customSymbol) : symbol;
    
    if (!activeSymbol) {
      setError("Please enter a symbol");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const today = getTodayDate();
      const response = await getOhlc(activeSymbol, today, today, resolution);
      
      if (response.data && Array.isArray(response.data)) {
        setData(response.data);
        setSource(response.source || "unknown");
        
        // Store info about market closed / date adjustments
        setDataInfo({
          marketClosed: response.market_closed || false,
          closeReason: response.close_reason || null,
          requestedDate: response.requested_date || today,
          actualDate: response.actual_date || today
        });
      } else {
        setData([]);
        setDataInfo(null);
        if (response.data && response.data.length === 0) {
          setError(null);
        } else {
          setError("No data returned from API");
        }
      }
    } catch (err) {
      console.error("Fetch error:", err);
      const msg = err.message || "Failed to fetch OHLC data";
      if (typeof msg === "string" && msg.startsWith("AUTH_REQUIRED")) {
        setAuthRequired(true);
        setAuthMessage(msg.replace(/^AUTH_REQUIRED:\s*/i, ""));
        setError("Authentication required to fetch live data. Please login.");
      } else {
        setError(msg);
      }
      setData([]);
      setDataInfo(null);
    } finally {
      setLoading(false);
    }
  };

  const fetchIndices = async () => {
    try {
      const indices = ['NSE:NIFTY50-INDEX', 'NSE:NIFTYBANK-INDEX', 'BSE:SENSEX-INDEX'];
      const response = await getQuotes(indices);
      
      if (response?.quotes) {
        const indexNames = ['Nifty 50', 'Nifty Bank', 'Sensex'];
        const enrichedIndices = response.quotes.map((quote, idx) => ({
          ...quote,
          displayName: indexNames[idx]
        }));
        setIndicesData(enrichedIndices);
      }
    } catch (err) {
      console.error('Failed to fetch indices:', err);
    }
  };

  const fetchTopStocks = async () => {
    try {
      const today = getTodayDate();
      const promises = POPULAR_SYMBOLS.map(async (stock) => {
        try {
          const response = await getOhlc(stock.value, today, today, "5");
          if (response.data && Array.isArray(response.data) && response.data.length > 0) {
            const latest = response.data[response.data.length - 1];
            const first = response.data[0];
            const change = latest.close - first.open;
            const changePercent = ((change / first.open) * 100).toFixed(2);
            return {
              ...stock,
              price: latest.close,
              open: first.open,
              high: Math.max(...response.data.map(d => d.high)),
              low: Math.min(...response.data.map(d => d.low)),
              volume: response.data.reduce((sum, d) => sum + (d.volume || 0), 0),
              change,
              changePercent,
              data: response.data
            };
          }
          return null;
        } catch (err) {
          return null;
        }
      });
      const results = await Promise.all(promises);
      setTopStocksData(results.filter(Boolean));
    } catch (err) {
      console.error("Failed to fetch top stocks:", err);
    }
  };

  useEffect(() => {
    // Check auth status on mount
    let mounted = true;
    (async () => {
      try {
        const st = await getAuthStatus();
        if (!mounted) return;
        if (st && st.authenticated) {
          setAuthRequired(false);
          setAuthMessage(null);
        } else {
          setAuthRequired(false);
        }
      } catch (e) {
        // ignore
      }
      
      // Fetch market status
      try {
        const mStatus = await getMarketStatus();
        if (mounted) {
          setMarketStatus(mStatus);
          // Disable live updates if market is closed
          if (!mStatus.is_open) {
            setLive(false);
          }
        }
      } catch (e) {
        console.error("Failed to fetch market status:", e);
      }
    })();

    fetchTodayOHLC();
    fetchIndices();
    fetchTopStocks();
    
    return () => { mounted = false; };
  }, [symbol, customSymbol, resolution]);

  // Cleanup auth polling on unmount
  useEffect(() => {
    return () => {
      if (authPollRef.current) {
        clearInterval(authPollRef.current);
        authPollRef.current = null;
      }
    };
  }, []);

  // Auto-refresh for today's data
  useEffect(() => {
    if (live) {
      intervalRef.current = setInterval(() => {
        fetchTodayOHLC();
        fetchIndices();
        fetchTopStocks();
      }, 30000); // 30 seconds
    } else {
      clearInterval(intervalRef.current);
    }

    return () => clearInterval(intervalRef.current);
  }, [live, symbol, customSymbol, resolution]);

  // Live WebSocket for real-time updates
  useEffect(() => {
    if (!live) {
      if (wsRef.current) {
        try { wsRef.current.close(); } catch (e) {}
        wsRef.current = null;
      }
      return;
    }

    const activeSymbol = customSymbol ? normalizeSymbol(customSymbol) : symbol;
    // don't open live websocket if we have no initial data (avoid repeated "no_data" messages)
    if (!activeSymbol || (Array.isArray(data) && data.length === 0)) {
      setLive(false);
      return;
    }

    const base = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
    const wsBase = base.replace(/^http/, "ws");
    const url = `${wsBase}/ohlc/ws?symbol=${encodeURIComponent(activeSymbol)}&resolution=${encodeURIComponent(resolution)}&interval=5`;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.info("Live websocket opened", url);
      };

      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          if (msg.error) {
            console.warn("WS error:", msg.error);
            return;
          }

          if (msg.candle) {
            setData((prev) => {
              if (!Array.isArray(prev) || prev.length === 0) return [msg.candle];
              const last = prev[prev.length - 1];
              if (last.time === msg.candle.time) {
                // replace last
                return [...prev.slice(0, -1), msg.candle];
              }
              return [...prev, msg.candle];
            });
          }
        } catch (e) {
          console.error("WS message parse error", e);
        }
      };

      ws.onerror = (e) => console.error("WebSocket error", e);

      ws.onclose = () => {
        console.info("Live websocket closed");
        wsRef.current = null;
      };
    } catch (err) {
      console.error("Failed to open websocket", err);
      setError("Failed to start live updates");
    }

    return () => {
      if (wsRef.current) {
        try { wsRef.current.close(); } catch (e) {}
        wsRef.current = null;
      }
    };
  }, [live, symbol, customSymbol, resolution]);

  const handleSymbolChange = (e) => {
    setSymbol(e.target.value);
    setCustomSymbol("");
  };

  const handleCustomSymbolChange = (e) => {
    setCustomSymbol(e.target.value);
    setSymbol("");
  };

  return (
    <div className="ohlc-dashboard">
      <div className="dashboard-header">
        <h1>
          <MdTrendingUp className="header-icon" />
          Live Stock Dashboard
        </h1>
        <p className="subtitle">Real-time market data and insights</p>
      </div>

      {/* Unified Market Status Banner */}
      {marketStatus && !marketStatus.is_open && (
        <div className="market-status-banner">
          <div className="banner-icon">
            <MdCancel size={28} />
          </div>
          <div className="banner-content">
            <strong>Market is Closed</strong>
            <span className="banner-details">
              {marketStatus.reason || "Closed"}
              {marketStatus.current_day ? ` • ${marketStatus.current_day}` : ""}
            </span>
            <span className="banner-details">
              Last trading day: <strong>{formatDate(marketStatus.last_trading_day || dataInfo?.actualDate || dataInfo?.requestedDate || getTodayDate())}</strong>
              { (dataInfo?.actualDate || dataInfo?.requestedDate) && (
                <> • Showing data from: <strong>{formatDate(dataInfo.actualDate || dataInfo.requestedDate)}</strong></>
              )}
            </span>
          </div>
        </div>
      )}
      
      {marketStatus && marketStatus.is_open && (
        <div className="market-status-banner market-open">
          <div className="banner-icon">
            <MdCheckCircle size={28} />
          </div>
          <div className="banner-content">
            <strong>Market is Open</strong>
            <span className="banner-details">
              Live trading in progress - {marketStatus.current_time}
            </span>
          </div>
        </div>
      )}

      {/* Top Stocks Section */}
      <div className="top-stocks-section">
        <h2 className="section-title">
          <MdShowChart />
          Market Overview
        </h2>

        {/* Indices Cards */}
        {indicesData.length > 0 && (
          <div className="indices-section">
            {indicesData.map((index, idx) => (
              <div key={idx} className="index-card">
                <div className="index-info">
                  <div className="index-name">{index.displayName}</div>
                  <div className="index-price">₹{index.ltp?.toFixed(2)}</div>
                  <div className={`index-change ${index.change_percent >= 0 ? 'positive' : 'negative'}`}>
                    {index.change_percent >= 0 ? '↑' : '↓'} {Math.abs(index.change_percent).toFixed(2)}%
                    <span className="change-value">({index.change >= 0 ? '+' : ''}{index.change?.toFixed(2)})</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="stocks-table">
          <div className="stocks-table-header">
            <div className="col-company">Company</div>
            <div className="col-chart">Chart</div>
            <div className="col-price">Market Price</div>
            <div className="col-change">Price Change</div>
            <div className="col-volume">Volume</div>
            <div className="col-high">High</div>
            <div className="col-low">Low</div>
          </div>
          <div className="stocks-table-body">
            {topStocksData.length > 0 ? (
              topStocksData.map((stock) => (
                <div 
                  key={stock.value} 
                  className="stock-row"
                  onClick={() => {
                    setSymbol(stock.value);
                    setCustomSymbol("");
                  }}
                >
                  <div className="col-company">
                    <div className="company-info">
                      <span className="company-symbol">{stock.label}</span>
                      <span className="company-name">{stock.name}</span>
                    </div>
                  </div>
                  <div className="col-chart">
                    <MiniChart data={stock.data} />
                  </div>
                  <div className="col-price">
                    <span className="price-value">₹{stock.price?.toFixed(2)}</span>
                  </div>
                  <div className="col-change">
                    <span className={`change-badge ${stock.change >= 0 ? 'positive' : 'negative'}`}>
                      {stock.change >= 0 ? <MdArrowUpward /> : <MdArrowDownward />}
                      {stock.change >= 0 ? '+' : ''}{stock.changePercent}%
                    </span>
                  </div>
                  <div className="col-volume">
                    <span className="volume-value">{(stock.volume / 10000000).toFixed(2)}Cr</span>
                  </div>
                  <div className="col-high">
                    <span className="high-value">₹{stock.high?.toFixed(2)}</span>
                  </div>
                  <div className="col-low">
                    <span className="low-value">₹{stock.low?.toFixed(2)}</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="loading-stocks">
                <div className="spinner-small"></div>
                <p>Loading market data...</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Chart Controls */}
      <div className="chart-section-header">
        <h2 className="section-title">
          <MdTrendingUp />
          Detailed Chart Analysis
        </h2>
      </div>

      <div className="dashboard-controls">
        <div className="control-group">
          <label>Symbol</label>
          <div className="symbol-input-group">
            <select
              value={symbol}
              onChange={handleSymbolChange}
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
              onChange={handleCustomSymbolChange}
              placeholder="Enter symbol (e.g., RELIANCE)"
              className="text-input"
              disabled={!!symbol}
            />
          </div>
        </div>

        <div className="control-group">
          <label>Time Interval</label>
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
          <label>Options</label>
          <div className="checkbox-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={live}
                onChange={(e) => setLive(e.target.checked)}
                disabled={marketStatus && !marketStatus.is_open}
              />
              <span>Live Updates {marketStatus && !marketStatus.is_open && "(Market Closed)"}</span>
            </label>
          </div>
        </div>

        <button
          onClick={fetchTodayOHLC}
          disabled={loading}
          className="fetch-button"
        >
          {loading ? "⏳ Loading..." : "🔄 Refresh"}
        </button>
        {authRequired && (
          <button
            onClick={async () => {
              try {
                const res = await getLoginUrl();
                const url = (res && res.login_url) ? res.login_url : (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000") + "/auth/login";
                const win = window.open(url, "_blank");

                // start polling for auth status while the login window is open
                if (authPollRef.current) {
                  clearInterval(authPollRef.current);
                }
                authPollRef.current = setInterval(async () => {
                  try {
                    const st = await getAuthStatus();
                    if (st && st.authenticated) {
                      clearInterval(authPollRef.current);
                      authPollRef.current = null;
                      setAuthRequired(false);
                      setAuthMessage(null);
                      // refresh data after successful login
                      fetchTodayOHLC();
                      if (win) win.close();
                    }
                  } catch (e) {
                    // ignore transient errors
                  }
                }, 2000);
              } catch (e) {
                console.error("Failed to get login URL", e);
                const fallback = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000") + "/auth/login";
                window.open(fallback, "_blank");
              }
            }}
            className="login-button"
          >
            🔐 Login to Fyers
          </button>
        )}
      </div>

      {error && (
        <div className="error-message">
          <strong>❌ Error:</strong> {error}
        </div>
      )}

      {source && (
        <div className="data-source">
          <span className={`source-badge ${source}`}>
            📊 Data from: {source === "mongodb" ? "Cache" : "Fyers API"}
          </span>
        </div>
      )}

      {loading && (
        <div className="loading-overlay">
          <div className="spinner"></div>
          <p>Fetching today's OHLC data...</p>
        </div>
      )}

      {data.length > 0 && (
        <>
          <div className="chart-container-fullwidth">
            <h2>Today's Candlestick Chart</h2>
            <CandlestickChart data={data} />
            <TrendSignal 
              symbol={customSymbol ? (customSymbol.trim().includes(":") ? customSymbol.trim() : `NSE:${customSymbol.trim().toUpperCase()}-EQ`) : symbol} 
              interval={resolution} 
              duration={1} 
              ohlcData={data}
            />
          </div>

          <div className="table-container">
            <h2>Today's OHLC Data</h2>
            <div className="table-wrapper">
              <table className="ohlc-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Open</th>
                    <th>High</th>
                    <th>Low</th>
                    <th>Close</th>
                    <th>Volume</th>
                    <th>Change</th>
                    <th>Change %</th>
                  </tr>
                </thead>
                <tbody>
                  {(showAll ? data : data.slice(0, 10)).map((row, idx) => {
                    const change = idx > 0 ? row.close - data[idx - 1].close : 0;
                    const changePercent = idx > 0 && data[idx - 1].close !== 0
                      ? ((change / data[idx - 1].close) * 100).toFixed(2)
                      : "0.00";
                    return (
                      <tr key={idx}>
                        <td>{row.time}</td>
                        <td>₹{row.open?.toFixed(2) || "N/A"}</td>
                        <td className="price-high">₹{row.high?.toFixed(2) || "N/A"}</td>
                        <td className="price-low">₹{row.low?.toFixed(2) || "N/A"}</td>
                        <td className="price-close">₹{row.close?.toFixed(2) || "N/A"}</td>
                        <td>{row.volume?.toLocaleString() || "N/A"}</td>
                        <td className={change >= 0 ? "positive" : "negative"}>
                          {change >= 0 ? "+" : ""}₹{change.toFixed(2)}
                        </td>
                        <td className={change >= 0 ? "positive" : "negative"}>
                          {change >= 0 ? "+" : ""}{changePercent}%
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {data.length > 10 && (
              <div className="load-more-container">
                <button 
                  className="load-more-btn"
                  onClick={() => setShowAll(!showAll)}
                >
                  {showAll ? "Show Less" : "Load More"}
                </button>
              </div>
            )}
            <div className="table-footer">
              <p>Total records: {data.length} | Date: {getTodayDate()}</p>
            </div>
          </div>
        </>
      )}

      {!loading && data.length === 0 && !error && (
        <div className="empty-state">
          <p>📊 No data available for today. Market may be closed or no trades occurred.</p>
        </div>
      )}
    </div>
  );
}
