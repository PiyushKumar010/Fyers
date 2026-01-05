import { useState, useEffect } from "react";
import "./MarketStatus.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function MarketStatus() {
  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkMarketStatus();
    const interval = setInterval(checkMarketStatus, 60000); // Check every minute
    return () => clearInterval(interval);
  }, []);

  const checkMarketStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/market/status`);
      if (!response.ok) {
        throw new Error("Failed to fetch market status");
      }
      const data = await response.json();
      console.log("Market status from API:", data);
      setMarketData(data);
    } catch (error) {
      console.error("Failed to check market status:", error);
      // Fallback to time-based logic if API fails
      const fallbackStatus = checkTimeBasedStatus();
      console.log("Using fallback status:", fallbackStatus);
      setMarketData({
        is_open: fallbackStatus,
        reason: "Unable to fetch from server"
      });
    } finally {
      setLoading(false);
    }
  };

  const checkTimeBasedStatus = () => {
    const now = new Date();
    const day = now.getDay(); // 0 = Sunday, 6 = Saturday
    const hour = now.getHours();
    const minute = now.getMinutes();

    // Market is closed on weekends
    if (day === 0 || day === 6) {
      return false;
    }

    // NSE market hours: 9:15 AM to 3:30 PM IST
    // Convert to UTC if needed (IST is UTC+5:30)
    const istHour = hour;
    const istMinute = minute;

    // Market opens at 9:15 and closes at 15:30
    if (istHour < 9 || (istHour === 9 && istMinute < 15)) {
      return false; // Before market open
    }
    if (istHour > 15 || (istHour === 15 && istMinute > 30)) {
      return false; // After market close
    }

    return true; // Market is open
  };

  if (loading) {
    return (
      <div className="market-status loading">
        <span>Checking market status...</span>
      </div>
    );
  }

  return (
    <div className={`market-status ${marketData?.is_open ? "open" : "closed"}`}>
      <div className="status-indicator">
        <span className="status-dot"></span>
        <span className="status-text">
          Market is {marketData?.is_open ? "Open" : "Closed"}
        </span>
      </div>
      {!marketData?.is_open && (
        <div className="status-details">
          <p className="status-message">{marketData?.reason || "Closed"}</p>
          {marketData?.last_trading_day && (
            <p className="status-info">
              Last trading day: {new Date(marketData.last_trading_day).toLocaleDateString('en-GB', { 
                day: '2-digit', 
                month: 'short', 
                year: 'numeric' 
              })}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

