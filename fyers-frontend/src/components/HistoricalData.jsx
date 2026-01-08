import { useState, useEffect } from "react";
import { MdShowChart } from "react-icons/md";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { getOhlc } from "../api/fyersApi";
import { ALL_SYMBOLS } from "../constants/stocks";
import CandlestickChart from "./CandlestickChart";
import StockSearchInput from "./StockSearchInput";
import "./HistoricalData.css";

const RESOLUTIONS = [
  { value: "1", label: "1 Minute" },
  { value: "5", label: "5 Minutes" },
  { value: "15", label: "15 Minutes" },
  { value: "60", label: "1 Hour" },
  { value: "D", label: "1 Day" },
];

export default function HistoricalData() {
  const [symbol, setSymbol] = useState("NSE:RELIANCE-EQ");
  const [customSymbol, setCustomSymbol] = useState("");
  const [resolution, setResolution] = useState("5");
  const [fromDate, setFromDate] = useState(() => {
    const date = new Date();
    date.setDate(date.getDate() - 7);
    return date;
  });
  const [toDate, setToDate] = useState(new Date());
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [source, setSource] = useState(null);
  const [showAllRecords, setShowAllRecords] = useState(false);
  const [dataInfo, setDataInfo] = useState(null);

  const normalizeSymbol = (sym) => {
    if (!sym) return "";
    const trimmed = sym.trim().toUpperCase();
    if (trimmed.includes(":")) return trimmed;
    return `NSE:${trimmed}-EQ`;
  };

  const fetchHistoricalOHLC = async () => {
    const activeSymbol = customSymbol ? normalizeSymbol(customSymbol) : symbol;
    
    if (!activeSymbol) {
      setError("Please enter a symbol");
      return;
    }

    if (fromDate > toDate) {
      setError("From date cannot be after To date");
      return;
    }

    const today = new Date();
    today.setHours(23, 59, 59, 999);
    if (toDate > today) {
      setError("To date cannot be in the future");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const fromStr = fromDate.toISOString().split("T")[0];
      const toStr = toDate.toISOString().split("T")[0];
      
      const response = await getOhlc(activeSymbol, fromStr, toStr, resolution);
      
      if (response.data && Array.isArray(response.data)) {
        setData(response.data);
        setSource(response.source || "unknown");
        
        // Store info about market closed / date adjustments
        if (response.market_closed) {
          setDataInfo({
            marketClosed: true,
            closeReason: response.close_reason || null,
            requestedDate: response.requested_date || toStr,
            actualDate: response.actual_date || toStr
          });
        } else {
          setDataInfo(null);
        }
      } else {
        setData([]);
        setDataInfo(null);
        setError("No data returned from API");
      }
    } catch (err) {
      console.error("Fetch error:", err);
      setError(err.message || "Failed to fetch OHLC data");
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSymbolChange = (e) => {
    setSymbol(e.target.value);
    setCustomSymbol("");
  };

  const handleCustomSymbolChange = (e) => {
    setCustomSymbol(e.target.value);
    setSymbol("");
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    fetchHistoricalOHLC();
  };

  return (
    <div className="historical-data">
      <div className="historical-header">
        <h1>
          <MdShowChart size={32} />
          Historical Stock Data
        </h1>
        <p className="subtitle">View historical OHLC data for any date range</p>
      </div>

      <form onSubmit={handleSubmit} className="historical-controls">
        <div className="control-group">
          <label>Search Stock</label>
          <StockSearchInput
            value={symbol}
            onChange={(newSymbol) => {
              setSymbol(newSymbol);
              setCustomSymbol("");
            }}
            placeholder="Search by symbol or company name..."
            required
          />
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
          <label>From Date</label>
          <DatePicker
            selected={fromDate}
            onChange={(date) => setFromDate(date)}
            maxDate={toDate < new Date() ? toDate : new Date()}
            dateFormat="yyyy-MM-dd"
            className="date-input"
          />
        </div>

        <div className="control-group">
          <label>To Date</label>
          <DatePicker
            selected={toDate}
            onChange={(date) => setToDate(date)}
            minDate={fromDate}
            maxDate={new Date()}
            dateFormat="yyyy-MM-dd"
            className="date-input"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="fetch-button"
        >
          {loading ? "⏳ Loading..." : "🔍 Fetch Historical Data"}
        </button>
      </form>

      {error && (
        <div className="error-message">
          <strong>❌ Error:</strong> {error}
        </div>
      )}
      
      {/* Data Info Banner - shown when dates were adjusted */}
      {dataInfo && dataInfo.marketClosed && (
        <div className="data-info-banner">
          <div className="banner-icon">📊</div>
          <div className="banner-content">
            <strong>Date Adjusted</strong>
            <span className="banner-details">
              Requested: <strong>{dataInfo.requestedDate}</strong> ({dataInfo.closeReason}) - 
              Showing: <strong>{dataInfo.actualDate}</strong>
            </span>
          </div>
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
          <p>Fetching historical OHLC data...</p>
        </div>
      )}

      {data.length > 0 && (
        <>
          <div className="chart-container-fullwidth">
            <h2>Historical Candlestick Chart</h2>
            <CandlestickChart data={data} />
          </div>

          <div className="table-container-fullwidth">
            <h2>Historical OHLC Data</h2>
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
                  {(showAllRecords ? data : data.slice(0, 10)).map((row, idx) => {
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
              <div className="show-more-container">
                <button
                  className="show-more-button"
                  onClick={() => setShowAllRecords(!showAllRecords)}
                >
                  {showAllRecords ? "Show Less" : `Show More (${data.length - 10} more records)`}
                </button>
              </div>
            )}
            <div className="table-footer">
              <p>
                Showing {showAllRecords ? data.length : Math.min(10, data.length)} of {data.length} records | 
                Period: {fromDate.toISOString().split("T")[0]} to {toDate.toISOString().split("T")[0]}
              </p>
            </div>
          </div>
        </>
      )}

      {!loading && data.length === 0 && !error && (
        <div className="empty-state">
          <p>📊 Select a symbol, date range, and time interval, then click "Fetch Historical Data" to view data.</p>
        </div>
      )}
    </div>
  );
}

